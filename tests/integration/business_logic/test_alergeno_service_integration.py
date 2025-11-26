"""Pruebas de integración para el servicio de alérgenos."""

import pytest
from ulid import ULID

from src.business_logic.menu.alergeno_service import AlergenoService
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.core.enums.alergeno_enums import NivelRiesgo
from src.models.menu.alergeno_model import AlergenoModel


@pytest.fixture(scope="function")
def alergeno_service(db_session) -> AlergenoService:
    """Crea una instancia del servicio de alérgenos con una sesión de base de datos."""
    return AlergenoService(db_session)


@pytest.mark.asyncio
async def test_integration_get_alergenos(alergeno_service: AlergenoService, db_session):
    """Prueba de integración para verificar la recuperación paginada de alérgenos."""
    # Arrange - Crear múltiples alérgenos directamente en la BD
    for i in range(5):
        alergeno = AlergenoModel(
            nombre=f"alergeno_paginacion_{i}",
            descripcion=f"Alérgeno para probar paginación {i}",
            nivel_riesgo=NivelRiesgo.MEDIO,
            activo=True
        )
        db_session.add(alergeno)
    await db_session.commit()

    # Act - Recuperar con paginación
    alergenos = await alergeno_service.get_alergenos(skip=0, limit=3)

    # Assert - Verificar la paginación
    assert alergenos is not None
    assert isinstance(alergenos.items, list)
    assert len(alergenos.items) == 3  # Limitamos a 3
    assert alergenos.total == 5  # Total de alérgenos creados

    # Verificar que todos son instancias de AlergenoSummary
    assert all(hasattr(item, 'id') for item in alergenos.items)
    assert all(hasattr(item, 'nombre') for item in alergenos.items)

    # Probar con offset
    alergenos_offset = await alergeno_service.get_alergenos(skip=2, limit=2)
    assert len(alergenos_offset.items) == 2
    assert alergenos_offset.total == 5


@pytest.mark.asyncio
async def test_integration_validation_errors(alergeno_service: AlergenoService):
    """Prueba de integración para verificar las validaciones de parámetros."""
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(AlergenoValidationError) as excinfo:
        await alergeno_service.get_alergenos(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(AlergenoValidationError) as excinfo:
        await alergeno_service.get_alergenos(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)
