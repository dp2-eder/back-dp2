"""Pruebas unitarias para los endpoints de alérgenos."""

import pytest
from unittest.mock import patch, AsyncMock
from ulid import ULID

from src.api.schemas.alergeno_schema import AlergenoList, AlergenoSummary
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.business_logic.menu.alergeno_service import AlergenoService
from src.core.enums.alergeno_enums import NivelRiesgo


@pytest.fixture
def sample_alergeno_data():
    """Proporciona datos de muestra para un alérgeno."""
    return {
        "id": str(ULID()),
        "nombre": "Gluten",
        "nivel_riesgo": NivelRiesgo.ALTO,
        "activo": True,
    }


@pytest.mark.asyncio
async def test_list_alergenos_service_success(sample_alergeno_data):
    """Prueba que el servicio retorna correctamente la lista de alérgenos."""
    # Arrange
    mock_session = AsyncMock()
    mock_repository = AsyncMock()
    
    alergeno_summary = AlergenoSummary(**sample_alergeno_data)
    alergeno_list = AlergenoList(items=[alergeno_summary], total=1)
    mock_repository.get_all_paginated.return_value = alergeno_list
    
    service = AlergenoService(mock_session)
    service._repository = mock_repository
    
    # Act
    result = await service.get_alergenos(skip=0, limit=10)
    
    # Assert
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].nombre == sample_alergeno_data["nombre"]


@pytest.mark.asyncio
async def test_list_alergenos_validation_error():
    """Prueba el manejo de errores de validación en el servicio."""
    # Arrange
    mock_session = AsyncMock()
    service = AlergenoService(mock_session)
    
    # Act & Assert
    with pytest.raises(AlergenoValidationError) as excinfo:
        await service.get_alergenos(skip=-1, limit=10)
    assert "skip" in str(excinfo.value).lower()

