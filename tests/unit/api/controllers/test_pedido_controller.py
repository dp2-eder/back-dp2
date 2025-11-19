"""
Pruebas unitarias para los endpoints de pedidos.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from ulid import ULID
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.pedido_controller import router, get_database_session
from src.business_logic.pedidos.pedido_service import PedidoService
from src.business_logic.exceptions.pedido_exceptions import (
    PedidoNotFoundError,
    PedidoConflictError,
    PedidoValidationError,
    PedidoStateTransitionError,
)
from src.api.schemas.pedido_schema import PedidoResponse, PedidoList
from src.core.enums.pedido_enums import EstadoPedido

app = FastAPI()
app.include_router(router)


# Mock de sesión de base de datos para pruebas unitarias usando el fixture global
@pytest.fixture
def mock_db_session_dependency(async_mock_db_session, cleanup_app):
    """
    Fixture que reemplaza la dependencia de la sesión de base de datos
    con un mock global de conftest.py para evitar conexiones reales durante pruebas unitarias

    PRECONDICIONES:
        - El fixture async_mock_db_session debe estar disponible en conftest.py
        - El fixture cleanup_app debe estar disponible para limpiar dependencias

    PROCESO:
        - Sobrescribe la dependencia get_database_session en la app de FastAPI
        - Configura una función asíncrona que devuelve el mock de sesión

    POSTCONDICIONES:
        - Las llamadas a get_database_session devolverán un mock en lugar de una conexión real
        - Las pruebas pueden ejecutarse sin depender de una base de datos real
    """

    async def override_get_db():
        yield async_mock_db_session

    app.dependency_overrides[get_database_session] = override_get_db


@pytest.fixture
def mock_pedido_service():
    """
    Fixture que proporciona un mock del servicio de pedidos.

    PRECONDICIONES:
        - La clase PedidoService debe estar importada correctamente

    PROCESO:
        - Crea un patch del servicio de pedidos
        - Configura el servicio mock con métodos asíncronos

    POSTCONDICIONES:
        - Devuelve una instancia mock de PedidoService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.pedido_controller.PedidoService") as mock:
        service_instance = AsyncMock(spec=PedidoService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_pedido_id():
    """
    Fixture que proporciona un ID de pedido de muestra.

    PRECONDICIONES:
        - La biblioteca ulid debe estar importada correctamente

    PROCESO:
        - Genera un ULID único
        - Lo convierte a string para usarlo en las pruebas

    POSTCONDICIONES:
        - Devuelve un string con formato ULID válido para usar como ID de pedido
    """
    return str(ULID())


@pytest.fixture
def sample_pedido_data():
    """
    Fixture que proporciona datos de muestra para un pedido.

    PRECONDICIONES:
        - La biblioteca ulid debe estar importada correctamente

    PROCESO:
        - Crea un diccionario con datos ficticios de un pedido
        - Incluye id, id_mesa, numero_pedido, estado, totales, etc.

    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para un pedido
        - Los datos pueden ser usados para construir objetos PedidoModel o PedidoResponse
    """
    return {
        "id": str(ULID()),
        "id_mesa": str(ULID()),
        "id_usuario": str(ULID()),
        "numero_pedido": "20251026-M001-001",
        "estado": EstadoPedido.PENDIENTE,
        "subtotal": Decimal("100.00"),
        "impuestos": Decimal("10.00"),
        "descuentos": Decimal("5.00"),
        "total": Decimal("105.00"),
        "notas_cliente": "Sin cebolla",
        "notas_cocina": "Urgente",
        "fecha_creacion": "2025-10-26T12:00:00",
        "fecha_modificacion": "2025-10-26T12:00:00",
    }


def test_create_pedido_success(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_data
):
    """
    Prueba la creación exitosa de un pedido.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Los datos de muestra deben estar disponibles (sample_pedido_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_pedido del servicio debe haber sido llamado una vez
    """
    # Arrange
    pedido_data = {
        "id_mesa": sample_pedido_data["id_mesa"],
        "id_usuario": sample_pedido_data["id_usuario"],
        "subtotal": float(sample_pedido_data["subtotal"]),
        "total": float(sample_pedido_data["total"]),
    }
    mock_pedido_service.create_pedido.return_value = PedidoResponse(**sample_pedido_data)

    # Act
    response = test_client.post("/api/v1/pedidos", json=pedido_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["numero_pedido"] == sample_pedido_data["numero_pedido"]
    assert response.json()["id_mesa"] == sample_pedido_data["id_mesa"]
    mock_pedido_service.create_pedido.assert_awaited_once()


def test_create_pedido_conflict(test_client, mock_db_session_dependency, mock_pedido_service):
    """
    Prueba el manejo de errores al crear un pedido con conflicto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar el conflicto
        - El método create_pedido del servicio debe haber sido llamado una vez
    """
    # Arrange
    pedido_data = {
        "id_mesa": str(ULID()),
        "id_usuario": str(ULID()),
        "total": 100.00,
    }
    mock_pedido_service.create_pedido.side_effect = PedidoConflictError(
        "Error al crear el pedido"
    )

    # Act
    response = test_client.post("/api/v1/pedidos", json=pedido_data)

    # Assert
    assert response.status_code == 409
    assert "Error al crear el pedido" in response.json()["detail"]
    mock_pedido_service.create_pedido.assert_awaited_once()


def test_get_pedido_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_service,
    sample_pedido_id,
    sample_pedido_data,
):
    """
    Prueba la obtención exitosa de un pedido por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)
        - Los datos de muestra deben estar disponibles (sample_pedido_data)

    PROCESO:
        - Configura el mock para simular la existencia de un pedido.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_pedido_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_pedido_service.get_pedido_by_id.return_value = PedidoResponse(**sample_pedido_data)

    # Act
    response = test_client.get(f"/api/v1/pedidos/{sample_pedido_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_pedido_data["id"]
    assert response.json()["numero_pedido"] == sample_pedido_data["numero_pedido"]
    mock_pedido_service.get_pedido_by_id.assert_awaited_once()


def test_get_pedido_not_found(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_id
):
    """
    Prueba el manejo de errores al buscar un pedido que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)

    PROCESO:
        - Configura el mock para simular que el pedido no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el pedido
        - El método get_pedido_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_pedido_service.get_pedido_by_id.side_effect = PedidoNotFoundError(
        f"No se encontró el pedido con ID {sample_pedido_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/pedidos/{sample_pedido_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el pedido con ID {sample_pedido_id}" in response.json()["detail"]
    mock_pedido_service.get_pedido_by_id.assert_awaited_once()


def test_get_pedido_by_numero_success(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_data
):
    """
    Prueba la obtención exitosa de un pedido por su número.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Los datos de muestra deben estar disponibles (sample_pedido_data)

    PROCESO:
        - Configura el mock para simular la existencia de un pedido.
        - Realiza una solicitud GET al endpoint con número de pedido.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_pedido_by_numero del servicio debe haber sido llamado una vez
    """
    # Arrange
    numero_pedido = sample_pedido_data["numero_pedido"]
    mock_pedido_service.get_pedido_by_numero.return_value = PedidoResponse(**sample_pedido_data)

    # Act
    response = test_client.get(f"/api/v1/pedidos/numero/{numero_pedido}")

    # Assert
    assert response.status_code == 200
    assert response.json()["numero_pedido"] == numero_pedido
    mock_pedido_service.get_pedido_by_numero.assert_awaited_once()


def test_list_pedidos_success(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_data
):
    """
    Prueba la obtención exitosa de una lista de pedidos.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Los datos de muestra deben estar disponibles (sample_pedido_data)

    PROCESO:
        - Configura el mock para simular una lista de pedidos.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de pedidos y el total
        - El método get_pedidos del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    pedido_summary = {
        "id": sample_pedido_data["id"],
        "numero_pedido": sample_pedido_data["numero_pedido"],
        "id_mesa": sample_pedido_data["id_mesa"],
        "estado": sample_pedido_data["estado"],
        "total": sample_pedido_data["total"],
        "fecha_creacion": sample_pedido_data["fecha_creacion"],
    }
    pedido_list = {"items": [pedido_summary, pedido_summary], "total": 2}
    mock_pedido_service.get_pedidos.return_value = PedidoList(**pedido_list)

    # Act
    response = test_client.get("/api/v1/pedidos?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_pedido_service.get_pedidos.assert_awaited_once_with(0, 10, None, None, None)


def test_update_pedido_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_service,
    sample_pedido_id,
    sample_pedido_data,
):
    """
    Prueba la actualización exitosa de un pedido.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)
        - Los datos de muestra deben estar disponibles (sample_pedido_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_pedido del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"total": 150.00}
    updated_data = {**sample_pedido_data, "total": Decimal("150.00")}
    mock_pedido_service.update_pedido.return_value = PedidoResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/pedidos/{sample_pedido_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert float(response.json()["total"]) == 150.00
    mock_pedido_service.update_pedido.assert_awaited_once()


def test_cambiar_estado_pedido_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_service,
    sample_pedido_id,
    sample_pedido_data,
):
    """
    Prueba el cambio exitoso de estado de un pedido.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)

    PROCESO:
        - Configura el mock para simular un cambio de estado exitoso.
        - Realiza una solicitud PATCH al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - El estado del pedido debe haber cambiado
        - El método cambiar_estado del servicio debe haber sido llamado una vez
    """
    # Arrange
    estado_data = {"estado": "confirmado"}
    updated_data = {**sample_pedido_data, "estado": EstadoPedido.CONFIRMADO}
    mock_pedido_service.cambiar_estado.return_value = PedidoResponse(**updated_data)

    # Act
    response = test_client.patch(f"/api/v1/pedidos/{sample_pedido_id}/estado", json=estado_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["estado"] == "confirmado"
    mock_pedido_service.cambiar_estado.assert_awaited_once()


def test_cambiar_estado_invalid_transition(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_id
):
    """
    Prueba el manejo de errores al intentar una transición de estado inválida.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)

    PROCESO:
        - Configura el mock para simular un error de transición inválida.
        - Realiza una solicitud PATCH al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 400 (Bad Request)
        - El mensaje de error debe indicar la transición inválida
    """
    # Arrange
    estado_data = {"estado": "pendiente"}
    mock_pedido_service.cambiar_estado.side_effect = PedidoStateTransitionError(
        "Transición de estado inválida"
    )

    # Act
    response = test_client.patch(f"/api/v1/pedidos/{sample_pedido_id}/estado", json=estado_data)

    # Assert
    assert response.status_code == 400
    assert "Transición de estado inválida" in response.json()["detail"]


def test_delete_pedido_success(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_id
):
    """
    Prueba la eliminación exitosa de un pedido.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_pedido del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_pedido_service.delete_pedido.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/pedidos/{sample_pedido_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_pedido_service.delete_pedido.assert_awaited_once_with(sample_pedido_id)


def test_delete_pedido_not_found(
    test_client, mock_db_session_dependency, mock_pedido_service, sample_pedido_id
):
    """
    Prueba el manejo de errores al eliminar un pedido que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de pedidos debe estar mockeado (mock_pedido_service)
        - Se debe tener un ID de pedido válido (sample_pedido_id)

    PROCESO:
        - Configura el mock para simular que el pedido no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el pedido
        - El método delete_pedido del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_pedido_service.delete_pedido.side_effect = PedidoNotFoundError(
        f"No se encontró el pedido con ID {sample_pedido_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/pedidos/{sample_pedido_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el pedido con ID {sample_pedido_id}" in response.json()["detail"]
    mock_pedido_service.delete_pedido.assert_awaited_once()
