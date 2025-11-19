"""
Pruebas unitarias para los endpoints de productos.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from decimal import Decimal
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.producto_controller import router, get_database_session
from src.business_logic.menu.producto_service import ProductoService
from src.business_logic.exceptions.producto_exceptions import (
    ProductoNotFoundError,
    ProductoConflictError,
    ProductoValidationError,
)
from src.api.schemas.producto_schema import ProductoResponse, ProductoList

app = FastAPI()
app.include_router(router, prefix="/api/v1")


@pytest.fixture
def test_client():
    """Fixture para TestClient local de ProductoController"""
    return TestClient(app)


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
def mock_producto_service():
    """
    Fixture que proporciona un mock del servicio de productos.
    
    PRECONDICIONES:
        - La clase ProductoService debe estar importada correctamente
    
    PROCESO:
        - Crea un patch del servicio de productos
        - Configura el servicio mock con métodos asíncronos
    
    POSTCONDICIONES:
        - Devuelve una instancia mock de ProductoService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.producto_controller.ProductoService") as mock:
        service_instance = AsyncMock(spec=ProductoService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_producto_id():
    """
    Fixture que proporciona un ID de producto de muestra.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Genera un UUID v4 único
        - Lo convierte a string para usarlo en las pruebas
    
    POSTCONDICIONES:
        - Devuelve un string con formato UUID válido para usar como ID de producto
    """
    return str(str(ULID()))


@pytest.fixture
def sample_producto_data():
    """
    Fixture que proporciona datos de muestra para un producto.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Crea un diccionario con datos ficticios de un producto
        - Incluye id, nombre, descripción, precio, estado y fechas
    
    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para un producto
        - Los datos pueden ser usados para construir objetos ProductoModel o ProductoResponse
    """
    return {
        "id": str(str(ULID())),
        "id_categoria": str(str(ULID())),
        "nombre": "Hamburguesa Clásica",
        "descripcion": "Hamburguesa con carne, lechuga y tomate",
        "precio_base": "15.99",
        "imagen_path": "/images/hamburguesa.jpg",
        "imagen_alt_text": "Hamburguesa clásica",
        "disponible": True,
        "destacado": False,
        "fecha_creacion": "2025-10-06T12:00:00",
        "fecha_modificacion": "2025-10-06T12:00:00",
    }


def test_create_producto_success(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_data
):
    """
    Prueba la creación exitosa de un producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Los datos de muestra deben estar disponibles (sample_producto_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_data = {
        "id_categoria": sample_producto_data["id_categoria"],
        "nombre": "Hamburguesa Clásica",
        "descripcion": "Hamburguesa con carne, lechuga y tomate",
        "precio_base": "15.99",
    }
    mock_producto_service.create_producto.return_value = ProductoResponse(**sample_producto_data)

    # Act
    response = test_client.post("/api/v1/productos", json=producto_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["nombre"] == sample_producto_data["nombre"]
    assert response.json()["descripcion"] == sample_producto_data["descripcion"]
    mock_producto_service.create_producto.assert_awaited_once()


def test_create_producto_conflict(test_client, mock_db_session_dependency, mock_producto_service):
    """
    Prueba el manejo de errores al crear un producto con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del producto
        - El método create_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_data = {
        "id_categoria": str(str(ULID())),
        "nombre": "Hamburguesa Clásica",
        "descripcion": "Hamburguesa con carne",
        "precio_base": "15.99",
    }
    mock_producto_service.create_producto.side_effect = ProductoConflictError(
        "Ya existe un producto con el nombre 'Hamburguesa Clásica'"
    )

    # Act
    response = test_client.post("/api/v1/productos", json=producto_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un producto" in response.json()["detail"]
    mock_producto_service.create_producto.assert_awaited_once()


def test_get_producto_success(
    test_client,
    mock_db_session_dependency,
    mock_producto_service,
    sample_producto_id,
    sample_producto_data,
):
    """
    Prueba la obtención exitosa de un producto por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)
        - Los datos de muestra deben estar disponibles (sample_producto_data)

    PROCESO:
        - Configura el mock para simular la existencia de un producto.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_producto_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_service.get_producto_by_id.return_value = ProductoResponse(**sample_producto_data)

    # Act
    response = test_client.get(f"/api/v1/productos/{sample_producto_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_producto_data["id"]
    assert response.json()["nombre"] == sample_producto_data["nombre"]
    mock_producto_service.get_producto_by_id.assert_awaited_once()


def test_get_producto_not_found(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_id
):
    """
    Prueba el manejo de errores al buscar un producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el producto
        - El método get_producto_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_service.get_producto_by_id.side_effect = ProductoNotFoundError(
        f"No se encontró el producto con ID {sample_producto_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/productos/{sample_producto_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el producto con ID {sample_producto_id}" in response.json()["detail"]
    mock_producto_service.get_producto_by_id.assert_awaited_once()


def test_list_productos_success(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_data
):
    """
    Prueba la obtención exitosa de una lista de productos.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Los datos de muestra deben estar disponibles (sample_producto_data)

    PROCESO:
        - Configura el mock para simular una lista de productos.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de productos y el total
        - El método get_productos del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    producto_summary = {
        "id": sample_producto_data["id"],
        "nombre": sample_producto_data["nombre"],
        "precio_base": sample_producto_data["precio_base"],
        "disponible": True,
    }
    producto_list = {"items": [producto_summary, producto_summary], "total": 2}
    mock_producto_service.get_productos.return_value = ProductoList(**producto_list)

    # Act
    response = test_client.get("/api/v1/productos?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_producto_service.get_productos.assert_awaited_once_with(0, 10, None, None, None)


def test_list_productos_validation_error(
    test_client, mock_db_session_dependency, mock_producto_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)

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
    mock_producto_service.get_productos.side_effect = ProductoValidationError(
        "El parámetro 'limit' debe ser mayor a cero"
    )

    # Act
    response = test_client.get("/api/v1/productos?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
    assert response.status_code == 422
    # Verificamos que el error esté relacionado con el parámetro limit
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)
    # No debe llamar al servicio porque la validación falla antes
    mock_producto_service.get_productos.assert_not_called()


def test_list_productos_with_categoria_filter(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_data
):
    """
    Prueba la obtención exitosa de una lista de productos filtrados por categoría.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Los datos de muestra deben estar disponibles (sample_producto_data)

    PROCESO:
        - Configura el mock para simular una lista filtrada de productos.
        - Realiza una solicitud GET al endpoint con filtro de categoría.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de productos filtrados y el total
        - El método get_productos del servicio debe haber sido llamado con el id_categoria
    """
    # Arrange
    id_categoria = str(ULID())
    producto_summary = {
        "id": sample_producto_data["id"],
        "nombre": sample_producto_data["nombre"],
        "precio_base": sample_producto_data["precio_base"],
        "disponible": True,
    }
    producto_list = {"items": [producto_summary], "total": 1}
    mock_producto_service.get_productos.return_value = ProductoList(**producto_list)

    # Act
    response = test_client.get(f"/api/v1/productos?skip=0&limit=10&id_categoria={id_categoria}")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    mock_producto_service.get_productos.assert_awaited_once_with(0, 10, id_categoria, None, None)


def test_update_producto_success(
    test_client,
    mock_db_session_dependency,
    mock_producto_service,
    sample_producto_id,
    sample_producto_data,
):
    """
    Prueba la actualización exitosa de un producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)
        - Los datos de muestra deben estar disponibles (sample_producto_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Hamburguesa Actualizada"}
    updated_data = {**sample_producto_data, "nombre": "Hamburguesa Actualizada"}
    mock_producto_service.update_producto.return_value = ProductoResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/productos/{sample_producto_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["nombre"] == "Hamburguesa Actualizada"
    mock_producto_service.update_producto.assert_awaited_once()


def test_update_producto_not_found(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_id
):
    """
    Prueba el manejo de errores al actualizar un producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el producto
        - El método update_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Hamburguesa Actualizada"}
    mock_producto_service.update_producto.side_effect = ProductoNotFoundError(
        f"No se encontró el producto con ID {sample_producto_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/productos/{sample_producto_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el producto con ID {sample_producto_id}" in response.json()["detail"]
    mock_producto_service.update_producto.assert_awaited_once()


def test_update_producto_conflict(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_id
):
    """
    Prueba el manejo de errores al actualizar un producto con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del nombre
        - El método update_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Otro Producto"}
    mock_producto_service.update_producto.side_effect = ProductoConflictError(
        "Ya existe un producto con el nombre 'Otro Producto'"
    )

    # Act
    response = test_client.put(f"/api/v1/productos/{sample_producto_id}", json=update_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe un producto" in response.json()["detail"]
    mock_producto_service.update_producto.assert_awaited_once()


def test_delete_producto_success(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_id
):
    """
    Prueba la eliminación exitosa de un producto.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_producto del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_producto_service.delete_producto.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/productos/{sample_producto_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_producto_service.delete_producto.assert_awaited_once_with(sample_producto_id)


def test_delete_producto_not_found(
    test_client, mock_db_session_dependency, mock_producto_service, sample_producto_id
):
    """
    Prueba el manejo de errores al eliminar un producto que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de productos debe estar mockeado (mock_producto_service)
        - Se debe tener un ID de producto válido (sample_producto_id)

    PROCESO:
        - Configura el mock para simular que el producto no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el producto
        - El método delete_producto del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_producto_service.delete_producto.side_effect = ProductoNotFoundError(
        f"No se encontró el producto con ID {sample_producto_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/productos/{sample_producto_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró el producto con ID {sample_producto_id}" in response.json()["detail"]
    mock_producto_service.delete_producto.assert_awaited_once()
