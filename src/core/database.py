"""
Configuración y gestión de conexiones a la base de datos.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.config import get_settings
from src.models.base_model import BaseModel


class DatabaseManager:
    """
    Gestor de conexiones a la base de datos.

    Implementa el patrón singleton para garantizar que solo exista
    una única conexión a la base de datos en toda la aplicación.
    Gestiona la creación y configuración del motor de SQLAlchemy
    y la factoría de sesiones.

    Attributes
    ----------
    _instance : Optional[DatabaseManager]
        Instancia única de la clase (patrón singleton)
    _engine : AsyncEngine
        Motor de SQLAlchemy para conexiones asíncronas
    _session_factory : async_sessionmaker
        Factoría para crear sesiones de base de datos

    Notes
    -----
    Esta clase sigue las mejores prácticas de SQLAlchemy 2.0 para
    aplicaciones asíncronas, incluyendo la gestión adecuada de
    conexiones y el manejo de sesiones.
    """

    _instance: Optional["DatabaseManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized") or not self._initialized:
            settings = get_settings()

            # Check if we're using SQLite (which doesn't support regular connection pooling)
            is_sqlite = settings.database_url.startswith("sqlite")

            # Create async engine with appropriate parameters based on DB type
            if is_sqlite:
                # SQLite doesn't support the same pooling as server databases
                self._engine = create_async_engine(
                    settings.database_url,
                    echo=settings.debug,  # Log SQL queries in debug mode
                    future=True,  # Enable SQLAlchemy 2.0 features
                )
            else:
                # For MySQL, PostgreSQL, etc. with full pooling support
                self._engine = create_async_engine(
                    settings.database_url,
                    echo=settings.debug,  # Log SQL queries in debug mode
                    pool_pre_ping=True,  # Enable pessimistic disconnect handling
                    pool_size=10,  # Connection pool size
                    max_overflow=20,  # Max overflow connections
                    future=True,  # Enable SQLAlchemy 2.0 features
                )

            # Create async session factory
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            self._initialized = True

    @property
    def engine(self):
        """
        Obtiene la instancia del motor SQLAlchemy.

        Proporciona acceso al motor de base de datos configurado
        para realizar operaciones de bajo nivel cuando sea necesario.

        Returns
        -------
        AsyncEngine
            Motor de SQLAlchemy configurado para esta instancia
        """
        return self._engine

    @property
    def session_factory(self):
        """
        Obtiene la factoría de sesiones SQLAlchemy.

        Permite crear sesiones adicionales de base de datos cuando
        se necesitan múltiples sesiones independientes.

        Returns
        -------
        async_sessionmaker
            Factoría para crear nuevas sesiones de base de datos
        """
        return self._session_factory

    async def close(self):
        """
        Cierra la conexión a la base de datos.

        Esta función libera todos los recursos asociados con
        la conexión a la base de datos de manera segura.
        Debe llamarse cuando la instancia ya no sea necesaria.

        Notes
        -----
        Este método es llamado internamente por la función
        close_database() durante el ciclo de vida de la aplicación.
        """
        if hasattr(self, "_engine") and self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self):
        """
        Proporciona un gestor de contexto para sesiones de base de datos.

        Crea y gestiona una sesión de base de datos de manera segura,
        manejando automáticamente el commit, rollback y cierre de sesión.

        Yields
        ------
        AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la BD

        Examples
        --------
        ```python
        async with DatabaseManager().session() as session:
            result = await session.execute(select(Model))
            # Usar session aquí
        ```
        """
        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Create a singleton instance
db = DatabaseManager()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Obtiene una sesión de base de datos para inyección de dependencias en FastAPI.

    Esta función es utilizada como dependencia en los controladores FastAPI
    para inyectar una sesión de base de datos activa. Gestiona automáticamente
    el ciclo de vida de la sesión, asegurando que se cierre correctamente.

    Yields
    ------
    AsyncSession
        Sesión de base de datos asíncrona de SQLAlchemy

    Examples
    --------
    ```python
    @router.get("/items")
    async def get_items(session: AsyncSession = Depends(get_database_session)):
        result = await session.execute(select(ItemModel))
        items = result.scalars().all()
        return items
    ```
    """
    async with db.session() as session:
        yield session


async def create_tables():
    """
    Crea todas las tablas definidas en el modelo de datos.

    Esta función debe ejecutarse durante el inicio de la aplicación
    para asegurar que todas las tablas necesarias existan en la base
    de datos antes de realizar operaciones.

    Notes
    -----
    Importa todos los modelos necesarios para asegurar que estén
    registrados con la clase base antes de crear las tablas.
    """
    # Import all models to ensure they are registered with the Base
    # Auth models
    from src.models.auth.rol_model import RolModel  # noqa: F401
    from src.models.auth.usuario_model import UsuarioModel  # noqa: F401
    from src.models.auth.sesion_model import SesionModel  # noqa: F401

    # Menu models
    from src.models.menu.categoria_model import CategoriaModel  # noqa: F401
    from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401
    from src.models.menu.producto_model import ProductoModel  # noqa: F401
    from src.models.menu.producto_alergeno_model import ProductoAlergenoModel  # noqa: F401

    # Mesas models
    from src.models.mesas.local_model import LocalModel  # noqa: F401
    from src.models.mesas.zona_model import ZonaModel  # noqa: F401
    from src.models.mesas.mesa_model import MesaModel  # noqa: F401
    from src.models.mesas.sesion_mesa_model import SesionMesaModel  # noqa: F401
    from src.models.mesas.locales_categorias_model import LocalesCategoriasModel  # noqa: F401
    from src.models.mesas.locales_productos_model import LocalesProductosModel  # noqa: F401
    from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel  # noqa: F401
    from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel  # noqa: F401

    # Pedidos models
    from src.models.pedidos.tipo_opciones_model import TipoOpcionModel  # noqa: F401
    from src.models.pedidos.producto_opcion_model import ProductoOpcionModel  # noqa: F401
    from src.models.pedidos.pedido_model import PedidoModel  # noqa: F401
    from src.models.pedidos.pedido_producto_model import PedidoProductoModel  # noqa: F401
    from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel  # noqa: F401

    # Pagos models
    from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
    from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401

    from src.models.auth.admin_model import AdminModel

    async with db.engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def drop_tables():
    """
    Elimina todas las tablas de la base de datos.

    Esta función es útil principalmente en entornos de prueba
    para garantizar un estado limpio de la base de datos antes
    de ejecutar pruebas que requieran un entorno controlado.

    Notes
    -----
    Debe utilizarse con precaución, ya que eliminará todos los datos
    existentes en las tablas. No se recomienda su uso en entornos
    de producción a menos que sea absolutamente necesario.
    ```
    """
    # Import all models to ensure they are registered with the Base
    from src.models.auth.rol_model import RolModel  # noqa: F401

    async with db.engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


async def close_database():
    """
    Cierra la conexión a la base de datos.

    Esta función debe llamarse al finalizar la aplicación
    para liberar recursos y cerrar conexiones de manera segura.
    Ayuda a prevenir fugas de memoria y conexiones huérfanas.

    Notes
    -----
    Se recomienda incluir esta función en el manejador de eventos
    de cierre de la aplicación FastAPI (lifespan).
    """
    await db.close()
