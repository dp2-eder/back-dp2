"""
Pruebas unitarias para los endpoints de items de pedidos (pedido_producto).
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from ulid import ULID
from fastapi import FastAPI

from src.api.controllers.pedido_producto_controller import router, get_database_session
from src.business_logic.pedidos.pedido_producto_service import PedidoProductoService
from src.business_logic.exceptions.pedido_producto_exceptions import (
    PedidoProductoNotFoundError,
    PedidoProductoConflictError,
    PedidoProductoValidationError,
)
from src.api.schemas.pedido_producto_schema import PedidoProductoResponse, PedidoProductoList

app = FastAPI()
app.include_router(router)


# Mock de sesión de base de datos
@pytest.fixture
def mock_db_session_dependency(async_mock_db_session, cleanup_app):
    """
    Fixture que reemplaza la dependencia de la sesión de base de datos.
    """

    async def override_get_db():
        yield async_mock_db_session

    app.dependency_overrides[get_database_session] = override_get_db


@pytest.fixture
def mock_pedido_producto_service():
    """
    Fixture que proporciona un mock del servicio de pedido_producto.
    """
    with patch("src.api.controllers.pedido_producto_controller.PedidoProductoService") as mock:
        service_instance = AsyncMock(spec=PedidoProductoService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_item_id():
    """Fixture que proporciona un ID de item de muestra."""
    return str(ULID())


@pytest.fixture
def sample_item_data():
    """Fixture que proporciona datos de muestra para un item."""
    return {
        "id": str(ULID()),
        "id_pedido": str(ULID()),
        "id_producto": str(ULID()),
        "cantidad": 2,
        "precio_unitario": Decimal("50.00"),
        "precio_opciones": Decimal("5.00"),
        "subtotal": Decimal("110.00"),
        "notas_personalizacion": "Sin cebolla",
        "fecha_creacion": "2025-10-26T12:00:00",
        "fecha_modificacion": "2025-10-26T12:00:00",
    }


def test_create_pedido_producto_success(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_data
):
    """Prueba la creación exitosa de un item de pedido."""
    # Arrange
    item_data = {
        "id_pedido": sample_item_data["id_pedido"],
        "id_producto": sample_item_data["id_producto"],
        "cantidad": 2,
        "precio_unitario": 50.00,
        "precio_opciones": 5.00,
    }
    mock_pedido_producto_service.create_pedido_producto.return_value = PedidoProductoResponse(**sample_item_data)

    # Act
    response = test_client.post("/api/v1/pedidos-productos", json=item_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["cantidad"] == 2
    assert response.json()["id_pedido"] == sample_item_data["id_pedido"]
    mock_pedido_producto_service.create_pedido_producto.assert_awaited_once()


def test_create_pedido_producto_validation_error(
    test_client, mock_db_session_dependency, mock_pedido_producto_service
):
    """Prueba el manejo de errores de validación al crear un item."""
    # Arrange
    item_data = {
        "id_pedido": str(ULID()),
        "id_producto": str(ULID()),
        "cantidad": 1,
        "precio_unitario": 10.00,
    }
    mock_pedido_producto_service.create_pedido_producto.side_effect = PedidoProductoValidationError(
        "El pedido no existe"
    )

    # Act
    response = test_client.post("/api/v1/pedidos-productos", json=item_data)

    # Assert
    assert response.status_code == 400
    assert "El pedido no existe" in response.json()["detail"]


def test_get_pedido_producto_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_producto_service,
    sample_item_id,
    sample_item_data,
):
    """Prueba la obtención exitosa de un item por su ID."""
    # Arrange
    mock_pedido_producto_service.get_pedido_producto_by_id.return_value = PedidoProductoResponse(**sample_item_data)

    # Act
    response = test_client.get(f"/api/v1/pedidos-productos/{sample_item_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_item_data["id"]
    assert response.json()["cantidad"] == 2
    mock_pedido_producto_service.get_pedido_producto_by_id.assert_awaited_once()


def test_get_pedido_producto_not_found(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_id
):
    """Prueba el manejo de errores al buscar un item que no existe."""
    # Arrange
    mock_pedido_producto_service.get_pedido_producto_by_id.side_effect = PedidoProductoNotFoundError(
        f"No se encontró el item con ID {sample_item_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/pedidos-productos/{sample_item_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el item con ID {sample_item_id}" in response.json()["detail"]


def test_get_items_by_pedido_success(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_data
):
    """Prueba la obtención exitosa de items de un pedido."""
    # Arrange
    pedido_id = sample_item_data["id_pedido"]
    item_summary = {
        "id": sample_item_data["id"],
        "id_pedido": sample_item_data["id_pedido"],
        "id_producto": sample_item_data["id_producto"],
        "cantidad": sample_item_data["cantidad"],
        "precio_unitario": sample_item_data["precio_unitario"],
        "precio_opciones": sample_item_data["precio_opciones"],
        "subtotal": sample_item_data["subtotal"],
    }
    item_list = {"items": [item_summary], "total": 1}
    mock_pedido_producto_service.get_productos_by_pedido.return_value = PedidoProductoList(**item_list)

    # Act
    response = test_client.get(f"/api/v1/pedidos-productos/pedido/{pedido_id}/items")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    mock_pedido_producto_service.get_productos_by_pedido.assert_awaited_once()


def test_list_pedidos_productos_success(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_data
):
    """Prueba la obtención exitosa de una lista de items."""
    # Arrange
    item_summary = {
        "id": sample_item_data["id"],
        "id_pedido": sample_item_data["id_pedido"],
        "id_producto": sample_item_data["id_producto"],
        "cantidad": sample_item_data["cantidad"],
        "precio_unitario": sample_item_data["precio_unitario"],
        "precio_opciones": sample_item_data["precio_opciones"],
        "subtotal": sample_item_data["subtotal"],
    }
    item_list = {"items": [item_summary, item_summary], "total": 2}
    mock_pedido_producto_service.get_pedidos_productos.return_value = PedidoProductoList(**item_list)

    # Act
    response = test_client.get("/api/v1/pedidos-productos?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_pedido_producto_service.get_pedidos_productos.assert_awaited_once_with(0, 10, None, None)


def test_update_pedido_producto_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_producto_service,
    sample_item_id,
    sample_item_data,
):
    """Prueba la actualización exitosa de un item."""
    # Arrange
    update_data = {"cantidad": 5}
    updated_data = {**sample_item_data, "cantidad": 5, "subtotal": Decimal("275.00")}
    mock_pedido_producto_service.update_pedido_producto.return_value = PedidoProductoResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/pedidos-productos/{sample_item_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["cantidad"] == 5
    mock_pedido_producto_service.update_pedido_producto.assert_awaited_once()


def test_update_pedido_producto_not_found(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_id
):
    """Prueba el manejo de errores al actualizar un item que no existe."""
    # Arrange
    update_data = {"cantidad": 5}
    mock_pedido_producto_service.update_pedido_producto.side_effect = PedidoProductoNotFoundError(
        f"No se encontró el item con ID {sample_item_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/pedidos-productos/{sample_item_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el item con ID {sample_item_id}" in response.json()["detail"]


def test_delete_pedido_producto_success(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_id
):
    """Prueba la eliminación exitosa de un item."""
    # Arrange
    mock_pedido_producto_service.delete_pedido_producto.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/pedidos-productos/{sample_item_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_pedido_producto_service.delete_pedido_producto.assert_awaited_once_with(sample_item_id)


def test_delete_pedido_producto_not_found(
    test_client, mock_db_session_dependency, mock_pedido_producto_service, sample_item_id
):
    """Prueba el manejo de errores al eliminar un item que no existe."""
    # Arrange
    mock_pedido_producto_service.delete_pedido_producto.side_effect = PedidoProductoNotFoundError(
        f"No se encontró el item con ID {sample_item_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/pedidos-productos/{sample_item_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el item con ID {sample_item_id}" in response.json()["detail"]
