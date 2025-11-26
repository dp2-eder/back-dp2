"""
Pruebas unitarias para el servicio de categorías.
"""

import pytest
from unittest.mock import AsyncMock
from ulid import ULID
from datetime import datetime


from src.business_logic.menu.categoria_service import CategoriaService
from src.models.menu.categoria_model import CategoriaModel
from src.api.schemas.categoria_schema import CategoriaCreate, CategoriaUpdate
from src.business_logic.exceptions.categoria_exceptions import (
    CategoriaValidationError,
    CategoriaNotFoundError,
    CategoriaConflictError,
)
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository():
    """
    Fixture que proporciona un mock del repositorio de categorías.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def categoria_service(mock_repository):
    """
    Fixture que proporciona una instancia del servicio de categorías con un repositorio mockeado.
    """
    service = CategoriaService(AsyncMock())
    service.repository = mock_repository
    return service


@pytest.fixture
def sample_categoria_data():
    """
    Fixture que proporciona datos de muestra para una categoría.
    """
    return {
        "id": str(ULID()),
        "nombre": "Test Categoría",
        "descripcion": "Categoría para pruebas",
        "imagen_path": "/images/test.jpg",
        "activo": True,
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_get_categorias_success(categoria_service, mock_repository, sample_categoria_data):
    """
    Prueba la obtención exitosa de una lista paginada de categorías.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de categorías.
        - Llama al método get_categorias con parámetros válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de categorías correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    categorias = [
        CategoriaModel(**sample_categoria_data),
        CategoriaModel(
            id=str(ULID()),
            nombre="Otra Categoría",
            descripcion="Otra categoría para pruebas",
            imagen_path="/images/otra.jpg",
            activo=True,
        ),
    ]
    mock_repository.get_all.return_value = (categorias, len(categorias))

    # Act
    result = await categoria_service.get_categorias(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].nombre == sample_categoria_data["nombre"]
    assert result.items[1].nombre == "Otra Categoría"
    mock_repository.get_all.assert_called_once_with(0, 10)


@pytest.mark.asyncio
async def test_get_categorias_validation_error(categoria_service):
    """
    Prueba el manejo de errores al proporcionar parámetros inválidos para obtener categorías.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Llama al método get_categorias con parámetros inválidos.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar CategoriaValidationError.
    """
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(CategoriaValidationError) as excinfo:
        await categoria_service.get_categorias(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(CategoriaValidationError) as excinfo:
        await categoria_service.get_categorias(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)
