"""Pruebas unitarias para el servicio de alérgenos."""

import pytest
from unittest.mock import AsyncMock
from ulid import ULID
from datetime import datetime

from src.business_logic.menu.alergeno_service import AlergenoService
from src.api.schemas.alergeno_schema import AlergenoList, AlergenoSummary
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.core.enums.alergeno_enums import NivelRiesgo


@pytest.fixture
def mock_repository():
    """Fixture que proporciona un mock del repositorio de alérgenos."""
    return AsyncMock()


@pytest.fixture
def alergeno_service(mock_repository):
    """Fixture que proporciona una instancia del servicio de alérgenos con un repositorio mockeado."""
    service = AlergenoService(AsyncMock())
    service._repository = mock_repository
    return service


@pytest.fixture
def sample_alergeno_data():
    """Fixture que proporciona datos de muestra para un alérgeno."""
    return {
        "id": str(ULID()),
        "nombre": "Test Alérgeno",
        "descripcion": "Alérgeno para pruebas",
        "icono": "🧪",
        "nivel_riesgo": NivelRiesgo.MEDIO,
        "activo": True,
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_get_alergenos_success(alergeno_service, mock_repository, sample_alergeno_data):
    """Prueba la obtención exitosa de una lista paginada de alérgenos."""
    # Arrange
    alergeno_list = AlergenoList(
        items=[
            AlergenoSummary(
                id=sample_alergeno_data["id"],
                nombre=sample_alergeno_data["nombre"],
                nivel_riesgo=sample_alergeno_data["nivel_riesgo"],
                activo=True
            )
        ],
        total=1
    )
    mock_repository.get_all_paginated.return_value = alergeno_list

    # Act
    result = await alergeno_service.get_alergenos(skip=0, limit=10)

    # Assert
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].nombre == sample_alergeno_data["nombre"]
    mock_repository.get_all_paginated.assert_called_once_with(0, 10, None)


@pytest.mark.asyncio
async def test_get_alergenos_validation_error_skip_negativo(alergeno_service):
    """Prueba el manejo de errores cuando skip es negativo."""
    # Act & Assert
    with pytest.raises(AlergenoValidationError) as excinfo:
        await alergeno_service.get_alergenos(skip=-1, limit=10)
    assert "skip" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_get_alergenos_validation_error_limit_cero(alergeno_service):
    """Prueba el manejo de errores cuando limit es cero."""
    # Act & Assert
    with pytest.raises(AlergenoValidationError) as excinfo:
        await alergeno_service.get_alergenos(skip=0, limit=0)
    assert "limit" in str(excinfo.value).lower()
