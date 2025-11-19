"""
Pruebas unitarias para los endpoints de relaciones producto-alérgeno.
"""

import pytest
from ulid import ULID
from unittest.mock import AsyncMock, patch
from datetime import datetime
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.controllers.producto_alergeno_controller import router, get_database_session
from src.business_logic.menu.producto_alergeno_service import ProductoAlergenoService
from src.business_logic.exceptions.producto_alergeno_exceptions import (
    ProductoAlergenoNotFoundError,
    ProductoAlergenoConflictError,
    ProductoAlergenoValidationError,
)
from src.api.schemas.producto_alergeno_schema import ProductoAlergenoResponse, ProductoAlergenoList
from src.core.enums.alergeno_enums import NivelPresencia

app = FastAPI()
app.include_router(router, prefix="/api/v1")


# Mock de sesión de base de datos para pruebas unitarias usando el fixture global
@pytest.fixture
def mock_db_session_dependency(async_mock_db_session, cleanup_app):
    """
    Sobrescribe la dependencia de base de datos en el router.
    
    PRECONDICIONES:
        - El fixture async_mock_db_session debe estar disponible
        - La aplicación FastAPI debe estar configurada
    
    PROCESO:
        - Reemplaza la dependencia get_database_session con un mock
    
    POSTCONDICIONES:
        - El router utilizará la sesión mockeada en lugar de la real
    """
    app.dependency_overrides[get_database_session] = lambda: async_mock_db_session
    yield async_mock_db_session
    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    """
    Crea un cliente de prueba para la aplicación FastAPI.
    
    PRECONDICIONES:
        - La aplicación FastAPI debe estar configurada con el router
    
    PROCESO:
        - Crea un TestClient con la aplicación
    
    POSTCONDICIONES:
        - Se retorna un cliente listo para realizar peticiones HTTP
    """
    return TestClient(app)


@pytest.fixture
def mock_producto_alergeno_service():
    """
    Crea un mock del servicio de relaciones producto-alérgeno.
    
    PRECONDICIONES:
        - None
    
    PROCESO:
        - Crea un AsyncMock del servicio con todos los métodos necesarios
    
    POSTCONDICIONES:
        - Se retorna un mock que puede ser configurado para las pruebas
    """
    service = AsyncMock(spec=ProductoAlergenoService)
    return service


@pytest.fixture
def sample_producto_id():
    """ID de producto de ejemplo para las pruebas."""
    return "12345678-1234-5678-1234-567812345678"  # UUID v4 string (backward compatible)


@pytest.fixture
def sample_alergeno_id():
    """ID de alérgeno de ejemplo para las pruebas."""
    return "87654321-4321-8765-4321-876543218765"  # UUID v4 string (backward compatible)


@pytest.fixture
def sample_producto_alergeno_data(sample_producto_id, sample_alergeno_id):
    """Datos de ejemplo de una relación producto-alérgeno para las pruebas."""
    return {
        "id": str(ULID()),  # ID único de la relación
        "id_producto": str(sample_producto_id),
        "id_alergeno": str(sample_alergeno_id),
        "nivel_presencia": NivelPresencia.CONTIENE.value,
        "notas": "Contiene trazas de frutos secos",
        "activo": True,
        "fecha_creacion": datetime.now().isoformat(),
        "fecha_modificacion": datetime.now().isoformat(),
    }


def test_create_producto_alergeno_success(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service, 
    sample_producto_id, sample_alergeno_id, sample_producto_alergeno_data
):
    """
    Prueba la creación exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Los datos de muestra deben estar disponibles (sample_producto_alergeno_data)

    PROCESO:
        - Configura el mock para simular una creación exitosa.
        - Realiza una solicitud POST al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 201 (Created)
        - Los datos devueltos deben coincidir con los proporcionados
        - El método create_producto_alergeno del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_alergeno_data = {
        "id_producto": str(sample_producto_id),
        "id_alergeno": str(sample_alergeno_id),
        "nivel_presencia": NivelPresencia.CONTIENE.value,
        "notas": "Contiene trazas de frutos secos",
    }
    
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.create_producto_alergeno.return_value = (
            ProductoAlergenoResponse(**sample_producto_alergeno_data)
        )

        # Act
        response = test_client.post("/api/v1/productos-alergenos", json=producto_alergeno_data)

        # Assert
        assert response.status_code == 201
        assert response.json()["id_producto"] == sample_producto_alergeno_data["id_producto"]
        assert response.json()["id_alergeno"] == sample_producto_alergeno_data["id_alergeno"]
        assert response.json()["nivel_presencia"] == sample_producto_alergeno_data["nivel_presencia"]
        mock_producto_alergeno_service.create_producto_alergeno.assert_awaited_once()


def test_create_producto_alergeno_conflict(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba el manejo de errores al crear una relación producto-alérgeno duplicada.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)

    PROCESO:
        - Configura el mock para simular un error de conflicto.
        - Realiza una solicitud POST al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 409 (Conflict)
        - El mensaje de error debe indicar la duplicidad de la relación
        - El método create_producto_alergeno del servicio debe haber sido llamado una vez
    """
    # Arrange
    producto_alergeno_data = {
        "id_producto": str(sample_producto_id),
        "id_alergeno": str(sample_alergeno_id),
        "nivel_presencia": NivelPresencia.CONTIENE.value,
        "notas": "Contiene trazas de frutos secos",
    }
    
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.create_producto_alergeno.side_effect = (
            ProductoAlergenoConflictError(
                f"Ya existe una relación entre el producto {sample_producto_id} "
                f"y el alérgeno {sample_alergeno_id}"
            )
        )

        # Act
        response = test_client.post("/api/v1/productos-alergenos", json=producto_alergeno_data)

        # Assert
        assert response.status_code == 409
        assert "Ya existe una relación" in response.json()["detail"]
        mock_producto_alergeno_service.create_producto_alergeno.assert_awaited_once()


def test_get_producto_alergeno_success(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id, sample_producto_alergeno_data
):
    """
    Prueba la obtención exitosa de una relación producto-alérgeno por combinación de IDs.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Los datos de muestra deben estar disponibles (sample_producto_alergeno_data)

    PROCESO:
        - Configura el mock para simular la existencia de una relación.
        - Realiza una solicitud GET al endpoint con id_producto e id_alergeno.
        - Verifica la respuesta HTTP y los datos retornados.

    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben coincidir con los esperados
        - El método get_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.get_producto_alergeno_by_combination.return_value = (
            ProductoAlergenoResponse(**sample_producto_alergeno_data)
        )

        # Act
        response = test_client.get(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}"
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["id_producto"] == sample_producto_alergeno_data["id_producto"]
        assert response.json()["id_alergeno"] == sample_producto_alergeno_data["id_alergeno"]
        mock_producto_alergeno_service.get_producto_alergeno_by_combination.assert_awaited_once()


def test_get_producto_alergeno_not_found(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba el manejo de errores al buscar una relación producto-alérgeno que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Se deben tener IDs válidos (sample_producto_id, sample_alergeno_id)

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Realiza una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la relación
        - El método get_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.get_producto_alergeno_by_combination.side_effect = (
            ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {sample_producto_id} "
                f"y alérgeno {sample_alergeno_id}"
            )
        )

        # Act
        response = test_client.get(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}"
        )

        # Assert
        assert response.status_code == 404
        assert "No se encontró la relación" in response.json()["detail"]
        mock_producto_alergeno_service.get_producto_alergeno_by_combination.assert_awaited_once()


def test_list_producto_alergenos_success(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba la obtención exitosa de una lista de relaciones producto-alérgeno.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)

    PROCESO:
        - Configura el mock para simular una lista de relaciones.
        - Realiza una solicitud GET al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - La respuesta debe incluir una lista de relaciones y el total
        - El método get_producto_alergenos del servicio debe haber sido llamado con los parámetros correctos
    """
    # Arrange
    producto_alergeno_summary = {
        "id": str(ULID()),  # Agregar el campo id requerido
        "id_producto": str(sample_producto_id),
        "id_alergeno": str(sample_alergeno_id),
        "nivel_presencia": NivelPresencia.CONTIENE.value,
        "activo": True,
    }
    producto_alergeno_list = {
        "items": [producto_alergeno_summary, producto_alergeno_summary],
        "total": 2
    }
    
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.get_producto_alergenos.return_value = (
            ProductoAlergenoList(**producto_alergeno_list)
        )

        # Act
        response = test_client.get("/api/v1/productos-alergenos?skip=0&limit=10")

        # Assert
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert len(response.json()["items"]) == 2
        mock_producto_alergeno_service.get_producto_alergenos.assert_awaited_once_with(0, 10)


def test_list_producto_alergenos_validation_error(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service
):
    """
    Prueba el manejo de errores de validación en los parámetros de paginación.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)

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
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.get_producto_alergenos.side_effect = (
            ProductoAlergenoValidationError("El parámetro 'limit' debe ser mayor a cero")
        )

        # Act
        response = test_client.get("/api/v1/productos-alergenos?skip=0&limit=0")

        # Assert
        # FastAPI valida automáticamente los parámetros y devuelve 422 para errores de validación
        assert response.status_code == 422
        # Verificamos que el error esté relacionado con el parámetro limit
        error_detail = response.json()["detail"]
        assert any("limit" in str(err).lower() for err in error_detail)
        # No debe llamar al servicio porque la validación falla antes
        mock_producto_alergeno_service.get_producto_alergenos.assert_not_called()


def test_update_producto_alergeno_success(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id, sample_producto_alergeno_data
):
    """
    Prueba la actualización exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Se deben tener IDs válidos (sample_producto_id, sample_alergeno_id)
        - Los datos de muestra deben estar disponibles (sample_producto_alergeno_data)

    PROCESO:
        - Configura el mock para simular una actualización exitosa.
        - Realiza una solicitud PUT al endpoint.
        - Verifica la respuesta HTTP y los datos retornados.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben reflejar los cambios realizados
        - El método update_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nivel_presencia": NivelPresencia.TRAZAS.value}
    updated_data = {**sample_producto_alergeno_data, "nivel_presencia": NivelPresencia.TRAZAS.value}

    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.update_producto_alergeno_by_combination.return_value = (
            ProductoAlergenoResponse(**updated_data)
        )

        # Act
        response = test_client.put(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["nivel_presencia"] == NivelPresencia.TRAZAS.value
        mock_producto_alergeno_service.update_producto_alergeno_by_combination.assert_awaited_once()


def test_update_producto_alergeno_not_found(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba el manejo de errores al actualizar una relación producto-alérgeno que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Se deben tener IDs válidos (sample_producto_id, sample_alergeno_id)

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Realiza una solicitud PUT al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la relación
        - El método update_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    update_data = {"nivel_presencia": NivelPresencia.TRAZAS.value}

    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.update_producto_alergeno_by_combination.side_effect = (
            ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {sample_producto_id} "
                f"y alérgeno {sample_alergeno_id}"
            )
        )

        # Act
        response = test_client.put(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 404
        assert "No se encontró la relación" in response.json()["detail"]
        mock_producto_alergeno_service.update_producto_alergeno_by_combination.assert_awaited_once()


def test_delete_producto_alergeno_success(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba la eliminación exitosa de una relación producto-alérgeno.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Se deben tener IDs válidos (sample_producto_id, sample_alergeno_id)

    PROCESO:
        - Configura el mock para simular una eliminación exitosa.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica la respuesta HTTP.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 204 (No Content)
        - El método delete_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.delete_producto_alergeno_by_combination.return_value = None

        # Act
        response = test_client.delete(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}"
        )

        # Assert
        assert response.status_code == 204
        mock_producto_alergeno_service.delete_producto_alergeno_by_combination.assert_awaited_once()


def test_delete_producto_alergeno_not_found(
    test_client, mock_db_session_dependency, mock_producto_alergeno_service,
    sample_producto_id, sample_alergeno_id
):
    """
    Prueba el manejo de errores al eliminar una relación producto-alérgeno que no existe.

    PRECONDICIONES:
        - El cliente de prueba (test_client) debe estar configurado
        - El servicio de producto-alérgeno debe estar mockeado (mock_producto_alergeno_service)
        - Se deben tener IDs válidos (sample_producto_id, sample_alergeno_id)

    PROCESO:
        - Configura el mock para simular que la relación no existe.
        - Realiza una solicitud DELETE al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró la relación
        - El método delete_producto_alergeno_by_combination del servicio debe haber sido llamado una vez
    """
    # Arrange
    with patch(
        "src.api.controllers.producto_alergeno_controller.ProductoAlergenoService"
    ) as mock_service_class:
        mock_service_class.return_value = mock_producto_alergeno_service
        mock_producto_alergeno_service.delete_producto_alergeno_by_combination.side_effect = (
            ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {sample_producto_id} "
                f"y alérgeno {sample_alergeno_id}"
            )
        )

        # Act
        response = test_client.delete(
            f"/api/v1/productos-alergenos/{sample_producto_id}/{sample_alergeno_id}"
        )

        # Assert
        assert response.status_code == 404
        assert "No se encontró la relación" in response.json()["detail"]
        mock_producto_alergeno_service.delete_producto_alergeno_by_combination.assert_awaited_once()
