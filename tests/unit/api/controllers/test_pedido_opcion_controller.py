"""
Pruebas unitarias para los endpoints de opciones de pedidos.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.pedido_opcion_controller import router, get_database_session
from src.business_logic.pedidos.pedido_opcion_service import PedidoOpcionService
from src.business_logic.exceptions.pedido_opcion_exceptions import (
    PedidoOpcionNotFoundError,
    PedidoOpcionConflictError,
    PedidoOpcionValidationError,
)
from src.api.schemas.pedido_opcion_schema import PedidoOpcionResponse, PedidoOpcionList

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
def mock_pedido_opcion_service():
    """
    Fixture que proporciona un mock del servicio de opciones de pedidos.

    PRECONDICIONES:
        - La clase PedidoOpcionService debe estar importada correctamente

    PROCESO:
        - Crea un patch del servicio de opciones de pedidos
        - Configura el servicio mock con métodos asíncronos

    POSTCONDICIONES:
        - Devuelve una instancia mock de PedidoOpcionService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.pedido_opcion_controller.PedidoOpcionService") as mock:
        service_instance = AsyncMock(spec=PedidoOpcionService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_pedido_opcion_id():
    """
    Fixture que proporciona un ID de opción de pedido de muestra.

    PRECONDICIONES:
        - La biblioteca ulid debe estar importada correctamente

    PROCESO:
        - Genera un ULID único
        - Lo convierte a string para usarlo en las pruebas

    POSTCONDICIONES:
        - Devuelve un string con formato ULID válido para usar como ID
    """
    return str(ULID())


@pytest.fixture
def sample_pedido_opcion_data():
    """
    Fixture que proporciona datos de muestra para una opción de pedido.

    PRECONDICIONES:
        - Las bibliotecas necesarias deben estar importadas correctamente

    PROCESO:
        - Crea un diccionario con datos ficticios de una opción de pedido
        - Incluye id, foreign keys, precio y fechas

    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios
    """
    return {
        "id": str(ULID()),
        "id_pedido_producto": str(ULID()),
        "id_producto_opcion": str(ULID()),
        "precio_adicional": Decimal("5.00"),
        "fecha_creacion": "2025-10-26T12:00:00",
        "creado_por": str(ULID()),
    }


def test_create_pedido_opcion_success(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_data
):
    """
    Prueba la creación exitosa de una opción de pedido.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio debe estar mockeado (mock_pedido_opcion_service)
        - Los datos de muestra deben estar disponibles

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_pedido_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    opcion_data = {
        "id_pedido_producto": sample_pedido_opcion_data["id_pedido_producto"],
        "id_producto_opcion": sample_pedido_opcion_data["id_producto_opcion"],
        "precio_adicional": str(sample_pedido_opcion_data["precio_adicional"]),
    }
    mock_pedido_opcion_service.create_pedido_opcion.return_value = PedidoOpcionResponse(
        **sample_pedido_opcion_data
    )

    # Act
    response = test_client.post("/api/v1/pedido-opciones", json=opcion_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["id_pedido_producto"] == sample_pedido_opcion_data["id_pedido_producto"]
    assert response.json()["id_producto_opcion"] == sample_pedido_opcion_data["id_producto_opcion"]
    mock_pedido_opcion_service.create_pedido_opcion.assert_awaited_once()


def test_create_pedido_opcion_validation_error(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service
):
    """
    Prueba el manejo de errores de validación al crear una opción.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular un error de validación.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 400 (Bad Request)
        - El mensaje de error debe indicar el problema de validación
    """
    # Arrange
    opcion_data = {
        "id_pedido_producto": str(ULID()),
        "id_producto_opcion": str(ULID()),
        "precio_adicional": "5.00",
    }
    mock_pedido_opcion_service.create_pedido_opcion.side_effect = PedidoOpcionValidationError(
        "No existe el item de pedido"
    )

    # Act
    response = test_client.post("/api/v1/pedido-opciones", json=opcion_data)

    # Assert
    assert response.status_code == 400
    assert "No existe el item de pedido" in response.json()["detail"]


def test_create_pedido_opcion_conflict(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service
):
    """
    Prueba el manejo de errores de conflicto al crear una opción.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
    """
    # Arrange
    opcion_data = {
        "id_pedido_producto": str(ULID()),
        "id_producto_opcion": str(ULID()),
        "precio_adicional": "5.00",
    }
    mock_pedido_opcion_service.create_pedido_opcion.side_effect = PedidoOpcionConflictError(
        "Error al crear la opción de pedido"
    )

    # Act
    response = test_client.post("/api/v1/pedido-opciones", json=opcion_data)

    # Assert
    assert response.status_code == 409
    assert "Error al crear" in response.json()["detail"]


def test_get_pedido_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_opcion_service,
    sample_pedido_opcion_id,
    sample_pedido_opcion_data,
):
    """
    Prueba la obtención exitosa de una opción de pedido por su ID.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado
        - Se debe tener un ID válido

    PROCESO:
        - Configura el mock para simular la existencia de la opción.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
    """
    # Arrange
    mock_pedido_opcion_service.get_pedido_opcion_by_id.return_value = PedidoOpcionResponse(
        **sample_pedido_opcion_data
    )

    # Act
    response = test_client.get(f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_pedido_opcion_data["id"]
    mock_pedido_opcion_service.get_pedido_opcion_by_id.assert_awaited_once()


def test_get_pedido_opcion_not_found(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_id
):
    """
    Prueba el manejo de errores al buscar una opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
    """
    # Arrange
    mock_pedido_opcion_service.get_pedido_opcion_by_id.side_effect = PedidoOpcionNotFoundError(
        f"No se encontró la opción de pedido con ID {sample_pedido_opcion_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert "No se encontró" in response.json()["detail"]


def test_get_opciones_by_pedido_producto_success(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_data
):
    """
    Prueba la obtención exitosa de opciones por item de pedido.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular opciones del item.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de opciones
    """
    # Arrange
    pedido_producto_id = sample_pedido_opcion_data["id_pedido_producto"]
    opcion_summary = {
        "id": sample_pedido_opcion_data["id"],
        "id_pedido_producto": sample_pedido_opcion_data["id_pedido_producto"],
        "id_producto_opcion": sample_pedido_opcion_data["id_producto_opcion"],
        "precio_adicional": sample_pedido_opcion_data["precio_adicional"],
    }
    opcion_list = {"items": [opcion_summary], "total": 1}
    mock_pedido_opcion_service.get_opciones_by_pedido_producto.return_value = PedidoOpcionList(
        **opcion_list
    )

    # Act
    response = test_client.get(
        f"/api/v1/pedido-opciones/pedido-producto/{pedido_producto_id}/opciones"
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1


def test_list_pedido_opciones_success(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_data
):
    """
    Prueba la obtención exitosa de una lista de opciones de pedidos.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular una lista de opciones.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de opciones y el total
    """
    # Arrange
    opcion_summary = {
        "id": sample_pedido_opcion_data["id"],
        "id_pedido_producto": sample_pedido_opcion_data["id_pedido_producto"],
        "id_producto_opcion": sample_pedido_opcion_data["id_producto_opcion"],
        "precio_adicional": sample_pedido_opcion_data["precio_adicional"],
    }
    opcion_list = {"items": [opcion_summary, opcion_summary], "total": 2}
    mock_pedido_opcion_service.get_pedido_opciones.return_value = PedidoOpcionList(**opcion_list)

    # Act
    response = test_client.get("/api/v1/pedido-opciones?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_pedido_opcion_service.get_pedido_opciones.assert_awaited_once_with(0, 10)


def test_list_pedido_opciones_validation_error(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Realiza una solicitud GET al endpoint con parámetros inválidos.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 422 (Unprocessable Entity)
        - Los detalles del error deben mencionar el parámetro inválido
    """
    # Act
    response = test_client.get("/api/v1/pedido-opciones?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)


def test_update_pedido_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_pedido_opcion_service,
    sample_pedido_opcion_id,
    sample_pedido_opcion_data,
):
    """
    Prueba la actualización exitosa de una opción de pedido.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
    """
    # Arrange
    update_data = {"precio_adicional": "10.00"}
    updated_data = {**sample_pedido_opcion_data, "precio_adicional": Decimal("10.00")}
    mock_pedido_opcion_service.update_pedido_opcion.return_value = PedidoOpcionResponse(
        **updated_data
    )

    # Act
    response = test_client.put(
        f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}", json=update_data
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["precio_adicional"] == "10.00"
    mock_pedido_opcion_service.update_pedido_opcion.assert_awaited_once()


def test_update_pedido_opcion_not_found(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_id
):
    """
    Prueba el manejo de errores al actualizar una opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
    """
    # Arrange
    update_data = {"precio_adicional": "10.00"}
    mock_pedido_opcion_service.update_pedido_opcion.side_effect = PedidoOpcionNotFoundError(
        f"No se encontró la opción de pedido con ID {sample_pedido_opcion_id}"
    )

    # Act
    response = test_client.put(
        f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}", json=update_data
    )

    # Assert
    assert response.status_code == 404
    assert "No se encontró" in response.json()["detail"]


def test_update_pedido_opcion_conflict(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_id
):
    """
    Prueba el manejo de errores de conflicto al actualizar.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
    """
    # Arrange
    update_data = {"precio_adicional": "10.00"}
    mock_pedido_opcion_service.update_pedido_opcion.side_effect = PedidoOpcionConflictError(
        "Error al actualizar la opción de pedido"
    )

    # Act
    response = test_client.put(
        f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}", json=update_data
    )

    # Assert
    assert response.status_code == 409
    assert "Error al actualizar" in response.json()["detail"]


def test_delete_pedido_opcion_success(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_id
):
    """
    Prueba la eliminación exitosa de una opción de pedido.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
    """
    # Arrange
    mock_pedido_opcion_service.delete_pedido_opcion.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""
    mock_pedido_opcion_service.delete_pedido_opcion.assert_awaited_once_with(
        sample_pedido_opcion_id
    )


def test_delete_pedido_opcion_not_found(
    test_client, mock_db_session_dependency, mock_pedido_opcion_service, sample_pedido_opcion_id
):
    """
    Prueba el manejo de errores al eliminar una opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba debe estar configurado
        - El servicio debe estar mockeado

    PROCESO:
        - Configura el mock para simular que la opción no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
    """
    # Arrange
    mock_pedido_opcion_service.delete_pedido_opcion.side_effect = PedidoOpcionNotFoundError(
        f"No se encontró la opción de pedido con ID {sample_pedido_opcion_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/pedido-opciones/{sample_pedido_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert "No se encontró" in response.json()["detail"]
