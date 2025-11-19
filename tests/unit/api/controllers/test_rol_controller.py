"""
Pruebas unitarias para el controlador de roles.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.rol_controller import router, get_database_session
from src.business_logic.auth.rol_service import RolService
from src.business_logic.exceptions.rol_exceptions import (
    RolNotFoundError,
    RolConflictError,
    RolValidationError,
)
from src.api.schemas.rol_schema import RolResponse, RolList

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
def mock_rol_service():
    """
    Fixture que proporciona un mock del servicio de roles.

    PRECONDICIONES:
        - La clase RolService debe estar importada correctamente

    PROCESO:
        - Crea un patch del servicio de roles
        - Configura el servicio mock con métodos asíncronos

    POSTCONDICIONES:
        - Devuelve una instancia mock de RolService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.rol_controller.RolService") as mock:
        service_instance = AsyncMock(spec=RolService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_usuario_id():
    """
    Fixture que proporciona un ID de usuario de muestra.

    PRECONDICIONES:
        - La biblioteca ULID debe estar importada correctamente

    PROCESO:
        - Genera un ULID único
        - Lo convierte a string para usarlo en las pruebas

    POSTCONDICIONES:
        - Devuelve un string con formato ULID válido para usar como ID de usuario
    """
    return str(ULID())


@pytest.fixture
def sample_rol_data():
    """
    Fixture que proporciona datos de muestra para un rol.

    PRECONDICIONES:
        - La biblioteca ULID debe estar importada correctamente

    PROCESO:
        - Crea un diccionario con datos ficticios de un rol
        - Incluye id, nombre, descripción, activo y fechas

    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para un rol
        - Los datos pueden ser usados para construir objetos RolModel o RolResponse
    """
    return {
        "id": str(ULID()),
        "nombre": "COMENSAL",
        "descripcion": "Rol para clientes del restaurante",
        "activo": True,
        "fecha_creacion": "2025-10-26T12:00:00",
        "fecha_modificacion": "2025-10-26T12:00:00",
    }


def test_get_nombre_rol_usuario_success(
    test_client, mock_db_session_dependency, mock_rol_service, sample_usuario_id
):
    """
    Prueba la obtención exitosa del nombre del rol de un usuario.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de roles debe estar mockeado (mock_rol_service)
        - Se debe tener un ID de usuario válido (sample_usuario_id)

    PROCESO:
        - Configura el mock para simular la existencia de un usuario con rol.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_nombre_rol_by_usuario_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    expected_response = {"nombre_rol": "COMENSAL"}
    mock_rol_service.get_nombre_rol_by_usuario_id.return_value = expected_response

    # Act
    response = test_client.get(f"/api/v1/roles/usuario/{sample_usuario_id}/nombre")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_response
    mock_rol_service.get_nombre_rol_by_usuario_id.assert_awaited_once_with(sample_usuario_id)


def test_get_nombre_rol_usuario_not_found(
    test_client, mock_db_session_dependency, mock_rol_service, sample_usuario_id
):
    """
    Prueba el manejo de errores al buscar el rol de un usuario que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de roles debe estar mockeado (mock_rol_service)
        - Se debe tener un ID de usuario válido (sample_usuario_id)

    PROCESO:
        - Configura el mock para simular que el usuario no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el usuario o rol
        - El método get_nombre_rol_by_usuario_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_rol_service.get_nombre_rol_by_usuario_id.side_effect = RolNotFoundError(
        f"No se encontró el usuario con ID {sample_usuario_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/roles/usuario/{sample_usuario_id}/nombre")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el usuario con ID {sample_usuario_id}" in response.json()["detail"]
    mock_rol_service.get_nombre_rol_by_usuario_id.assert_awaited_once_with(sample_usuario_id)


def test_get_nombre_rol_usuario_sin_rol_asignado(
    test_client, mock_db_session_dependency, mock_rol_service, sample_usuario_id
):
    """
    Prueba el manejo de errores al buscar el rol de un usuario sin rol asignado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de roles debe estar mockeado (mock_rol_service)
        - Se debe tener un ID de usuario válido (sample_usuario_id)

    PROCESO:
        - Configura el mock para simular que el usuario no tiene rol asignado.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que el usuario no tiene rol asignado
        - El método get_nombre_rol_by_usuario_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_rol_service.get_nombre_rol_by_usuario_id.side_effect = RolNotFoundError(
        f"El usuario con ID {sample_usuario_id} no tiene un rol asignado"
    )

    # Act
    response = test_client.get(f"/api/v1/roles/usuario/{sample_usuario_id}/nombre")

    # Assert
    assert response.status_code == 404
    assert "no tiene un rol asignado" in response.json()["detail"]
    mock_rol_service.get_nombre_rol_by_usuario_id.assert_awaited_once_with(sample_usuario_id)


def test_get_nombre_rol_usuario_rol_inexistente(
    test_client, mock_db_session_dependency, mock_rol_service, sample_usuario_id
):
    """
    Prueba el manejo de errores al buscar un rol que no existe en la BD.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de roles debe estar mockeado (mock_rol_service)
        - Se debe tener un ID de usuario válido (sample_usuario_id)

    PROCESO:
        - Configura el mock para simular que el rol del usuario no existe en la BD.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el rol
        - El método get_nombre_rol_by_usuario_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    rol_id = str(ULID())
    mock_rol_service.get_nombre_rol_by_usuario_id.side_effect = RolNotFoundError(
        f"No se encontró el rol con ID {rol_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/roles/usuario/{sample_usuario_id}/nombre")

    # Assert
    assert response.status_code == 404
    assert "No se encontró el rol con ID" in response.json()["detail"]
    mock_rol_service.get_nombre_rol_by_usuario_id.assert_awaited_once_with(sample_usuario_id)


def test_get_nombre_rol_usuario_internal_error(
    test_client, mock_db_session_dependency, mock_rol_service, sample_usuario_id
):
    """
    Prueba el manejo de errores internos del servidor.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de roles debe estar mockeado (mock_rol_service)
        - Se debe tener un ID de usuario válido (sample_usuario_id)

    PROCESO:
        - Configura el mock para simular un error interno.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 500 (Internal Server Error)
        - El mensaje de error debe indicar error interno del servidor
        - El método get_nombre_rol_by_usuario_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_rol_service.get_nombre_rol_by_usuario_id.side_effect = Exception("Error de conexión a BD")

    # Act
    response = test_client.get(f"/api/v1/roles/usuario/{sample_usuario_id}/nombre")

    # Assert
    assert response.status_code == 500
    assert "Error interno del servidor" in response.json()["detail"]
    mock_rol_service.get_nombre_rol_by_usuario_id.assert_awaited_once_with(sample_usuario_id)
