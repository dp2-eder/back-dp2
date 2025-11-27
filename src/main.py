"""
Punto de entrada principal de la aplicación FastAPI.
"""

import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.database import create_tables, close_database
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.core.dependencies import ErrorHandlerMiddleware

# ======================= SOLUCION AL ERROR DE MAPPER =======================
# Importar TODOS los modelos aqui para registrarlos en SQLAlchemy
# ANTES de que cualquier controlador sea importado.
# Esto resuelve el error: failed to locate a name DivisionCuentaModel

# Auth models
# from src.models.auth.rol_model import RolModel  # noqa: F401  # ELIMINADO: Ya no se usa RolModel
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

# Pedidos models - CRITICO: importar ANTES de pagos
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel  # noqa: F401
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel  # noqa: F401
from src.models.pedidos.pedido_model import PedidoModel  # noqa: F401
from src.models.pedidos.pedido_producto_model import PedidoProductoModel  # noqa: F401
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel  # noqa: F401

# Pagos models - DESPUES de pedidos (por la relacion bidireccional)
from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401
# ===========================================================================


# Configurar logger para este módulo
logger = logging.getLogger(__name__)


async def auto_seed_database():
    """
    Ejecuta el seed de la base de datos automáticamente si está vacía.
    
    Verifica si existen categorías en la base de datos. Si no hay ninguna,
    ejecuta el script de seed para poblar la BD con datos iniciales.
    """
    try:
        import os
        from sqlalchemy import select, func
        from src.core.database import DatabaseManager
        from src.models.menu.categoria_model import CategoriaModel
        
        logger.info("🔍 Verificando estado de la base de datos...")
        
        # Obtener sesión de base de datos
        db_manager = DatabaseManager()
        async with db_manager.session() as session:
            # Contar categorías existentes
            query = select(func.count(CategoriaModel.id))
            result = await session.execute(query)
            count = result.scalar()
            
            logger.info(f"Categorías encontradas: {count}")
            logger.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'No configurada')}")
            
            if count == 0:
                logger.info("🌱 Base de datos vacía detectada. Ejecutando seed automático...")
                
                # Importar y ejecutar el seeder
                from scripts.seed_cevicheria_data import CevicheriaSeeder
                
                # Crear instancia del seeder CON la sesión
                seeder = CevicheriaSeeder(session)
                await seeder.seed_all()
                
                # Commit de los cambios
                await session.commit()
                
                logger.info("✅ Seed completado exitosamente!")
            else:
                logger.info(f"✅ Base de datos ya contiene datos ({count} categorías). Skip seed.")
            
    except Exception as e:
        import traceback
        logger.error(f"❌ Error al ejecutar auto-seed: {e}")
        logger.error(f"Stack trace completo:\n{traceback.format_exc()}")
        logger.warning("⚠️ La aplicación continuará sin datos de seed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación FastAPI.

    Controla los eventos de inicio y apagado de la aplicación,
    configurando recursos necesarios al inicio y liberándolos al finalizar.

    Parameters
    ----------
    app : FastAPI
        La instancia de la aplicación FastAPI

    Notes
    -----
    Este gestor se ejecuta en estas fases:
    1. Código de inicialización (antes de yield)
    2. Aplicación en funcionamiento (durante yield)
    3. Código de limpieza (después de yield)
    """
    # Fase de inicialización
    logger.info("Iniciando Restaurant Backend API...")

    # Configurar sistema de logging
    configure_logging()

    # Crear tablas en la base de datos si no existen
    # import os
    # if os.getenv("INIT_DB", "false").lower() == "true":
    #     logger.info("INIT_DB=true: Creando tablas en la base de datos...")
    await create_tables()
    # Pequeña espera para asegurar que las tablas estén completamente creadas
    import asyncio
    await asyncio.sleep(0.5)
    # else:
    #     logger.info("INIT_DB no está activado, omitiendo creación de tablas")

    # Ejecutar seed automáticamente si la BD está vacía
    # await auto_seed_database()

    logger.info("Restaurant Backend API iniciada correctamente")

    yield  # La aplicación está en funcionamiento

    # Fase de limpieza
    logger.info("Cerrando Restaurant Backend API...")

    # Cerrar conexiones de base de datos
    await close_database()

    logger.info("Recursos liberados correctamente")


def register_routers(app: FastAPI) -> None:
    """
    Registra todos los routers de la aplicación.

    Carga dinámicamente los controladores disponibles y los registra
    con la aplicación FastAPI.

    Parameters
    ----------
    app : FastAPI
        La instancia de la aplicación FastAPI donde registrar los routers
    """
    # Estructura de controladores a cargar: (módulo, tag)
    controllers = [
        ("src.api.controllers.login_controller", "Login"),  # Nuevo controlador de login simplificado
        ("src.api.controllers.admin_sesiones_controller", "Admin - Sesiones"),  # Controlador admin de sesiones
        ("src.api.controllers.auth_controller", "Autenticación"),
        ("src.api.controllers.rol_controller", "Roles"),
        ("src.api.controllers.local_controller", "Locales"),
        ("src.api.controllers.zona_controller", "Zonas"),
        ("src.api.controllers.sesion_controller", "Sesiones"),
        ("src.api.controllers.sesion_mesa_controller", "Sesiones de Mesa"),
        ("src.api.controllers.categoria_controller", "Categorías"),
        ("src.api.controllers.alergeno_controller", "Alérgenos"),
        ("src.api.controllers.producto_controller", "Productos"),
        ("src.api.controllers.tipo_opciones_controller", "Tipos de Opciones"),
        ("src.api.controllers.producto_opcion_controller", "Producto Opciones"),
        ("src.api.controllers.producto_opciones_manage_controller", "Gestión de Opciones de Productos"),
        ("src.api.controllers.sync_controller", "Sincronización"),
        ("src.api.controllers.mesa_controller", "Mesas"),
        ("src.api.controllers.pedido_controller", "Pedidos"),
        ("src.api.controllers.pedido_producto_controller", "Pedidos Productos"),
        ("src.api.controllers.pedido_opcion_controller", "Pedido Opciones"),
        # ("src.api.controllers.division_cuenta_controller", "Divisiones de Cuenta"),
        # ("src.api.controllers.division_cuenta_detalle_controller", "Detalles de División"),
        # ("src.api.controllers.pagos_controller", "Pagos"),

        # Controladores de catálogo multi-local
        ("src.api.controllers.locales_categorias_controller", "Local - Categorías"),
        ("src.api.controllers.locales_productos_controller", "Local - Productos"),
        ("src.api.controllers.locales_tipos_opciones_controller", "Local - Tipos de Opciones"),
        ("src.api.controllers.locales_productos_opciones_controller", "Local - Opciones de Productos"),
    ]

    # Prefijo API común para todas las rutas
    api_prefix = "/v1"

    for module_name, tag in controllers:
        try:
            # Importar dinámicamente el módulo del controlador
            module = importlib.import_module(module_name)
            router = getattr(module, "router", None)

            if router and isinstance(router, APIRouter):
                # Registrar el router con la aplicación
                # No pasamos tags aquí porque los routers ya tienen sus tags definidos
                app.include_router(router, prefix=api_prefix)
                logger.info(f"Router '{tag}' registrado correctamente")
            else:
                logger.warning(f"No se encontró un router válido en {module_name}")
        except Exception as e:
            import traceback
            logger.error(f"Error al cargar el controlador {module_name}: {e}")
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")


def create_app() -> FastAPI:
    """
    Crea y configura la aplicación FastAPI.

    Configura todos los aspectos de la aplicación FastAPI, incluyendo
    middlewares, gestión de excepciones y registro de rutas.

    Returns
    -------
    FastAPI
        Instancia configurada de la aplicación FastAPI
    """
    settings = get_settings()

    # Crear la instancia de FastAPI
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        root_path="/api",
    )

    # Montar archivos estáticos para imágenes
    from pathlib import Path
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Agregar middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    # Agregar middleware para manejo de errores
    app.add_middleware(ErrorHandlerMiddleware)

    # Registrar todos los routers disponibles
    register_routers(app)

    # Registrar endpoints básicos
    @app.get("/")
    async def root():
        """
        Endpoint raíz de la API.

        Proporciona información básica sobre la API y enlaces a la documentación.

        Returns
        -------
        dict
            Información básica sobre la API
        """
        return {
            "message": "Restaurant Backend API",
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health")
    async def health_check():
        """
        Endpoint de verificación de salud del sistema.

        Permite monitorizar el estado de la API para herramientas
        de supervisión y balanceadores de carga.

        Returns
        -------
        dict
            Estado actual del servicio
        """
        return {
            "status": "healthy",
            "service": "restaurant-backend",
            "version": settings.app_version,
            "environment": settings.environment,
        }

    return app


# Crear la instancia de la aplicación
app = create_app()

# Punto de entrada para ejecución directa del script
if __name__ == "__main__":
    import uvicorn

    # Obtener configuración
    settings = get_settings()

    # Iniciar servidor uvicorn
    logger.info(f"Iniciando servidor en {settings.host}:{settings.port}")
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

