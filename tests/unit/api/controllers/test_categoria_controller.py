"""
Pruebas unitarias para los endpoints de categorías.
"""

import pytest
from unittest.mock import AsyncMock, patch
from ulid import ULID
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.categoria_controller import router, get_database_session
from src.business_logic.menu.categoria_service import CategoriaService
from src.business_logic.exceptions.categoria_exceptions import (
    CategoriaNotFoundError,
    CategoriaConflictError,
    CategoriaValidationError,
)
from src.api.schemas.categoria_schema import CategoriaResponse, CategoriaList

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
def mock_categoria_service():
    """
    Fixture que proporciona un mock del servicio de categorías.
    
    PRECONDICIONES:
        - La clase CategoriaService debe estar importada correctamente
    
    PROCESO:
        - Crea un patch del servicio de categorías
        - Configura el servicio mock con métodos asíncronos
    
    POSTCONDICIONES:
        - Devuelve una instancia mock de CategoriaService lista para usar en pruebas
        - El mock puede configurarse para simular diferentes comportamientos
    """
    with patch("src.api.controllers.categoria_controller.CategoriaService") as mock:
        service_instance = AsyncMock(spec=CategoriaService)
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def sample_categoria_id():
    """
    Fixture que proporciona un ID de categoría de muestra.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Genera un UUID v4 único
        - Lo convierte a string para usarlo en las pruebas
    
    POSTCONDICIONES:
        - Devuelve un string con formato UUID válido para usar como ID de categoría
    """
    return str(str(ULID()))


@pytest.fixture
def sample_categoria_data():
    """
    Fixture que proporciona datos de muestra para una categoría.
    
    PRECONDICIONES:
        - La biblioteca uuid debe estar importada correctamente
    
    PROCESO:
        - Crea un diccionario con datos ficticios de una categoría
        - Incluye id, nombre, descripción, imagen_path, estado y fechas
    
    POSTCONDICIONES:
        - Devuelve un diccionario con todos los campos necesarios para una categoría
        - Los datos pueden ser usados para construir objetos CategoriaModel o CategoriaResponse
    """
    return {
        "id": str(str(ULID())),
        "nombre": "Bebidas",
        "descripcion": "Bebidas frías y calientes",
        "imagen_path": "/images/bebidas.jpg",
        "activo": True,
        "fecha_creacion": "2025-10-06T12:00:00",
        "fecha_modificacion": "2025-10-06T12:00:00",
    }


def test_create_categoria_success(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_data
):
    """
    Prueba la creación exitosa de una categoría.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Los datos de muestra deben estar disponibles (sample_categoria_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    categoria_data = {
        "nombre": "Bebidas",
        "descripcion": "Bebidas frías y calientes",
        "imagen_path": "/images/bebidas.jpg",
    }
    mock_categoria_service.create_categoria.return_value = CategoriaResponse(**sample_categoria_data)

    # Act
    response = test_client.post("/api/v1/categorias", json=categoria_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["nombre"] == sample_categoria_data["nombre"]
    assert response.json()["descripcion"] == sample_categoria_data["descripcion"]
    assert response.json()["imagen_path"] == sample_categoria_data["imagen_path"]
    mock_categoria_service.create_categoria.assert_awaited_once()


def test_create_categoria_conflict(test_client, mock_db_session_dependency, mock_categoria_service):
    """
    Prueba el manejo de errores al crear una categoría con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad de la categoría
        - El método create_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    categoria_data = {
        "nombre": "Bebidas",
        "descripcion": "Bebidas frías y calientes",
    }
    mock_categoria_service.create_categoria.side_effect = CategoriaConflictError(
        "Ya existe una categoría con el nombre 'Bebidas'"
    )

    # Act
    response = test_client.post("/api/v1/categorias", json=categoria_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe una categoría" in response.json()["detail"]
    mock_categoria_service.create_categoria.assert_awaited_once()


def test_get_categoria_success(
    test_client,
    mock_db_session_dependency,
    mock_categoria_service,
    sample_categoria_id,
    sample_categoria_data,
):
    """
    Prueba la obtención exitosa de una categoría por su ID.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)
        - Los datos de muestra deben estar disponibles (sample_categoria_data)

    PROCESO:
        - Configura el mock para simular la existencia de una categoría.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_categoria_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_categoria_service.get_categoria_by_id.return_value = CategoriaResponse(**sample_categoria_data)

    # Act
    response = test_client.get(f"/api/v1/categorias/{sample_categoria_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == sample_categoria_data["id"]
    assert response.json()["nombre"] == sample_categoria_data["nombre"]
    assert response.json()["imagen_path"] == sample_categoria_data["imagen_path"]
    mock_categoria_service.get_categoria_by_id.assert_awaited_once()


def test_get_categoria_not_found(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_id
):
    """
    Prueba el manejo de errores al buscar una categoría que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)

    PROCESO:
        - Configura el mock para simular que la categoría no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la categoría
        - El método get_categoria_by_id del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_categoria_service.get_categoria_by_id.side_effect = CategoriaNotFoundError(
        f"No se encontró la categoría con ID {sample_categoria_id}"
    )

    # Act
    response = test_client.get(f"/api/v1/categorias/{sample_categoria_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la categoría con ID {sample_categoria_id}" in response.json()["detail"]
    mock_categoria_service.get_categoria_by_id.assert_awaited_once()


def test_list_categorias_success(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_data
):
    """
    Prueba la obtención exitosa de una lista de categorías.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Los datos de muestra deben estar disponibles (sample_categoria_data)

    PROCESO:
        - Configura el mock para simular una lista de categorías.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de categorías y el total
        - El método get_categorias del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    categoria_summary = {
        "id": sample_categoria_data["id"],
        "nombre": sample_categoria_data["nombre"],
        "descripcion": sample_categoria_data.get("descripcion"),
        "imagen_path": sample_categoria_data.get("imagen_path"),
        "activo": True,
    }
    categoria_list = {"items": [categoria_summary, categoria_summary], "total": 2}
    mock_categoria_service.get_categorias.return_value = CategoriaList(**categoria_list)

    # Act
    response = test_client.get("/api/v1/categorias?skip=0&limit=10")

    # Assert
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    mock_categoria_service.get_categorias.assert_awaited_once_with(0, 10, None, None)


def test_list_categorias_validation_error(
    test_client, mock_db_session_dependency, mock_categoria_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)

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
    mock_categoria_service.get_categorias.side_effect = CategoriaValidationError(
        "El parámetro 'limit' debe ser mayor a cero"
    )

    # Act
    response = test_client.get("/api/v1/categorias?skip=0&limit=0")

    # Assert
    # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
    assert response.status_code == 422
    # Verificamos que el error esté relacionado con el parámetro limit
    error_detail = response.json()["detail"]
    assert any("limit" in str(err).lower() for err in error_detail)
    # No debe llamar al servicio porque la validación falla antes
    mock_categoria_service.get_categorias.assert_not_called()


def test_update_categoria_success(
    test_client,
    mock_db_session_dependency,
    mock_categoria_service,
    sample_categoria_id,
    sample_categoria_data,
):
    """
    Prueba la actualización exitosa de una categoría.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)
        - Los datos de muestra deben estar disponibles (sample_categoria_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Bebidas Actualizado"}
    updated_data = {**sample_categoria_data, "nombre": "Bebidas Actualizado"}
    mock_categoria_service.update_categoria.return_value = CategoriaResponse(**updated_data)

    # Act
    response = test_client.put(f"/api/v1/categorias/{sample_categoria_id}", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["nombre"] == "Bebidas Actualizado"
    mock_categoria_service.update_categoria.assert_awaited_once()


def test_update_categoria_not_found(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_id
):
    """
    Prueba el manejo de errores al actualizar una categoría que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)

    PROCESO:
        - Configura el mock para simular que la categoría no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la categoría
        - El método update_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Bebidas Actualizado"}
    mock_categoria_service.update_categoria.side_effect = CategoriaNotFoundError(
        f"No se encontró la categoría con ID {sample_categoria_id}"
    )

    # Act
    response = test_client.put(f"/api/v1/categorias/{sample_categoria_id}", json=update_data)

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la categoría con ID {sample_categoria_id}" in response.json()["detail"]
    mock_categoria_service.update_categoria.assert_awaited_once()


def test_update_categoria_conflict(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_id
):
    """
    Prueba el manejo de errores al actualizar una categoría con nombre duplicado.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad del nombre
        - El método update_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nombre": "Otra Categoría"}
    mock_categoria_service.update_categoria.side_effect = CategoriaConflictError(
        "Ya existe una categoría con el nombre 'Otra Categoría'"
    )

    # Act
    response = test_client.put(f"/api/v1/categorias/{sample_categoria_id}", json=update_data)

    # Assert
    assert response.status_code == 409
    assert "Ya existe una categoría" in response.json()["detail"]
    mock_categoria_service.update_categoria.assert_awaited_once()


def test_delete_categoria_success(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_id
):
    """
    Prueba la eliminación exitosa de una categoría.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código HTTP apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - La respuesta no debe tener contenido
        - El método delete_categoria del servicio debe haber sido llamado con el ID correcto
    """
    # Arrange
    mock_categoria_service.delete_categoria.return_value = True

    # Act
    response = test_client.delete(f"/api/v1/categorias/{sample_categoria_id}")

    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content
    mock_categoria_service.delete_categoria.assert_awaited_once_with(sample_categoria_id)


def test_delete_categoria_not_found(
    test_client, mock_db_session_dependency, mock_categoria_service, sample_categoria_id
):
    """
    Prueba el manejo de errores al eliminar una categoría que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de categorías debe estar mockeado (mock_categoria_service)
        - Se debe tener un ID de categoría válido (sample_categoria_id)

    PROCESO:
        - Configura el mock para simular que la categoría no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la categoría
        - El método delete_categoria del servicio debe haber sido llamado una vez
    """
    # Arrange
    mock_categoria_service.delete_categoria.side_effect = CategoriaNotFoundError(
        f"No se encontró la categoría con ID {sample_categoria_id}"
    )

    # Act
    response = test_client.delete(f"/api/v1/categorias/{sample_categoria_id}")

    # Assert
    assert response.status_code == 404
    assert f"No se encontró la categoría con ID {sample_categoria_id}" in response.json()["detail"]
    mock_categoria_service.delete_categoria.assert_awaited_once()
