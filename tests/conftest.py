"""Global fixtures for all tests."""

import pytest
import asyncio
import httpx
from ulid import ULID
from decimal import Decimal
from datetime import datetime
from faker import Faker
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)

from src.main import app
from src.core.database import get_database_session as get_db
from src.models.base_model import BaseModel as Base
from src.models.auth.admin_model import AdminModel
from src.core.security import security
from src.core.model_registry import register_all_models

# Registrar todos los modelos al inicio
register_all_models()

# Inicializar Faker para español
fake = Faker('es_ES')

# Database configuration for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ==================== Database Fixtures ====================

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Crea un motor de base de datos para tests en memoria."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Limpiar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session_factory(test_engine):
    """Crea una factoría de sesiones para tests."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture
async def db_session(test_session_factory):
    """Crea una sesión de base de datos para pruebas de integración."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def override_get_db(db_session):
    """Proporciona una dependencia de DB para inyección."""
    async def _get_db():
        yield db_session
    return _get_db


@pytest.fixture
def test_client():
    """Fixture para TestClient de FastAPI"""
    return TestClient(app)


@pytest.fixture
async def test_admin(db_session):
    """Crea un admin de prueba en la base de datos."""
    admin = AdminModel(
        id=str(ULID()),
        usuario="admin_test",
        email="admin@test.com",
        password=security.get_password_hash("testpassword123")
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token(test_admin):
    """Genera un token JWT válido para el admin de prueba."""
    token_data = {
        "sub": test_admin.id,
        "email": test_admin.email,
        "usuario": test_admin.usuario
    }
    return security.create_access_token(data=token_data)


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


# ==================== Fake Data Generators ====================

@pytest.fixture
def fake_usuario_data():
    """Genera datos fake para un Usuario."""
    return {
        "id": str(ULID()),
        "email": fake.email(),
        "nombre": fake.name(),
        "ultimo_acceso": fake.date_time_this_year(),
    }


@pytest.fixture
def fake_categoria_data():
    """Genera datos fake para una Categoría."""
    return {
        "id": str(ULID()),
        "nombre": fake.word().capitalize()[:50],
        "descripcion": fake.sentence(),
        "imagen_path": f"/images/{fake.file_name(extension='jpg')}",
        "activo": True,
    }


@pytest.fixture
def fake_producto_data(fake_categoria_data):
    """Genera datos fake para un Producto."""
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
    """Genera datos fake para un Alérgeno."""
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
    """Genera datos fake para una relación Producto-Alérgeno."""
    from src.core.enums.alergeno_enums import NivelPresencia
    
    return {
        "id_producto": fake_producto_data["id"],
        "id_alergeno": fake_alergeno_data["id"],
        "nivel_presencia": fake.random_element(elements=list(NivelPresencia)),
        "notas": fake.sentence() if fake.boolean() else None,
        "activo": True,
    }


# ==================== Fake Data Factories ====================

@pytest.fixture
def create_fake_rol():
    """Factory para crear múltiples roles fake."""
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
    """Factory para crear múltiples usuarios fake."""
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
