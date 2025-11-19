"""
Global fixtures for all tests.
"""

import pytest
import asyncio
import httpx
from ulid import ULID
from decimal import Decimal
from datetime import datetime
from faker import Faker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.core.database import get_database_session as get_db, DatabaseManager
from src.models.base_model import BaseModel as Base

# Importar TODOS los modelos al inicio para registrarlos con SQLAlchemy
# Esto es necesario para que los tests unitarios que instancian modelos directamente funcionen
from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401

# Inicializar Faker para español
fake = Faker('es_ES')

# Database fixtures for integration tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_manager():
    """Crea un DatabaseManager para pruebas usando una base de datos en memoria."""

    # Creamos una clase que hereda de DatabaseManager para tests
    class TestDatabaseManager(DatabaseManager):
        def __new__(cls):
            # Aseguramos que siempre se cree una nueva instancia para tests
            return super(DatabaseManager, cls).__new__(cls)

        def __init__(self):
            # Configuramos la base de datos en memoria para tests
            self._engine = create_async_engine(
                TEST_DATABASE_URL, echo=False, future=True
            )

            # Session factory para tests
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            self._initialized = True

    # Creamos una instancia del manejador de BD para tests
    test_db = TestDatabaseManager()

    # Importamos los modelos para registrarlos con Base
    # from src.models.auth.rol_model import RolModel  # noqa: F401  # ELIMINADO: Ya no existe RolModel
    from src.models.pagos.division_cuenta_model import DivisionCuentaModel  # noqa: F401
    from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel  # noqa: F401
    from src.models.auth.usuario_model import UsuarioModel  # noqa: F401
    from src.models.mesas.mesa_model import MesaModel  # noqa: F401
    from src.models.mesas.local_model import LocalModel  # noqa: F401
    from src.models.mesas.zona_model import ZonaModel  # noqa: F401
    from src.models.mesas.sesion_mesa_model import SesionMesaModel  # noqa: F401
    from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel  # noqa: F401

    # Creamos las tablas
    async with test_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_db

    # Limpiamos después de los tests
    async with test_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_db.close()


@pytest.fixture
async def db_session(test_db_manager):
    """Crea una sesión de base de datos para pruebas de integración."""
    async with test_db_manager.session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def override_get_db(db_session):
    """Proporciona una dependencia de DB para inyección."""

    async def _get_db():
        try:
            yield db_session
        finally:
            pass

    return _get_db


@pytest.fixture
def test_client():
    """Fixture para TestClient de FastAPI"""
    return TestClient(app)


@pytest.fixture
async def async_client(override_get_db):
    """Cliente async para pruebas de integración."""
    app.dependency_overrides[get_db] = override_get_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
def mock_db_session():
    """Fixture para mock de sesión de BD (sync)"""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def async_mock_db_session():
    """Fixture para mock de sesión de BD (async)"""
    mock_session = AsyncMock()
    return mock_session


@pytest.fixture
def cleanup_app():
    """Limpia dependency_overrides después de cada test"""
    yield
    app.dependency_overrides = {}


# ============================================================================
# FAKE DATA GENERATORS - Para crear datos de prueba reutilizables
# ============================================================================

# FIXTURE ELIMINADA: fake_rol_data
# Ya no existe RolModel en el sistema
# @pytest.fixture
# def fake_rol_data():
#     ...


@pytest.fixture
def fake_usuario_data():
    """
    Genera datos fake para un Usuario (simplificado).

    Returns:
        dict: Datos de usuario con valores fake realistas

    Uso:
        def test_ejemplo(fake_usuario_data):
            usuario = UsuarioModel(**fake_usuario_data)
    """
    return {
        "id": str(ULID()),
        "email": fake.email(),
        "nombre": fake.name(),
        "ultimo_acceso": fake.date_time_this_year(),
    }


@pytest.fixture
def fake_categoria_data():
    """
    Genera datos fake para una Categoría.
    
    Returns:
        dict: Datos de categoría con valores fake realistas
    """
    return {
        "id": str(ULID()),
        "nombre": fake.word().capitalize()[:50],
        "descripcion": fake.sentence(),
        "imagen_path": f"/images/{fake.file_name(extension='jpg')}",
        "activo": True,
    }


@pytest.fixture
def fake_producto_data(fake_categoria_data):
    """
    Genera datos fake para un Producto.
    
    Returns:
        dict: Datos de producto con valores fake realistas
    """
    return {
        "id": str(ULID()),
        "id_categoria": fake_categoria_data["id"],
        "nombre": f"{fake.word().capitalize()} {fake.word()}",
        "descripcion": fake.text(max_nb_chars=200),
        "precio_base": Decimal(fake.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=5, max_value=100)),
        "imagen_path": f"/images/{fake.file_name(extension='jpg')}",
        "imagen_alt_text": fake.sentence(nb_words=5),
        "disponible": True,
        "destacado": fake.boolean(),
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.fixture
def fake_alergeno_data():
    """
    Genera datos fake para un Alérgeno.
    
    Returns:
        dict: Datos de alérgeno con valores fake realistas
    """
    alergenos = [
        "Gluten", "Crustáceos", "Huevos", "Pescado", "Cacahuetes",
        "Soja", "Lácteos", "Frutos secos", "Apio", "Mostaza",
        "Sésamo", "Sulfitos", "Altramuces", "Moluscos"
    ]
    return {
        "id": str(ULID()),
        "nombre": fake.random_element(elements=alergenos),
        "descripcion": fake.sentence(),
        "icono_path": f"/icons/{fake.file_name(extension='svg')}",
        "activo": True,
    }


@pytest.fixture
def fake_producto_alergeno_data(fake_producto_data, fake_alergeno_data):
    """
    Genera datos fake para una relación Producto-Alérgeno.
    
    Returns:
        dict: Datos de producto-alérgeno con valores fake realistas
    """
    from src.core.enums.alergeno_enums import NivelPresencia
    
    return {
        "id_producto": fake_producto_data["id"],
        "id_alergeno": fake_alergeno_data["id"],
        "nivel_presencia": fake.random_element(elements=list(NivelPresencia)),
        "notas": fake.sentence() if fake.boolean() else None,
        "activo": True,
    }


# ============================================================================
# FAKE DATA FACTORIES - Para crear múltiples instancias
# ============================================================================

@pytest.fixture
def create_fake_rol():
    """
    Factory para crear múltiples roles fake.
    
    Returns:
        callable: Función que genera datos de rol
    
    Uso:
        def test_ejemplo(create_fake_rol):
            rol1 = create_fake_rol()
            rol2 = create_fake_rol(nombre="Admin")
    """
    def _create_fake_rol(**kwargs):
        data = {
            "id": str(ULID()),
            "nombre": fake.job()[:50],
            "descripcion": fake.text(max_nb_chars=200),
            "activo": True,
        }
        data.update(kwargs)
        return data
    
    return _create_fake_rol


@pytest.fixture
def create_fake_usuario():
    """
    Factory para crear múltiples usuarios fake.
    
    Returns:
        callable: Función que genera datos de usuario
    
    Uso:
        def test_ejemplo(create_fake_usuario):
            user1 = create_fake_usuario()
            user2 = create_fake_usuario(email="custom@test.com")
    """
    def _create_fake_usuario(**kwargs):
        data = {
            "id": str(ULID()),
            "id_rol": str(ULID()),
            "email": fake.email(),
            "password_hash": fake.sha256(),
            "nombre": fake.name(),
            "telefono": fake.phone_number()[:20],
            "activo": True,
            "ultimo_acceso": fake.date_time_this_year(),
        }
        data.update(kwargs)
        return data
    
    return _create_fake_usuario


@pytest.fixture
def create_fake_producto():
    """
    Factory para crear múltiples productos fake.
    
    Returns:
        callable: Función que genera datos de producto
    
    Uso:
        def test_ejemplo(create_fake_producto):
            producto1 = create_fake_producto()
            producto2 = create_fake_producto(precio_base=Decimal("15.99"))
    """
    def _create_fake_producto(**kwargs):
        data = {
            "id": str(ULID()),
            "id_categoria": str(ULID()),
            "nombre": f"{fake.word().capitalize()} {fake.word()}",
            "descripcion": fake.text(max_nb_chars=200),
            "precio_base": Decimal(fake.pyfloat(left_digits=2, right_digits=2, positive=True, min_value=5, max_value=100)),
            "imagen_path": f"/images/{fake.file_name(extension='jpg')}",
            "imagen_alt_text": fake.sentence(nb_words=5),
            "disponible": True,
            "destacado": fake.boolean(),
        }
        data.update(kwargs)
        return data
    
    return _create_fake_producto


@pytest.fixture
def create_fake_producto_alergeno():
    """
    Factory para crear múltiples relaciones producto-alergeno fake.
    
    Returns:
        callable: Función que genera datos de producto_alergeno
    
    Uso:
        def test_ejemplo(create_fake_producto_alergeno):
            rel1 = create_fake_producto_alergeno()
            rel2 = create_fake_producto_alergeno(nivel_presencia=NivelPresencia.CONTIENE)
    """
    from src.core.enums.alergeno_enums import NivelPresencia
    
    def _create_fake_producto_alergeno(**kwargs):
        data = {
            "id_producto": str(ULID()),
            "id_alergeno": str(ULID()),
            "nivel_presencia": fake.random_element(elements=[
                NivelPresencia.CONTIENE,
                NivelPresencia.PUEDE_CONTENER,
                NivelPresencia.TRAZAS
            ]),
        }
        data.update(kwargs)
        return data
    
    return _create_fake_producto_alergeno
