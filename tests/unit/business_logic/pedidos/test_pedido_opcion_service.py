"""
Pruebas unitarias para el servicio de opciones de pedidos.
"""

import pytest
from unittest.mock import AsyncMock
from ulid import ULID
from datetime import datetime
from decimal import Decimal

from src.business_logic.pedidos.pedido_opcion_service import PedidoOpcionService
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.api.schemas.pedido_opcion_schema import PedidoOpcionCreate, PedidoOpcionUpdate
from src.business_logic.exceptions.pedido_opcion_exceptions import (
    PedidoOpcionValidationError,
    PedidoOpcionNotFoundError,
    PedidoOpcionConflictError,
)
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository():
    """
    Fixture que proporciona un mock del repositorio de opciones de pedidos.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_pedido_producto_repository():
    """
    Fixture que proporciona un mock del repositorio de items de pedidos.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_producto_opcion_repository():
    """
    Fixture que proporciona un mock del repositorio de opciones de productos.
    """
    repository = AsyncMock()
    return repository


@pytest.fixture
def pedido_opcion_service(mock_repository, mock_pedido_producto_repository, mock_producto_opcion_repository):
    """
    Fixture que proporciona una instancia del servicio con repositorios mockeados.
    """
    service = PedidoOpcionService(AsyncMock())
    service.repository = mock_repository
    service.pedido_producto_repository = mock_pedido_producto_repository
    service.producto_opcion_repository = mock_producto_opcion_repository
    return service


@pytest.fixture
def sample_pedido_opcion_data():
    """
    Fixture que proporciona datos de muestra para una opción de pedido.
    """
    return {
        "id": str(ULID()),
        "id_pedido_producto": str(ULID()),
        "id_producto_opcion": str(ULID()),
        "precio_adicional": Decimal("5.00"),
        "fecha_creacion": datetime.now(),
        "creado_por": str(ULID()),
    }


@pytest.mark.asyncio
async def test_create_pedido_opcion_success(
    pedido_opcion_service,
    mock_repository,
    mock_pedido_producto_repository,
    mock_producto_opcion_repository,
    sample_pedido_opcion_data,
):
    """
    Prueba la creación exitosa de una opción de pedido.

    PRECONDICIONES:
        - El servicio y repositorios mock deben estar configurados.

    PROCESO:
        - Configura los mocks para simular una creación exitosa.
        - Llama al método create_pedido_opcion con datos válidos.
        - Verifica el resultado y las llamadas a los mocks.

    POSTCONDICIONES:
        - El servicio debe crear la opción de pedido correctamente.
        - Los repositorios deben ser llamados con los parámetros correctos.
    """
    # Arrange
    pedido_opcion_create = PedidoOpcionCreate(
        id_pedido_producto=sample_pedido_opcion_data["id_pedido_producto"],
        id_producto_opcion=sample_pedido_opcion_data["id_producto_opcion"],
        precio_adicional=sample_pedido_opcion_data["precio_adicional"],
    )

    # Mock de pedido_producto existente
    mock_pedido_producto = PedidoProductoModel(id=sample_pedido_opcion_data["id_pedido_producto"])
    mock_pedido_producto_repository.get_by_id.return_value = mock_pedido_producto

    # Mock de producto_opcion existente
    mock_producto_opcion = ProductoOpcionModel(id=sample_pedido_opcion_data["id_producto_opcion"])
    mock_producto_opcion_repository.get_by_id.return_value = mock_producto_opcion

    # Mock de creación exitosa
    mock_repository.create.return_value = PedidoOpcionModel(**sample_pedido_opcion_data)

    # Act
    result = await pedido_opcion_service.create_pedido_opcion(pedido_opcion_create)

    # Assert
    assert result.id == sample_pedido_opcion_data["id"]
    assert result.id_pedido_producto == sample_pedido_opcion_data["id_pedido_producto"]
    assert result.id_producto_opcion == sample_pedido_opcion_data["id_producto_opcion"]
    mock_pedido_producto_repository.get_by_id.assert_called_once()
    mock_producto_opcion_repository.get_by_id.assert_called_once()
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_pedido_opcion_invalid_pedido_producto(
    pedido_opcion_service,
    mock_pedido_producto_repository,
    sample_pedido_opcion_data,
):
    """
    Prueba el manejo de errores al crear con pedido_producto inexistente.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Configura el mock para simular que el pedido_producto no existe.
        - Llama al método create_pedido_opcion.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionValidationError.
    """
    # Arrange
    pedido_opcion_create = PedidoOpcionCreate(
        id_pedido_producto=sample_pedido_opcion_data["id_pedido_producto"],
        id_producto_opcion=sample_pedido_opcion_data["id_producto_opcion"],
        precio_adicional=sample_pedido_opcion_data["precio_adicional"],
    )

    mock_pedido_producto_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionValidationError) as excinfo:
        await pedido_opcion_service.create_pedido_opcion(pedido_opcion_create)

    assert "No existe el item de pedido" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_pedido_opcion_invalid_producto_opcion(
    pedido_opcion_service,
    mock_pedido_producto_repository,
    mock_producto_opcion_repository,
    sample_pedido_opcion_data,
):
    """
    Prueba el manejo de errores al crear con producto_opcion inexistente.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Configura el mock para simular que el producto_opcion no existe.
        - Llama al método create_pedido_opcion.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionValidationError.
    """
    # Arrange
    pedido_opcion_create = PedidoOpcionCreate(
        id_pedido_producto=sample_pedido_opcion_data["id_pedido_producto"],
        id_producto_opcion=sample_pedido_opcion_data["id_producto_opcion"],
        precio_adicional=sample_pedido_opcion_data["precio_adicional"],
    )

    mock_pedido_producto = PedidoProductoModel(id=sample_pedido_opcion_data["id_pedido_producto"])
    mock_pedido_producto_repository.get_by_id.return_value = mock_pedido_producto
    mock_producto_opcion_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionValidationError) as excinfo:
        await pedido_opcion_service.create_pedido_opcion(pedido_opcion_create)

    assert "No existe la opción de producto" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_pedido_opcion_by_id_success(
    pedido_opcion_service, mock_repository, sample_pedido_opcion_data
):
    """
    Prueba la obtención exitosa de una opción de pedido por su ID.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia de la opción.
        - Llama al método get_pedido_opcion_by_id con un ID válido.
        - Verifica el resultado y las llamadas al mock.

    POSTCONDICIONES:
        - El servicio debe retornar la opción de pedido correctamente.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion_data["id"]
    mock_repository.get_by_id.return_value = PedidoOpcionModel(**sample_pedido_opcion_data)

    # Act
    result = await pedido_opcion_service.get_pedido_opcion_by_id(pedido_opcion_id)

    # Assert
    assert result.id == pedido_opcion_id
    assert result.id_pedido_producto == sample_pedido_opcion_data["id_pedido_producto"]
    mock_repository.get_by_id.assert_called_once_with(pedido_opcion_id)


@pytest.mark.asyncio
async def test_get_pedido_opcion_by_id_not_found(pedido_opcion_service, mock_repository):
    """
    Prueba el manejo de errores al intentar obtener una opción que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Llama al método get_pedido_opcion_by_id con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionNotFoundError.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionNotFoundError) as excinfo:
        await pedido_opcion_service.get_pedido_opcion_by_id(pedido_opcion_id)

    assert f"No se encontró la opción de pedido con ID {pedido_opcion_id}" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_opciones_by_pedido_producto_success(
    pedido_opcion_service,
    mock_repository,
    mock_pedido_producto_repository,
    sample_pedido_opcion_data,
):
    """
    Prueba la obtención exitosa de opciones por item de pedido.

    PRECONDICIONES:
        - El servicio y repositorios mock deben estar configurados.

    PROCESO:
        - Configura los mocks para simular opciones del item de pedido.
        - Llama al método get_opciones_by_pedido_producto.
        - Verifica el resultado.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de opciones correctamente.
    """
    # Arrange
    pedido_producto_id = sample_pedido_opcion_data["id_pedido_producto"]
    mock_pedido_producto = PedidoProductoModel(id=pedido_producto_id)
    mock_pedido_producto_repository.get_by_id.return_value = mock_pedido_producto

    opciones = [PedidoOpcionModel(**sample_pedido_opcion_data)]
    mock_repository.get_by_pedido_producto_id.return_value = opciones

    # Act
    result = await pedido_opcion_service.get_opciones_by_pedido_producto(pedido_producto_id)

    # Assert
    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == sample_pedido_opcion_data["id"]


@pytest.mark.asyncio
async def test_get_opciones_by_pedido_producto_invalid(
    pedido_opcion_service, mock_pedido_producto_repository
):
    """
    Prueba el manejo de errores al obtener opciones de item inexistente.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Configura el mock para simular que el item no existe.
        - Llama al método get_opciones_by_pedido_producto.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionValidationError.
    """
    # Arrange
    pedido_producto_id = str(ULID())
    mock_pedido_producto_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionValidationError) as excinfo:
        await pedido_opcion_service.get_opciones_by_pedido_producto(pedido_producto_id)

    assert "No existe el item de pedido" in str(excinfo.value)


@pytest.mark.asyncio
async def test_delete_pedido_opcion_success(
    pedido_opcion_service, mock_repository, sample_pedido_opcion_data
):
    """
    Prueba la eliminación exitosa de una opción de pedido.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia y eliminación exitosa.
        - Llama al método delete_pedido_opcion con un ID válido.
        - Verifica el resultado.

    POSTCONDICIONES:
        - El servicio debe eliminar la opción correctamente.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion_data["id"]
    mock_repository.get_by_id.return_value = PedidoOpcionModel(**sample_pedido_opcion_data)
    mock_repository.delete.return_value = True

    # Act
    result = await pedido_opcion_service.delete_pedido_opcion(pedido_opcion_id)

    # Assert
    assert result is True
    mock_repository.get_by_id.assert_called_once_with(pedido_opcion_id)
    mock_repository.delete.assert_called_once_with(pedido_opcion_id)


@pytest.mark.asyncio
async def test_delete_pedido_opcion_not_found(pedido_opcion_service, mock_repository):
    """
    Prueba el manejo de errores al intentar eliminar una opción que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Llama al método delete_pedido_opcion con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionNotFoundError.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionNotFoundError) as excinfo:
        await pedido_opcion_service.delete_pedido_opcion(pedido_opcion_id)

    assert f"No se encontró la opción de pedido con ID {pedido_opcion_id}" in str(excinfo.value)
    mock_repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_pedido_opciones_success(
    pedido_opcion_service, mock_repository, sample_pedido_opcion_data
):
    """
    Prueba la obtención exitosa de una lista paginada de opciones de pedidos.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular una lista de opciones.
        - Llama al método get_pedido_opciones con parámetros válidos.
        - Verifica el resultado.

    POSTCONDICIONES:
        - El servicio debe retornar la lista de opciones correctamente.
    """
    # Arrange
    opciones = [
        PedidoOpcionModel(**sample_pedido_opcion_data),
        PedidoOpcionModel(
            id=str(ULID()),
            id_pedido_producto=str(ULID()),
            id_producto_opcion=str(ULID()),
            precio_adicional=Decimal("3.00"),
        ),
    ]
    mock_repository.get_all.return_value = (opciones, len(opciones))

    # Act
    result = await pedido_opcion_service.get_pedido_opciones(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    mock_repository.get_all.assert_called_once_with(0, 10)


@pytest.mark.asyncio
async def test_get_pedido_opciones_validation_error(pedido_opcion_service):
    """
    Prueba el manejo de errores al proporcionar parámetros inválidos.

    PRECONDICIONES:
        - El servicio debe estar configurado.

    PROCESO:
        - Llama al método get_pedido_opciones con parámetros inválidos.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionValidationError.
    """
    # Act & Assert - Parámetro skip negativo
    with pytest.raises(PedidoOpcionValidationError) as excinfo:
        await pedido_opcion_service.get_pedido_opciones(skip=-1, limit=10)
    assert "El parámetro 'skip' debe ser mayor o igual a cero" in str(excinfo.value)

    # Act & Assert - Parámetro limit no positivo
    with pytest.raises(PedidoOpcionValidationError) as excinfo:
        await pedido_opcion_service.get_pedido_opciones(skip=0, limit=0)
    assert "El parámetro 'limit' debe ser mayor a cero" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_pedido_opcion_success(
    pedido_opcion_service, mock_repository, sample_pedido_opcion_data
):
    """
    Prueba la actualización exitosa de una opción de pedido.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la actualización exitosa.
        - Llama al método update_pedido_opcion con datos válidos.
        - Verifica el resultado.

    POSTCONDICIONES:
        - El servicio debe actualizar la opción correctamente.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion_data["id"]
    update_data = PedidoOpcionUpdate(precio_adicional=Decimal("10.00"))

    updated_opcion = PedidoOpcionModel(
        **{**sample_pedido_opcion_data, "precio_adicional": Decimal("10.00")}
    )
    mock_repository.update.return_value = updated_opcion

    # Act
    result = await pedido_opcion_service.update_pedido_opcion(pedido_opcion_id, update_data)

    # Assert
    assert result.id == pedido_opcion_id
    assert result.precio_adicional == Decimal("10.00")
    mock_repository.update.assert_called_once_with(
        pedido_opcion_id, precio_adicional=Decimal("10.00")
    )


@pytest.mark.asyncio
async def test_update_pedido_opcion_not_found(pedido_opcion_service, mock_repository):
    """
    Prueba el manejo de errores al intentar actualizar una opción que no existe.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Llama al método update_pedido_opcion con un ID inexistente.
        - Verifica que se lance la excepción adecuada.

    POSTCONDICIONES:
        - El servicio debe lanzar PedidoOpcionNotFoundError.
    """
    # Arrange
    pedido_opcion_id = str(ULID())
    update_data = PedidoOpcionUpdate(precio_adicional=Decimal("10.00"))
    mock_repository.update.return_value = None

    # Act & Assert
    with pytest.raises(PedidoOpcionNotFoundError) as excinfo:
        await pedido_opcion_service.update_pedido_opcion(pedido_opcion_id, update_data)

    assert f"No se encontró la opción de pedido con ID {pedido_opcion_id}" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_pedido_opcion_no_changes(
    pedido_opcion_service, mock_repository, sample_pedido_opcion_data
):
    """
    Prueba la actualización de una opción cuando no se proporcionan cambios.

    PRECONDICIONES:
        - El servicio y repositorio mock deben estar configurados.

    PROCESO:
        - Configura el mock para simular la existencia de la opción.
        - Llama al método update_pedido_opcion sin proporcionar campos para actualizar.
        - Verifica que se recupere la opción existente sin cambios.

    POSTCONDICIONES:
        - El servicio debe retornar la opción existente sin modificaciones.
    """
    # Arrange
    pedido_opcion_id = sample_pedido_opcion_data["id"]
    update_data = PedidoOpcionUpdate()  # Sin datos para actualizar
    mock_repository.get_by_id.return_value = PedidoOpcionModel(**sample_pedido_opcion_data)

    # Act
    result = await pedido_opcion_service.update_pedido_opcion(pedido_opcion_id, update_data)

    # Assert
    assert result.id == pedido_opcion_id
    mock_repository.get_by_id.assert_called_once_with(pedido_opcion_id)
    mock_repository.update.assert_not_called()
