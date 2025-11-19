"""
Pruebas unitarias para el servicio de zonas.
"""

import pytest
from unittest.mock import AsyncMock
from ulid import ULID
from datetime import datetime

from src.business_logic.mesas.zona_service import ZonaService
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.local_model import LocalModel
from src.api.schemas.zona_schema import ZonaCreate, ZonaUpdate
from src.business_logic.exceptions.zona_exceptions import (
    ZonaValidationError,
    ZonaNotFoundError,
    ZonaConflictError,
)
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repositories():
    """Fixture que proporciona mocks de los repositorios."""
    zona_repo = AsyncMock()
    local_repo = AsyncMock()
    return zona_repo, local_repo


@pytest.fixture
def zona_service(mock_repositories):
    """Fixture que proporciona una instancia del servicio con repositorios mockeados."""
    service = ZonaService(AsyncMock())
    service.repository, service.local_repository = mock_repositories
    return service


@pytest.fixture
def sample_zona_data():
    """Fixture con datos de muestra para una zona."""
    return {
        "id": str(ULID()),
        "id_local": str(ULID()),
        "nombre": "Terraza",
        "descripcion": "Zona de terraza con vista",
        "nivel": 0,
        "capacidad_maxima": 40,
        "activo": True,
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_create_zona_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba la creación exitosa de una zona."""
    zona_repo, local_repo = mock_repositories

    # Mock: el local existe
    local_repo.get_by_id.return_value = LocalModel(
        id=sample_zona_data["id_local"],
        codigo="CEV-001",
        nombre="Local Test",
        direccion="Dir Test",
    )

    zona_create = ZonaCreate(
        id_local=sample_zona_data["id_local"],
        nombre=sample_zona_data["nombre"],
        descripcion=sample_zona_data["descripcion"],
        nivel=sample_zona_data["nivel"],
        capacidad_maxima=sample_zona_data["capacidad_maxima"],
    )
    zona_repo.create.return_value = ZonaModel(**sample_zona_data)

    result = await zona_service.create_zona(zona_create)

    assert result.id == sample_zona_data["id"]
    assert result.nombre == sample_zona_data["nombre"]
    zona_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_zona_local_not_exists(zona_service, mock_repositories):
    """Prueba error al crear zona con local inexistente."""
    zona_repo, local_repo = mock_repositories
    local_repo.get_by_id.return_value = None

    zona_create = ZonaCreate(
        id_local=str(ULID()),
        nombre="Terraza",
        nivel=0,
    )

    with pytest.raises(ZonaValidationError) as excinfo:
        await zona_service.create_zona(zona_create)

    assert "no existe" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_zona_invalid_nivel(zona_service, mock_repositories, sample_zona_data):
    """Prueba error al crear zona con nivel inválido."""
    from pydantic import ValidationError

    zona_repo, local_repo = mock_repositories
    local_repo.get_by_id.return_value = LocalModel(
        id=sample_zona_data["id_local"],
        codigo="CEV-001",
        nombre="Local Test",
        direccion="Dir Test",
    )

    # Pydantic valida antes de llegar al servicio
    with pytest.raises(ValidationError) as excinfo:
        zona_create = ZonaCreate(
            id_local=sample_zona_data["id_local"],
            nombre="Test",
            nivel=5,  # Inválido
        )

    assert "less_than_equal" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_zona_by_id_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba la obtención exitosa de una zona por ID."""
    zona_repo, local_repo = mock_repositories
    zona_repo.get_by_id.return_value = ZonaModel(**sample_zona_data)

    result = await zona_service.get_zona_by_id(sample_zona_data["id"])

    assert result.id == sample_zona_data["id"]
    zona_repo.get_by_id.assert_called_once_with(sample_zona_data["id"])


@pytest.mark.asyncio
async def test_get_zona_by_id_not_found(zona_service, mock_repositories):
    """Prueba error al obtener zona inexistente."""
    zona_repo, local_repo = mock_repositories
    zona_repo.get_by_id.return_value = None
    zona_id = str(ULID())

    with pytest.raises(ZonaNotFoundError):
        await zona_service.get_zona_by_id(zona_id)


@pytest.mark.asyncio
async def test_delete_zona_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba la eliminación exitosa de una zona."""
    zona_repo, local_repo = mock_repositories
    zona_repo.get_by_id.return_value = ZonaModel(**sample_zona_data)
    zona_repo.delete.return_value = True

    result = await zona_service.delete_zona(sample_zona_data["id"])

    assert result is True
    zona_repo.delete.assert_called_once_with(sample_zona_data["id"])


@pytest.mark.asyncio
async def test_get_zonas_by_local_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba obtener zonas por local."""
    zona_repo, local_repo = mock_repositories
    zonas = [ZonaModel(**sample_zona_data)]
    zona_repo.get_by_local.return_value = (zonas, 1)

    result = await zona_service.get_zonas_by_local(sample_zona_data["id_local"], 0, 10)

    assert result.total == 1
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_get_zonas_by_nivel_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba obtener zonas por nivel."""
    zona_repo, local_repo = mock_repositories
    zonas = [ZonaModel(**sample_zona_data)]
    zona_repo.get_by_nivel.return_value = (zonas, 1)

    result = await zona_service.get_zonas_by_nivel(0, 0, 10)

    assert result.total == 1
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_update_zona_success(zona_service, mock_repositories, sample_zona_data):
    """Prueba la actualización exitosa de una zona."""
    zona_repo, local_repo = mock_repositories
    update_data = ZonaUpdate(nombre="Zona Actualizada")
    updated_zona = ZonaModel(**{**sample_zona_data, "nombre": "Zona Actualizada"})
    zona_repo.update.return_value = updated_zona

    result = await zona_service.update_zona(sample_zona_data["id"], update_data)

    assert result.nombre == "Zona Actualizada"


@pytest.mark.asyncio
async def test_update_zona_not_found(zona_service, mock_repositories):
    """Prueba error al actualizar zona inexistente."""
    zona_repo, local_repo = mock_repositories
    zona_repo.update.return_value = None
    update_data = ZonaUpdate(nombre="Test")

    with pytest.raises(ZonaNotFoundError):
        await zona_service.update_zona(str(ULID()), update_data)
