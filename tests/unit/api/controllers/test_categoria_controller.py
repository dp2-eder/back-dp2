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


def test_list_categorias_success(
    test_client,
    mock_db_session_dependency,
    mock_categoria_service,
    sample_categoria_data,
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
