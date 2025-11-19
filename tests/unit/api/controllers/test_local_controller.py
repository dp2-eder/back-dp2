"""
Pruebas unitarias para los endpoints de locales.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from datetime import date
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.local_controller import router, get_database_session
from src.business_logic.mesas.local_service import LocalService
from src.business_logic.exceptions.local_exceptions import (
    LocalNotFoundError,
    LocalConflictError,
    LocalValidationError,
)
from src.api.schemas.local_schema import LocalResponse, LocalList
from src.core.enums.local_enums import TipoLocal

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
def mock_local_service():
    """
    Fixture que proporciona un mock del servicio de locales.

    PRECONDICIONES:
        - La clase LocalService debe estar importada correctamente

    PROCESO:
        - Crea un patch del servicio de locales
        - Configura el servicio mock con métodos asíncronos

    POSTCONDICIONES:
        - Devuelve una instancia mock de LocalService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.local_controller.LocalService") as mock:
        service_instance = AsyncMock(spec=LocalService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_local_id():
    """
    Fixture que proporciona un ID de local de muestra.

    PRECONDICIONES:
        - La biblioteca ULID debe estar importada correctamente

    PROCESO:
        - Genera un ULID único
        - Lo convierte a string para usarlo en las pruebas

    POSTCONDICIONES:
        - Devuelve un string con formato ULID válido para usar como ID de local
    """
    return str(ULID())


@pytest.fixture
def sample_local_data():
    """
    Fixture que proporciona datos de muestra para un local.

    PRECONDICIONES:
        - La biblioteca ULID debe estar importada correctamente

    PROCESO:
        - Crea un diccionario con datos ficticios de un local
        - Incluye id, codigo, nombre, direccion, tipo, estado y fechas

    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para un local
        - Los datos pueden ser usados para construir objetos LocalModel o LocalResponse
    """
    return {
        "id": str(ULID()),
        "codigo": "CEV-001",
        "nombre": "La Cevichería del Centro",
        "direccion": "Av. Principal 123",
        "distrito": "Miraflores",
        "ciudad": "Lima",
        "telefono": "01-2345678",
        "email": "contacto@cevicheria.com",
        "tipo_local": TipoLocal.CENTRAL,
        "capacidad_total": 100,
        "activo": True,
        "fecha_apertura": date(2024, 1, 15),
        "fecha_creacion": "2025-10-06T12:00:00",
        "fecha_modificacion": "2025-10-06T12:00:00",
    }


def test_create_local_success(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_data
):
    """
    Prueba la creación exitosa de un local.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Los datos de muestra deben estar disponibles (sample_local_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    local_data = {
        "codigo": "CEV-001",
        "nombre": "La Cevichería del Centro",
        "direccion": "Av. Principal 123",
        "distrito": "Miraflores",
        "ciudad": "Lima",
        "telefono": "01-2345678",
        "email": "contacto@cevicheria.com",
        "tipo_local": "CENTRAL",
        "capacidad_total": 100,
        "fecha_apertura": "2024-01-15",
    }
    mock_local_service.create_local.return_value = LocalResponse(**sample_local_data)

    # Act
    response = test_client.post("/api/v1/locales", json=local_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["codigo"] == sample_local_data["codigo"]
    assert response.json()["nombre"] == sample_local_data["nombre"]
    mock_local_service.create_local.assert_awaited_once()


def test_create_local_conflict(test_client, mock_db_session_dependency, mock_local_service):
    """
    Prueba el manejo de errores al crear un local con código duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del código
        - El método create_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    local_data = {
        "codigo": "CEV-001",
        "nombre": "La Cevichería del Centro",
        "direccion": "Av. Principal 123",
        "tipo_local": "CENTRAL",
    }
    mock_local_service.create_local.side_effect = LocalConflictError(
        "Ya existe un local con el código 'CEV-001'"
    )

    # Act
    response = test_client.post("/api/v1/locales", json=local_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un local" in response.json()["detail"]
    mock_local_service.create_local.assert_awaited_once()


def test_get_local_success(
    test_client,
    mock_db_session_dependency,
    mock_local_service,
    sample_local_id,
    sample_local_data,
):
    """
    Prueba la obtención exitosa de un local por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)
        - Los datos de muestra deben estar disponibles (sample_local_data)

    PROCESO:
        - Configura el mock para simular la existencia de un local.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_local_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_local_service.get_local_by_id.return_value = LocalResponse(**sample_local_data)

    # Act
    response = test_client.get(f"/api/v1/locales/{sample_local_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_local_data["id"]
    assert response.json()["codigo"] == sample_local_data["codigo"]
    mock_local_service.get_local_by_id.assert_awaited_once()


def test_get_local_not_found(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_id
):
    """
    Prueba el manejo de errores al buscar un local que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el local
        - El método get_local_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_local_service.get_local_by_id.side_effect = LocalNotFoundError(
        f"No se encontró el local con ID {sample_local_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/locales/{sample_local_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el local con ID {sample_local_id}" in response.json()["detail"]
    mock_local_service.get_local_by_id.assert_awaited_once()


def test_get_local_by_codigo_success(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_data
):
    """
    Prueba la obtención exitosa de un local por su código.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Los datos de muestra deben estar disponibles (sample_local_data)

    PROCESO:
        - Configura el mock para simular la existencia de un local.
        - Realiza una solicitud GET al endpoint con código.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_local_by_codigo del servicio debe haber sido llamado una vez
    """
    # Arrange
    codigo = sample_local_data["codigo"]
    mock_local_service.get_local_by_codigo.return_value = LocalResponse(
        **sample_local_data
    )

    # Act
    response = test_client.get(f"/api/v1/locales/codigo/{codigo}")

    # Assert
    assert response.status_code == 200
    assert response.json()["codigo"] == codigo
    assert response.json()["nombre"] == sample_local_data["nombre"]
    mock_local_service.get_local_by_codigo.assert_awaited_once()


def test_list_locales_success(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_data
):
    """
    Prueba la obtención exitosa de una lista de locales.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Los datos de muestra deben estar disponibles (sample_local_data)

    PROCESO:
        - Configura el mock para simular una lista de locales.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de locales y el total
        - El método get_locales del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    local_summary = {
        "id": sample_local_data["id"],
        "codigo": sample_local_data["codigo"],
        "nombre": sample_local_data["nombre"],
        "tipo_local": sample_local_data["tipo_local"],
        "activo": True,
    }
    local_list = {"items": [local_summary, local_summary], "total": 2}
    mock_local_service.get_locales.return_value = LocalList(**local_list)

    # Act
    response = test_client.get("/api/v1/locales?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_local_service.get_locales.assert_awaited_once_with(0, 10)


def test_list_locales_validation_error(
    test_client, mock_db_session_dependency, mock_local_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)

    PROCESO:
        - Configura el mock para simular un error de validación.
        - Realiza una solicitud GET al endpoint con parámetros inválidos.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 422 (Unprocessable Entity)
        - Los detalles del error deben mencionar el parámetro limit
        - El servicio no debe ser llamado debido a la validación de FastAPI
    """
    # Arrange
    mock_local_service.get_locales.side_effect = LocalValidationError(
        "El parámetro 'limit' debe ser mayor a cero"
    )

    # Act
    response = test_client.get("/api/v1/locales?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
    assert response.status_code == 422
    # Verificamos que el error esté relacionado con el parámetro limit
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)
    # No debe llamar al servicio porque la validación falla antes
    mock_local_service.get_locales.assert_not_called()


def test_update_local_success(
    test_client,
    mock_db_session_dependency,
    mock_local_service,
    sample_local_id,
    sample_local_data,
):
    """
    Prueba la actualización exitosa de un local.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)
        - Los datos de muestra deben estar disponibles (sample_local_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Local Actualizado"}
    updated_data = {**sample_local_data, "nombre": "Local Actualizado"}
    mock_local_service.update_local.return_value = LocalResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/locales/{sample_local_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["nombre"] == "Local Actualizado"
    mock_local_service.update_local.assert_awaited_once()


def test_update_local_not_found(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_id
):
    """
    Prueba el manejo de errores al actualizar un local que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el local
        - El método update_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Local Actualizado"}
    mock_local_service.update_local.side_effect = LocalNotFoundError(
        f"No se encontró el local con ID {sample_local_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/locales/{sample_local_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el local con ID {sample_local_id}" in response.json()["detail"]
    mock_local_service.update_local.assert_awaited_once()


def test_update_local_conflict(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_id
):
    """
    Prueba el manejo de errores al actualizar un local con código duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del código
        - El método update_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"codigo": "CEV-999"}
    mock_local_service.update_local.side_effect = LocalConflictError(
        "Ya existe un local con el código 'CEV-999'"
    )

    # Act
    response = test_client.put(f"/api/v1/locales/{sample_local_id}", json=update_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un local" in response.json()["detail"]
    mock_local_service.update_local.assert_awaited_once()


def test_delete_local_success(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_id
):
    """
    Prueba la eliminación exitosa de un local.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_local del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_local_service.delete_local.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/locales/{sample_local_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_local_service.delete_local.assert_awaited_once_with(sample_local_id)


def test_delete_local_not_found(
    test_client, mock_db_session_dependency, mock_local_service, sample_local_id
):
    """
    Prueba el manejo de errores al eliminar un local que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de locales debe estar mockeado (mock_local_service)
        - Se debe tener un ID de local válido (sample_local_id)

    PROCESO:
        - Configura el mock para simular que el local no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el local
        - El método delete_local del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_local_service.delete_local.side_effect = LocalNotFoundError(
        f"No se encontró el local con ID {sample_local_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/locales/{sample_local_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el local con ID {sample_local_id}" in response.json()["detail"]
    mock_local_service.delete_local.assert_awaited_once()
