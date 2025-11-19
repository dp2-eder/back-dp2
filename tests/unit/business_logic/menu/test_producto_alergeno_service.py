"""
Pruebas unitarias para el servicio de relaciones producto-alérgeno.
"""

import pytest
from ulid import ULID
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.business_logic.menu.producto_alergeno_service import ProductoAlergenoService
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.api.schemas.producto_alergeno_schema import (
    ProductoAlergenoCreate,
    ProductoAlergenoUpdate,
)
from src.business_logic.exceptions.producto_alergeno_exceptions import (
    ProductoAlergenoValidationError,
    ProductoAlergenoNotFoundError,
    ProductoAlergenoConflictError,
)
from src.core.enums.alergeno_enums import NivelPresencia
from sqlalchemy.exc import IntegrityError

# Importar modelos relacionados para resolver dependencias de SQLAlchemy
from src.models.menu.producto_model import ProductoModel  # noqa: F401
from src.models.menu.alergeno_model import AlergenoModel  # noqa: F401


@pytest.fixture
def mock_repository():
    """
    Fixture que proporciona un mock del repositorio de producto-alérgeno.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def producto_alergeno_service(mock_repository):
    """
    Fixture que proporciona una instancia del servicio con un repositorio mockeado.
    """
    service = ProductoAlergenoService(AsyncMock())
    service.repository = mock_repository
    return service


@pytest.fixture
def sample_producto_alergeno_data():
    """
    Fixture que proporciona datos de muestra para una relación producto-alérgeno.
    """
    return {
        "id_producto": str(ULID()),
        "id_alergeno": str(ULID()),
        "nivel_presencia": NivelPresencia.CONTIENE,
        "notas": "Contiene gluten",
        "activo": True,
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.mark.asyncio
async def test_create_producto_alergeno_success(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba la creación exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Llama al método create_producto_alergeno con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe crear la relación correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    producto_alergeno_create = ProductoAlergenoCreate(
        id_producto=sample_producto_alergeno_data["id_producto"],
        id_alergeno=sample_producto_alergeno_data["id_alergeno"],
        nivel_presencia=sample_producto_alergeno_data["nivel_presencia"],
        notas=sample_producto_alergeno_data["notas"],
    )
    mock_repository.create.return_value = ProductoAlergenoModel(
        **sample_producto_alergeno_data
    )

    # Act
    result = await producto_alergeno_service.create_producto_alergeno(
        producto_alergeno_create
    )

    # Assert
    assert result.id_producto == sample_producto_alergeno_data["id_producto"]
    assert result.id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert result.nivel_presencia == sample_producto_alergeno_data["nivel_presencia"]
    assert result.notas == sample_producto_alergeno_data["notas"]
    mock_repository.create.assert_called_once()

    # Verificar que se pasó un objeto ProductoAlergenoModel al repositorio
    args, _ = mock_repository.create.call_args
    assert isinstance(args[0], ProductoAlergenoModel)
    assert args[0].id_producto == sample_producto_alergeno_data["id_producto"]
    assert args[0].id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert args[0].nivel_presencia == sample_producto_alergeno_data["nivel_presencia"]
    assert args[0].notas == sample_producto_alergeno_data["notas"]


@pytest.mark.asyncio
async def test_create_producto_alergeno_duplicate(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba el manejo de errores al intentar crear una relación duplicada.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular un error de integridad.
        - Llama al método create_producto_alergeno con una relación duplicada.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoAlergenoConflictError.
    """
    # Arrange
    producto_alergeno_create = ProductoAlergenoCreate(
        id_producto=sample_producto_alergeno_data["id_producto"],
        id_alergeno=sample_producto_alergeno_data["id_alergeno"],
        nivel_presencia=sample_producto_alergeno_data["nivel_presencia"],
        notas=sample_producto_alergeno_data["notas"],
    )
    mock_repository.create.side_effect = IntegrityError(
        statement="Duplicate entry", params={}, orig=Exception("Duplicate entry")
    )

    # Act & Assert
    with pytest.raises(ProductoAlergenoConflictError) as excinfo:
        await producto_alergeno_service.create_producto_alergeno(
            producto_alergeno_create
        )

    assert "Ya existe una relación entre el producto" in str(excinfo.value)
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_producto_alergeno_by_id_success(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba la obtención exitosa de una relación por su ID único.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia de la relación.
        - Llama al método get_producto_alergeno_by_id con ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la relación correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    id_relacion = str(ULID())
    producto_alergeno = ProductoAlergenoModel(**sample_producto_alergeno_data)
    producto_alergeno.id = id_relacion
    mock_repository.get_by_id.return_value = producto_alergeno

    # Act
    result = await producto_alergeno_service.get_producto_alergeno_by_id(id_relacion)

    # Assert
    assert result.id == id_relacion
    assert result.id_producto == sample_producto_alergeno_data["id_producto"]
    assert result.id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert result.nivel_presencia == sample_producto_alergeno_data["nivel_presencia"]
    assert result.notas == sample_producto_alergeno_data["notas"]
    mock_repository.get_by_id.assert_called_once_with(id_relacion)


@pytest.mark.asyncio
async def test_get_producto_alergeno_by_id_not_found(
    producto_alergeno_service, mock_repository
):
    """
    Prueba el manejo de errores al intentar obtener una relación que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Llama al método get_producto_alergeno_by_id con ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoAlergenoNotFoundError.
    """
    # Arrange
    id_relacion = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ProductoAlergenoNotFoundError) as excinfo:
        await producto_alergeno_service.get_producto_alergeno_by_id(id_relacion)

    assert f"No se encontró la relación con ID {id_relacion}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(id_relacion)


@pytest.mark.asyncio
async def test_delete_producto_alergeno_success(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba la eliminación exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia y eliminación exitosa.
        - Llama al método delete_producto_alergeno con ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe eliminar la relación correctamente.
        - El repositorio debe ser llamado con el ID correcto.
    """
    # Arrange
    id_relacion = str(ULID())
    producto_alergeno = ProductoAlergenoModel(**sample_producto_alergeno_data)
    producto_alergeno.id = id_relacion
    mock_repository.get_by_id.return_value = producto_alergeno
    mock_repository.delete.return_value = True

    # Act
    result = await producto_alergeno_service.delete_producto_alergeno(id_relacion)

    # Assert
    assert result is True
    mock_repository.get_by_id.assert_called_once_with(id_relacion)
    mock_repository.delete.assert_called_once_with(id_relacion)


@pytest.mark.asyncio
async def test_delete_producto_alergeno_not_found(
    producto_alergeno_service, mock_repository
):
    """
    Prueba el manejo de errores al intentar eliminar una relación que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Llama al método delete_producto_alergeno con ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoAlergenoNotFoundError.
    """
    # Arrange
    id_relacion = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(ProductoAlergenoNotFoundError) as excinfo:
        await producto_alergeno_service.delete_producto_alergeno(id_relacion)

    assert f"No se encontró la relación con ID {id_relacion}" in str(excinfo.value)
    mock_repository.get_by_id.assert_called_once_with(id_relacion)
    mock_repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_producto_alergenos_success(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba la obtención exitosa de una lista paginada de relaciones.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de relaciones.
        - Llama al método get_producto_alergenos con parámetros válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de relaciones correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    producto_alergenos = [
        ProductoAlergenoModel(**sample_producto_alergeno_data),
        ProductoAlergenoModel(
            id_producto=str(ULID()),
            id_alergeno=str(ULID()),
            nivel_presencia=NivelPresencia.TRAZAS,
            notas="Puede contener trazas",
            activo=True,
        ),
    ]
    mock_repository.get_all.return_value = (producto_alergenos, len(producto_alergenos))

    # Act
    result = await producto_alergeno_service.get_producto_alergenos(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    assert result.items[0].id_producto == sample_producto_alergeno_data["id_producto"]
    assert result.items[0].id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert result.items[1].nivel_presencia == NivelPresencia.TRAZAS
    mock_repository.get_all.assert_called_once_with(0, 10)


@pytest.mark.asyncio
async def test_get_producto_alergenos_validation_error(producto_alergeno_service):
    """
    Prueba el manejo de errores al proporcionar parámetros inválidos.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Llama al método get_producto_alergenos con parámetros inválidos.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoAlergenoValidationError.
    """
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(ProductoAlergenoValidationError) as excinfo:
        await producto_alergeno_service.get_producto_alergenos(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(ProductoAlergenoValidationError) as excinfo:
        await producto_alergeno_service.get_producto_alergenos(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_producto_alergeno_success(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba la actualización exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la actualización exitosa.
        - Llama al método update_producto_alergeno con datos válidos.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe actualizar la relación correctamente.
        - El repositorio debe ser llamado con los parámetros correctos.
    """
    # Arrange
    id_relacion = str(ULID())
    update_data = ProductoAlergenoUpdate(
        nivel_presencia=NivelPresencia.TRAZAS, notas="Actualizado: contiene trazas"
    )

    updated_producto_alergeno = ProductoAlergenoModel(
        **{
            **sample_producto_alergeno_data,
            "nivel_presencia": NivelPresencia.TRAZAS,
            "notas": "Actualizado: contiene trazas",
        }
    )
    updated_producto_alergeno.id = id_relacion
    mock_repository.update.return_value = updated_producto_alergeno

    # Act
    result = await producto_alergeno_service.update_producto_alergeno(
        id_relacion, update_data
    )

    # Assert
    assert result.id == id_relacion
    assert result.id_producto == sample_producto_alergeno_data["id_producto"]
    assert result.id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert result.nivel_presencia == NivelPresencia.TRAZAS
    assert result.notas == "Actualizado: contiene trazas"
    mock_repository.update.assert_called_once_with(
        id_relacion,
        nivel_presencia=NivelPresencia.TRAZAS,
        notas="Actualizado: contiene trazas",
    )


@pytest.mark.asyncio
async def test_update_producto_alergeno_not_found(
    producto_alergeno_service, mock_repository
):
    """
    Prueba el manejo de errores al intentar actualizar una relación que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Llama al método update_producto_alergeno con ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar ProductoAlergenoNotFoundError.
    """
    # Arrange
    id_relacion = str(ULID())
    update_data = ProductoAlergenoUpdate(nivel_presencia=NivelPresencia.TRAZAS)
    mock_repository.update.return_value = None

    # Act & Assert
    with pytest.raises(ProductoAlergenoNotFoundError) as excinfo:
        await producto_alergeno_service.update_producto_alergeno(
            id_relacion, update_data
        )

    assert f"No se encontró la relación con ID {id_relacion}" in str(excinfo.value)
    mock_repository.update.assert_called_once_with(
        id_relacion, nivel_presencia=NivelPresencia.TRAZAS
    )


@pytest.mark.asyncio
async def test_update_producto_alergeno_no_changes(
    producto_alergeno_service, mock_repository, sample_producto_alergeno_data
):
    """
    Prueba el comportamiento al intentar actualizar sin proporcionar cambios.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia de la relación.
        - Llama al método update_producto_alergeno sin datos de actualización.
        - Verifica que se retorne la relación sin modificar.

    POSTCONDICIONES:
        - El servicio debe retornar la relación actual sin cambios.
        - El repositorio update no debe ser llamado.
    """
    # Arrange
    id_relacion = str(ULID())
    update_data = ProductoAlergenoUpdate()  # Sin cambios
    producto_alergeno = ProductoAlergenoModel(**sample_producto_alergeno_data)
    producto_alergeno.id = id_relacion
    mock_repository.get_by_id.return_value = producto_alergeno

    # Act
    result = await producto_alergeno_service.update_producto_alergeno(
        id_relacion, update_data
    )

    # Assert
    assert result.id == id_relacion
    assert result.id_producto == sample_producto_alergeno_data["id_producto"]
    assert result.id_alergeno == sample_producto_alergeno_data["id_alergeno"]
    assert result.nivel_presencia == sample_producto_alergeno_data["nivel_presencia"]
    mock_repository.get_by_id.assert_called_once_with(id_relacion)
    mock_repository.update.assert_not_called()
