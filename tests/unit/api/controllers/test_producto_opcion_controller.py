"""
Pruebas unitarias para los endpoints de opciones de productos.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.producto_opcion_controller import router, get_database_session
from src.business_logic.pedidos.producto_opcion_service import ProductoOpcionService
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionNotFoundError,
    ProductoOpcionConflictError,
    ProductoOpcionValidationError,
)
from src.api.schemas.producto_opcion_schema import ProductoOpcionResponse, ProductoOpcionList

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
def mock_producto_opcion_service():
    """
    Fixture que proporciona un mock del servicio de opciones de productos.
    
    PRECONDICIONES:
        - La clase ProductoOpcionService debe estar importada correctamente
    
    PROCESO:
        - Crea un patch del servicio de opciones de productos
        - Configura el servicio mock con métodos asíncronos
    
    POSTCONDICIONES:
        - Devuelve una instancia mock de ProductoOpcionService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.producto_opcion_controller.ProductoOpcionService") as mock:
        service_instance = AsyncMock(spec=ProductoOpcionService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_producto_opcion_id():
    """
    Fixture que proporciona un ID de opción de producto de muestra.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Genera un UUID v4 único
        - Lo convierte a string para usarlo en las pruebas
    
    POSTCONDICIONES:
        - Devuelve un string con formato UUID válido para usar como ID de opción de producto
    """
    return str(str(ULID()))


@pytest.fixture
def sample_producto_opcion_data():
    """
    Fixture que proporciona datos de muestra para una opción de producto.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Crea un diccionario con datos ficticios de una opción de producto
        - Incluye id, nombre, precio adicional, estado y fechas
    
    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para una opción de producto
        - Los datos pueden ser usados para construir objetos ProductoOpcionModel o ProductoOpcionResponse
    """
    return {
        "id": str(str(ULID())),
        "id_producto": str(str(ULID())),
        "id_tipo_opcion": str(str(ULID())),
        "nombre": "Ají suave",
        "precio_adicional": "0.00",
        "activo": True,
        "orden": 1,
        "fecha_creacion": "2025-10-06T12:00:00",
        "fecha_modificacion": "2025-10-06T12:00:00",
    }


def test_create_producto_opcion_success(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_data
):
    """
    Prueba la creación exitosa de una opción de producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Los datos de muestra deben estar disponibles (sample_producto_opcion_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_opcion_data = {
        "id_producto": sample_producto_opcion_data["id_producto"],
        "id_tipo_opcion": sample_producto_opcion_data["id_tipo_opcion"],
        "nombre": "Ají suave",
        "precio_adicional": "0.00",
        "activo": True,
        "orden": 1
    }
    mock_producto_opcion_service.create_producto_opcion.return_value = ProductoOpcionResponse(**sample_producto_opcion_data)

    # Act
    response = test_client.post("/api/v1/producto-opciones", json=producto_opcion_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["nombre"] == sample_producto_opcion_data["nombre"]
    assert response.json()["precio_adicional"] == sample_producto_opcion_data["precio_adicional"]
    mock_producto_opcion_service.create_producto_opcion.assert_awaited_once()


def test_create_producto_opcion_conflict(test_client, mock_db_session_dependency, mock_producto_opcion_service):
    """
    Prueba el manejo de errores al crear una opción de producto con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad de la opción de producto
        - El método create_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_opcion_data = {
        "id_producto": str(str(ULID())),
        "id_tipo_opcion": str(str(ULID())),
        "nombre": "Ají suave",
        "precio_adicional": "0.00",
        "activo": True,
        "orden": 1
    }
    mock_producto_opcion_service.create_producto_opcion.side_effect = ProductoOpcionConflictError(
        "Ya existe una opción de producto con el nombre 'Ají suave'"
    )

    # Act
    response = test_client.post("/api/v1/producto-opciones", json=producto_opcion_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe una opción de producto" in response.json()["detail"]
    mock_producto_opcion_service.create_producto_opcion.assert_awaited_once()


def test_get_producto_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_producto_opcion_service,
    sample_producto_opcion_id,
    sample_producto_opcion_data,
):
    """
    Prueba la obtención exitosa de una opción de producto por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)
        - Los datos de muestra deben estar disponibles (sample_producto_opcion_data)

    PROCESO:
        - Configura el mock para simular la existencia de una opción de producto.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_producto_opcion_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_opcion_service.get_producto_opcion_by_id.return_value = ProductoOpcionResponse(**sample_producto_opcion_data)

    # Act
    response = test_client.get(f"/api/v1/producto-opciones/{sample_producto_opcion_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_producto_opcion_data["id"]
    assert response.json()["nombre"] == sample_producto_opcion_data["nombre"]
    mock_producto_opcion_service.get_producto_opcion_by_id.assert_awaited_once()


def test_get_producto_opcion_not_found(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_id
):
    """
    Prueba el manejo de errores al buscar una opción de producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)

    PROCESO:
        - Configura el mock para simular que la opción de producto no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la opción de producto
        - El método get_producto_opcion_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_opcion_service.get_producto_opcion_by_id.side_effect = ProductoOpcionNotFoundError(
        f"No se encontró la opción de producto con ID {sample_producto_opcion_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/producto-opciones/{sample_producto_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la opción de producto con ID {sample_producto_opcion_id}" in response.json()["detail"]
    mock_producto_opcion_service.get_producto_opcion_by_id.assert_awaited_once()


def test_list_producto_opciones_success(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_data
):
    """
    Prueba la obtención exitosa de una lista de opciones de productos.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Los datos de muestra deben estar disponibles (sample_producto_opcion_data)

    PROCESO:
        - Configura el mock para simular una lista de opciones de productos.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de opciones de productos y el total
        - El método get_producto_opciones del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    producto_opcion_summary = {
        "id": sample_producto_opcion_data["id"],
        "id_producto": sample_producto_opcion_data["id_producto"],
        "id_tipo_opcion": sample_producto_opcion_data["id_tipo_opcion"],
        "nombre": sample_producto_opcion_data["nombre"],
        "precio_adicional": sample_producto_opcion_data["precio_adicional"],
        "activo": True,
        "orden": sample_producto_opcion_data["orden"],
    }
    producto_opcion_list = {"items": [producto_opcion_summary, producto_opcion_summary], "total": 2}
    mock_producto_opcion_service.get_producto_opciones.return_value = ProductoOpcionList(**producto_opcion_list)

    # Act
    response = test_client.get("/api/v1/producto-opciones?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_producto_opcion_service.get_producto_opciones.assert_awaited_once_with(0, 10, None, None)


def test_list_producto_opciones_validation_error(
    test_client, mock_db_session_dependency, mock_producto_opcion_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)

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
    mock_producto_opcion_service.get_producto_opciones.side_effect = ProductoOpcionValidationError(
        "El parámetro 'limit' debe ser mayor a cero"
    )

    # Act
    response = test_client.get("/api/v1/producto-opciones?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
    assert response.status_code == 422
    # Verificamos que el error esté relacionado con el parámetro limit
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)
    # No debe llamar al servicio porque la validación falla antes
    mock_producto_opcion_service.get_producto_opciones.assert_not_called()


def test_update_producto_opcion_success(
    test_client,
    mock_db_session_dependency,
    mock_producto_opcion_service,
    sample_producto_opcion_id,
    sample_producto_opcion_data,
):
    """
    Prueba la actualización exitosa de una opción de producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)
        - Los datos de muestra deben estar disponibles (sample_producto_opcion_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Ají picante"}
    updated_data = {**sample_producto_opcion_data, "nombre": "Ají picante"}
    mock_producto_opcion_service.update_producto_opcion.return_value = ProductoOpcionResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/producto-opciones/{sample_producto_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["nombre"] == "Ají picante"
    mock_producto_opcion_service.update_producto_opcion.assert_awaited_once()


def test_update_producto_opcion_not_found(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_id
):
    """
    Prueba el manejo de errores al actualizar una opción de producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)

    PROCESO:
        - Configura el mock para simular que la opción de producto no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la opción de producto
        - El método update_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Ají picante"}
    mock_producto_opcion_service.update_producto_opcion.side_effect = ProductoOpcionNotFoundError(
        f"No se encontró la opción de producto con ID {sample_producto_opcion_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/producto-opciones/{sample_producto_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la opción de producto con ID {sample_producto_opcion_id}" in response.json()["detail"]
    mock_producto_opcion_service.update_producto_opcion.assert_awaited_once()


def test_update_producto_opcion_conflict(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_id
):
    """
    Prueba el manejo de errores al actualizar una opción de producto con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del nombre
        - El método update_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Otra Opción"}
    mock_producto_opcion_service.update_producto_opcion.side_effect = ProductoOpcionConflictError(
        "Ya existe una opción de producto con el nombre 'Otra Opción'"
    )

    # Act
    response = test_client.put(f"/api/v1/producto-opciones/{sample_producto_opcion_id}", json=update_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe una opción de producto" in response.json()["detail"]
    mock_producto_opcion_service.update_producto_opcion.assert_awaited_once()


def test_delete_producto_opcion_success(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_id
):
    """
    Prueba la eliminación exitosa de una opción de producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_producto_opcion del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_producto_opcion_service.delete_producto_opcion.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/producto-opciones/{sample_producto_opcion_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_producto_opcion_service.delete_producto_opcion.assert_awaited_once_with(sample_producto_opcion_id)


def test_delete_producto_opcion_not_found(
    test_client, mock_db_session_dependency, mock_producto_opcion_service, sample_producto_opcion_id
):
    """
    Prueba el manejo de errores al eliminar una opción de producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de opciones de productos debe estar mockeado (mock_producto_opcion_service)
        - Se debe tener un ID de opción de producto válido (sample_producto_opcion_id)

    PROCESO:
        - Configura el mock para simular que la opción de producto no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la opción de producto
        - El método delete_producto_opcion del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_opcion_service.delete_producto_opcion.side_effect = ProductoOpcionNotFoundError(
        f"No se encontró la opción de producto con ID {sample_producto_opcion_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/producto-opciones/{sample_producto_opcion_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la opción de producto con ID {sample_producto_opcion_id}" in response.json()["detail"]
    mock_producto_opcion_service.delete_producto_opcion.assert_awaited_once()
