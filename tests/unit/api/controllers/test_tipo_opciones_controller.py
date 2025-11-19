"""
Pruebas unitarias para los endpoints de tipos de opciones.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.tipo_opciones_controller import router, get_database_session
from src.business_logic.pedidos.tipo_opciones_service import TipoOpcionService
from src.business_logic.exceptions.tipo_opciones_exceptions import (
    TipoOpcionNotFoundError,
    TipoOpcionConflictError,
    TipoOpcionValidationError,
)
from src.api.schemas.tipo_opciones_schema import TipoOpcionResponse, TipoOpcionList

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
def mock_tipo_opcion_service():
    """
    Fixture que proporciona un mock del servicio de tipos de opciones.
    
    PRECONDICIONES:
        - La clase TipoOpcionService debe estar importada correctamente
    
    PROCESO:
        - Crea un patch del servicio de tipos de opciones
        - Configura el servicio mock con métodos asíncronos
    
    POSTCONDICIONES:
        - Devuelve una instancia mock de TipoOpcionService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.tipo_opciones_controller.TipoOpcionService") as mock:
        service_instance = AsyncMock(spec=TipoOpcionService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_tipo_opcion_id():
    """
    Fixture que proporciona un ID de tipo de opción de muestra.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Genera un UUID v4 único
        - Lo convierte a string para usarlo en las pruebas
    
    POSTCONDICIONES:
        - Devuelve un string con formato UUID válido para usar como ID de tipo de opción
    """
    return str(str(ULID()))


@pytest.fixture
def sample_tipo_opcion_data():
    """
    Fixture que proporciona datos de muestra para un tipo de opción.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Crea un diccionario con datos ficticios de un tipo de opción
        - Incluye id, código, nombre, descripción, estado activo, orden y fechas
    
    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para un tipo de opción
        - Los datos pueden ser usados para construir objetos TipoOpcionModel o TipoOpcionResponse
    """
    return {
        "id": str(str(ULID())),
        "codigo": "nivel_aji",
        "nombre": "Nivel de Ají",
        "descripcion": "Nivel de picante del plato",
        "activo": True,
        "orden": 1,
        "fecha_creacion": "2025-10-08T12:00:00",
        "fecha_modificacion": "2025-10-08T12:00:00",
    }


def test_create_tipo_opcion_success(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_data
):
    """
    Prueba la creación exitosa de un tipo de opción.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Los datos de muestra deben estar disponibles (sample_tipo_opcion_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    tipo_opcion_data = {
        "codigo": "nivel_aji",
        "nombre": "Nivel de Ají",
        "descripcion": "Nivel de picante del plato",
        "activo": True,
        "orden": 1,
    }
    mock_tipo_opcion_service.create_tipo_opcion.return_value = TipoOpcionResponse(**sample_tipo_opcion_data)

    # Act
    response = test_client.post("/api/v1/tipos-opciones", json=tipo_opcion_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["codigo"] == sample_tipo_opcion_data["codigo"]
    assert response.json()["nombre"] == sample_tipo_opcion_data["nombre"]
    assert response.json()["descripcion"] == sample_tipo_opcion_data["descripcion"]
    mock_tipo_opcion_service.create_tipo_opcion.assert_awaited_once()


def test_create_tipo_opcion_conflict(test_client, mock_db_session_dependency, mock_tipo_opcion_service):
    """
    Prueba el manejo de errores al crear un tipo de opción con código duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del tipo de opción
        - El método create_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    tipo_opcion_data = {
        "codigo": "nivel_aji",
        "nombre": "Nivel de Ají",
        "activo": True,
    }
    mock_tipo_opcion_service.create_tipo_opcion.side_effect = TipoOpcionConflictError(
        "Ya existe un tipo de opción con el código 'nivel_aji'"
    )

    # Act
    response = test_client.post("/api/v1/tipos-opciones", json=tipo_opcion_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un tipo de opción" in response.json()["detail"]
    mock_tipo_opcion_service.create_tipo_opcion.assert_awaited_once()


def test_get_tipo_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_tipo_opcion_service,
    sample_tipo_opcion_id,
    sample_tipo_opcion_data,
):
    """
    Prueba la obtención exitosa de un tipo de opción por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)
        - Los datos de muestra deben estar disponibles (sample_tipo_opcion_data)

    PROCESO:
        - Configura el mock para simular la existencia de un tipo de opción.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_tipo_opcion_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_tipo_opcion_service.get_tipo_opcion_by_id.return_value = TipoOpcionResponse(**sample_tipo_opcion_data)

    # Act
    response = test_client.get(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_tipo_opcion_data["id"]
    assert response.json()["codigo"] == sample_tipo_opcion_data["codigo"]
    mock_tipo_opcion_service.get_tipo_opcion_by_id.assert_awaited_once()


def test_get_tipo_opcion_not_found(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_id
):
    """
    Prueba el manejo de errores al buscar un tipo de opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)

    PROCESO:
        - Configura el mock para simular que el tipo de opción no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el tipo de opción
        - El método get_tipo_opcion_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_tipo_opcion_service.get_tipo_opcion_by_id.side_effect = TipoOpcionNotFoundError(
        f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}" in response.json()["detail"]
    mock_tipo_opcion_service.get_tipo_opcion_by_id.assert_awaited_once()


def test_list_tipos_opciones_success(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_data
):
    """
    Prueba la obtención exitosa de una lista de tipos de opciones.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Los datos de muestra deben estar disponibles (sample_tipo_opcion_data)

    PROCESO:
        - Configura el mock para simular una lista de tipos de opciones.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de tipos de opciones y el total
        - El método get_tipos_opciones del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    tipo_opcion_summary = {
        "id": sample_tipo_opcion_data["id"],
        "codigo": sample_tipo_opcion_data["codigo"],
        "nombre": sample_tipo_opcion_data["nombre"],
        "activo": True,
        "orden": 1,
    }
    tipo_opcion_list = {"items": [tipo_opcion_summary, tipo_opcion_summary], "total": 2}
    mock_tipo_opcion_service.get_tipos_opciones.return_value = TipoOpcionList(**tipo_opcion_list)

    # Act
    response = test_client.get("/api/v1/tipos-opciones?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_tipo_opcion_service.get_tipos_opciones.assert_awaited_once_with(0, 10, None, None)


def test_list_tipos_opciones_validation_error(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)

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
    mock_tipo_opcion_service.get_tipos_opciones.side_effect = TipoOpcionValidationError(
        "El parámetro 'limit' debe ser mayor a cero"
    )

    # Act
    response = test_client.get("/api/v1/tipos-opciones?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
    assert response.status_code == 422
    # Verificamos que el error esté relacionado con el parámetro limit
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)
    # No debe llamar al servicio porque la validación falla antes
    mock_tipo_opcion_service.get_tipos_opciones.assert_not_called()


def test_update_tipo_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_tipo_opcion_service,
    sample_tipo_opcion_id,
    sample_tipo_opcion_data,
):
    """
    Prueba la actualización exitosa de un tipo de opción.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)
        - Los datos de muestra deben estar disponibles (sample_tipo_opcion_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Nivel de Ají Actualizado", "orden": 5}
    updated_data = {**sample_tipo_opcion_data, "nombre": "Nivel de Ají Actualizado", "orden": 5}
    mock_tipo_opcion_service.update_tipo_opcion.return_value = TipoOpcionResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["nombre"] == "Nivel de Ají Actualizado"
    mock_tipo_opcion_service.update_tipo_opcion.assert_awaited_once()


def test_update_tipo_opcion_not_found(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_id
):
    """
    Prueba el manejo de errores al actualizar un tipo de opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)

    PROCESO:
        - Configura el mock para simular que el tipo de opción no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el tipo de opción
        - El método update_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Tipo de Opción Actualizado"}
    mock_tipo_opcion_service.update_tipo_opcion.side_effect = TipoOpcionNotFoundError(
        f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}" in response.json()["detail"]
    mock_tipo_opcion_service.update_tipo_opcion.assert_awaited_once()


def test_update_tipo_opcion_conflict(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_id
):
    """
    Prueba el manejo de errores al actualizar un tipo de opción con código duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del código
        - El método update_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"codigo": "otro_codigo"}
    mock_tipo_opcion_service.update_tipo_opcion.side_effect = TipoOpcionConflictError(
        "Ya existe un tipo de opción con el código 'otro_codigo'"
    )

    # Act
    response = test_client.put(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un tipo de opción" in response.json()["detail"]
    mock_tipo_opcion_service.update_tipo_opcion.assert_awaited_once()


def test_delete_tipo_opcion_success(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_id
):
    """
    Prueba la eliminación exitosa de un tipo de opción.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_tipo_opcion del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_tipo_opcion_service.delete_tipo_opcion.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_tipo_opcion_service.delete_tipo_opcion.assert_awaited_once_with(sample_tipo_opcion_id)


def test_delete_tipo_opcion_not_found(
    test_client, mock_db_session_dependency, mock_tipo_opcion_service, sample_tipo_opcion_id
):
    """
    Prueba el manejo de errores al eliminar un tipo de opción que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de tipos de opciones debe estar mockeado (mock_tipo_opcion_service)
        - Se debe tener un ID de tipo de opción válido (sample_tipo_opcion_id)

    PROCESO:
        - Configura el mock para simular que el tipo de opción no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el tipo de opción
        - El método delete_tipo_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_tipo_opcion_service.delete_tipo_opcion.side_effect = TipoOpcionNotFoundError(
        f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/tipos-opciones/{sample_tipo_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el tipo de opción con ID {sample_tipo_opcion_id}" in response.json()["detail"]
    mock_tipo_opcion_service.delete_tipo_opcion.assert_awaited_once()

