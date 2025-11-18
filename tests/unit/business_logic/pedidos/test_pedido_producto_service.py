"""
Pruebas unitarias para el servicio de items de pedidos (pedido_producto).
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock
from ulid import ULID

from src.business_logic.pedidos.pedido_producto_service import PedidoProductoService
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.pedido_model import PedidoModel
from src.models.menu.producto_model import ProductoModel
from src.api.schemas.pedido_producto_schema import (
    PedidoProductoCreate,
    PedidoProductoUpdate,
)
from src.business_logic.exceptions.pedido_producto_exceptions import (
    PedidoProductoValidationError,
    PedidoProductoNotFoundError,
    PedidoProductoConflictError,
)
from src.core.enums.pedido_enums import EstadoPedido
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository(sample_item_data):
    """
    Mock del repositorio de pedido_producto con métodos async correctamente mockeados.
    """
    items = [
        PedidoProductoModel(**sample_item_data),
        PedidoProductoModel(**{**sample_item_data, "id": str(ULID()), "cantidad": 3}),
    ]

    repo = AsyncMock()
    repo.get_by_pedido_id = AsyncMock(return_value=items)
    return repo



@pytest.fixture
def mock_pedido_repository():
    """Fixture que proporciona un mock del repositorio de pedidos."""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_producto_repository():
    """Fixture que proporciona un mock del repositorio de productos."""
    repository = AsyncMock()
    return repository


@pytest.fixture
def pedido_producto_service(mock_repository, mock_pedido_repository, mock_producto_repository):
    """Fixture que proporciona una instancia del servicio con repositorios mockeados."""
    service = PedidoProductoService(AsyncMock())
    service.repository = mock_repository
    service.pedido_repository = mock_pedido_repository
    service.producto_repository = mock_producto_repository
    return service


@pytest.fixture
def sample_item_data():
    """Fixture que proporciona datos de muestra para un item de pedido."""
    return {
        "id": str(ULID()),
        "id_pedido": str(ULID()),
        "id_producto": str(ULID()),
        "cantidad": 2,
        "precio_unitario": Decimal("50.00"),
        "precio_opciones": Decimal("5.00"),
        "subtotal": Decimal("110.00"),
        "notas_personalizacion": "Sin cebolla",
        "fecha_creacion": datetime.now(),
        "fecha_modificacion": datetime.now(),
    }


@pytest.fixture
def sample_pedido_data():
    """Fixture que proporciona datos de muestra para un pedido."""
    return {
        "id": str(ULID()),
        "id_mesa": str(ULID()),
        "numero_pedido": "20251026-M001-001",
        "estado": EstadoPedido.PENDIENTE,
        "total": Decimal("100.00"),
    }


@pytest.fixture
def sample_producto_data():
    """Fixture que proporciona datos de muestra para un producto."""
    return {
        "id": str(ULID()),
        "id_categoria": str(ULID()),
        "nombre": "Ceviche",
        "precio_base": Decimal("50.00"),
        "disponible": True,
    }


@pytest.mark.asyncio
async def test_create_pedido_producto_success(
    pedido_producto_service,
    mock_repository,
    mock_pedido_repository,
    mock_producto_repository,
    sample_item_data,
    sample_pedido_data,
    sample_producto_data,
):
    """
    Prueba la creación exitosa de un item de pedido.
    """
    # Arrange
    item_create = PedidoProductoCreate(
        id_pedido=sample_item_data["id_pedido"],
        id_producto=sample_item_data["id_producto"],
        cantidad=sample_item_data["cantidad"],
        precio_unitario=sample_item_data["precio_unitario"],
        precio_opciones=sample_item_data["precio_opciones"],
    )

    # Mock pedido y producto existen
    mock_pedido_repository.get_by_id.return_value = PedidoModel(**sample_pedido_data)
    mock_producto_repository.get_by_id.return_value = ProductoModel(**sample_producto_data)

    # Mock create
    created_item = PedidoProductoModel(**sample_item_data)
    mock_repository.create.return_value = created_item

    # Act
    result = await pedido_producto_service.create_pedido_producto(item_create)

    # Assert
    assert result.id == sample_item_data["id"]
    assert result.cantidad == 2
    assert result.subtotal == Decimal("110.00")
    mock_pedido_repository.get_by_id.assert_called_once()
    mock_producto_repository.get_by_id.assert_called_once()
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_pedido_producto_pedido_not_found(
    pedido_producto_service, mock_pedido_repository
):
    """
    Prueba el manejo de errores cuando el pedido no existe.
    """
    # Arrange
    item_create = PedidoProductoCreate(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
    )
    mock_pedido_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoProductoValidationError) as excinfo:
        await pedido_producto_service.create_pedido_producto(item_create)

    assert "No se encontró el pedido" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_pedido_producto_producto_not_found(
    pedido_producto_service,
    mock_pedido_repository,
    mock_producto_repository,
    sample_pedido_data,
):
    """
    Prueba el manejo de errores cuando el producto no existe.
    """
    # Arrange
    item_create = PedidoProductoCreate(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
    )
    mock_pedido_repository.get_by_id.return_value = PedidoModel(**sample_pedido_data)
    mock_producto_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoProductoValidationError) as excinfo:
        await pedido_producto_service.create_pedido_producto(item_create)

    assert "No se encontró el producto" in str(excinfo.value)


@pytest.mark.asyncio
async def test_create_pedido_producto_producto_not_disponible(
    pedido_producto_service,
    mock_pedido_repository,
    mock_producto_repository,
    sample_pedido_data,
    sample_producto_data,
):
    """
    Prueba el manejo de errores cuando el producto no está disponible.
    """
    # Arrange
    item_create = PedidoProductoCreate(
        id_pedido=str(ULID()),
        id_producto=str(ULID()),
        cantidad=1,
        precio_unitario=Decimal("10.00"),
    )
    mock_pedido_repository.get_by_id.return_value = PedidoModel(**sample_pedido_data)

    # Producto no disponible
    producto_no_disponible = ProductoModel(**{**sample_producto_data, "disponible": False})
    mock_producto_repository.get_by_id.return_value = producto_no_disponible

    # Act & Assert
    with pytest.raises(PedidoProductoValidationError) as excinfo:
        await pedido_producto_service.create_pedido_producto(item_create)

    assert "no está disponible" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_pedido_producto_by_id_success(
    pedido_producto_service, mock_repository, sample_item_data
):
    """
    Prueba la obtención exitosa de un item por su ID.
    """
    # Arrange
    item_id = sample_item_data["id"]
    mock_repository.get_by_id.return_value = PedidoProductoModel(**sample_item_data)

    # Act
    result = await pedido_producto_service.get_pedido_producto_by_id(item_id)

    # Assert
    assert result.id == item_id
    assert result.cantidad == 2
    mock_repository.get_by_id.assert_called_once_with(item_id)


@pytest.mark.asyncio
async def test_get_pedido_producto_by_id_not_found(
    pedido_producto_service, mock_repository
):
    """
    Prueba el manejo de errores al intentar obtener un item que no existe.
    """
    # Arrange
    item_id = str(ULID())
    mock_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(PedidoProductoNotFoundError) as excinfo:
        await pedido_producto_service.get_pedido_producto_by_id(item_id)

    assert f"No se encontró el item de pedido con ID {item_id}" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_productos_by_pedido_success(
    pedido_producto_service,
    mock_repository,
    mock_pedido_repository,
    sample_item_data,
    sample_pedido_data,
):
    """
    Prueba la obtención exitosa de items de un pedido.
    """
    # Arrange
    pedido_id = sample_pedido_data["id"]
    items = [
        PedidoProductoModel(**sample_item_data),
        PedidoProductoModel(
            **{**sample_item_data, "id": str(ULID()), "cantidad": 3}
        ),
    ]
    mock_pedido_repository.get_by_id.return_value = PedidoModel(**sample_pedido_data)
    mock_repository.get_by_pedido_id = AsyncMock(return_value=items)


    # Act
    result = await pedido_producto_service.get_productos_by_pedido(pedido_id)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    mock_pedido_repository.get_by_id.assert_called_once()
    mock_repository.get_by_pedido_id.assert_called_once_with(pedido_id)


@pytest.mark.asyncio
async def test_delete_pedido_producto_success(
    pedido_producto_service, mock_repository, sample_item_data
):
    """
    Prueba la eliminación exitosa de un item.
    """
    # Arrange
    item_id = sample_item_data["id"]
    mock_repository.get_by_id.return_value = PedidoProductoModel(**sample_item_data)
    mock_repository.delete.return_value = True

    # Act
    result = await pedido_producto_service.delete_pedido_producto(item_id)

    # Assert
    assert result is True
    mock_repository.get_by_id.assert_called_once_with(item_id)
    mock_repository.delete.assert_called_once_with(item_id)


@pytest.mark.asyncio
async def test_update_pedido_producto_success(
    pedido_producto_service, mock_repository, sample_item_data
):
    """
    Prueba la actualización exitosa de un item.
    """
    # Arrange
    item_id = sample_item_data["id"]
    item_actual = PedidoProductoModel(**sample_item_data)
    mock_repository.get_by_id.return_value = item_actual

    update_data = PedidoProductoUpdate(cantidad=5)

    updated_item = PedidoProductoModel(
        **{**sample_item_data, "cantidad": 5, "subtotal": Decimal("275.00")}
    )
    mock_repository.update.return_value = updated_item

    # Act
    result = await pedido_producto_service.update_pedido_producto(item_id, update_data)

    # Assert
    assert result.cantidad == 5
    # Verificar que se recalculó el subtotal: 5 * (50.00 + 5.00) = 275.00
    mock_repository.update.assert_called_once()
    call_kwargs = mock_repository.update.call_args.kwargs
    assert "subtotal" in call_kwargs
    assert call_kwargs["subtotal"] == Decimal("275.00")


@pytest.mark.asyncio
async def test_update_pedido_producto_recalcula_subtotal(
    pedido_producto_service, mock_repository, sample_item_data
):
    """
    Prueba que el subtotal se recalcula al actualizar cantidad o precios.
    """
    # Arrange
    item_id = sample_item_data["id"]
    item_actual = PedidoProductoModel(**sample_item_data)
    mock_repository.get_by_id.return_value = item_actual

    # Actualizar precio_unitario
    update_data = PedidoProductoUpdate(precio_unitario=Decimal("60.00"))

    updated_item = PedidoProductoModel(
        **{**sample_item_data, "precio_unitario": Decimal("60.00"), "subtotal": Decimal("130.00")}
    )
    mock_repository.update.return_value = updated_item

    # Act
    result = await pedido_producto_service.update_pedido_producto(item_id, update_data)

    # Assert
    # Verificar que se recalculó: 2 * (60.00 + 5.00) = 130.00
    mock_repository.update.assert_called_once()
    call_kwargs = mock_repository.update.call_args.kwargs
    assert "subtotal" in call_kwargs
    assert call_kwargs["subtotal"] == Decimal("130.00")


@pytest.mark.asyncio
async def test_get_pedidos_productos_success(
    pedido_producto_service, mock_repository, sample_item_data
):
    """
    Prueba la obtención exitosa de una lista paginada de items.
    """
    # Arrange
    items = [
        PedidoProductoModel(**sample_item_data),
        PedidoProductoModel(**{**sample_item_data, "id": str(ULID())}),
    ]
    mock_repository.get_all.return_value = (items, len(items))

    # Act
    result = await pedido_producto_service.get_pedidos_productos(skip=0, limit=10)

    # Assert
    assert result.total == 2
    assert len(result.items) == 2
    mock_repository.get_all.assert_called_once_with(0, 10, None, None)
