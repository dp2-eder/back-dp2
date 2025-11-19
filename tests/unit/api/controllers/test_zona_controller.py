"""
Pruebas unitarias para el controlador de zonas.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from ulid import ULID
from datetime import datetime

from src.main import app
from src.models.mesas.zona_model import ZonaModel
from src.models.mesas.local_model import LocalModel
from src.api.schemas.zona_schema import ZonaResponse, ZonaList, LocalInfo
from src.business_logic.exceptions.zona_exceptions import (
    ZonaValidationError,
    ZonaNotFoundError,
    ZonaConflictError,
)


@pytest.fixture
def sample_local():
    """Fixture con datos de muestra para un local."""
    return LocalModel(
        id=str(ULID()),
        codigo="CEV-001",
        nombre="Local Test",
        direccion="Dir Test",
    )


@pytest.fixture
def sample_zona(sample_local):
    """Fixture con datos de muestra para una zona."""
    zona = ZonaModel(
        id=str(ULID()),
        id_local=sample_local.id,
        nombre="Terraza",
        descripcion="Zona de terraza con vista",
        nivel=0,
        capacidad_maxima=40,
        activo=True,
        fecha_creacion=datetime.now(),
        fecha_modificacion=datetime.now(),
    )
    zona.local = sample_local
    return zona


@pytest.mark.asyncio
async def test_create_zona_success(sample_zona, sample_local):
    """Prueba la creación exitosa de una zona."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.create_zona.return_value = sample_zona

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/zonas",
                json={
                    "id_local": sample_local.id,
                    "nombre": "Terraza",
                    "descripcion": "Zona de terraza con vista",
                    "nivel": 0,
                    "capacidad_maxima": 40,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Terraza"
        assert data["id_local"] == sample_local.id
        assert "local" in data


@pytest.mark.asyncio
async def test_create_zona_validation_error():
    """Prueba error de validación al crear zona."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.create_zona.side_effect = ZonaValidationError(
            "El local no existe"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/zonas",
                json={
                    "id_local": str(ULID()),
                    "nombre": "Terraza",
                    "nivel": 0,
                },
            )

        assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_zona_by_id_success(sample_zona):
    """Prueba la obtención exitosa de una zona por ID."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.get_zona_by_id.return_value = sample_zona

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/zonas/{sample_zona.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_zona.id
        assert data["nombre"] == "Terraza"


@pytest.mark.asyncio
async def test_get_zona_by_id_not_found():
    """Prueba error al obtener zona inexistente."""
    zona_id = str(ULID())
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.get_zona_by_id.side_effect = ZonaNotFoundError(
            f"Zona con ID '{zona_id}' no encontrada"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/zonas/{zona_id}")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_zonas_by_local_success(sample_zona, sample_local):
    """Prueba obtener zonas por local."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        zona_list = ZonaList(
            items=[sample_zona],
            total=1,
        )
        mock_service.get_zonas_by_local.return_value = zona_list

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/zonas/local/{sample_local.id}?skip=0&limit=10"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id_local"] == sample_local.id


@pytest.mark.asyncio
async def test_get_zonas_by_nivel_success(sample_zona):
    """Prueba obtener zonas por nivel."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        zona_list = ZonaList(
            items=[sample_zona],
            total=1,
        )
        mock_service.get_zonas_by_nivel.return_value = zona_list

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/zonas/nivel/0?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["nivel"] == 0


@pytest.mark.asyncio
async def test_get_all_zonas_success(sample_zona, sample_local):
    """Prueba la obtención de todas las zonas."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        zona_list = ZonaList(
            items=[sample_zona],
            total=1,
        )
        mock_service.get_zonas.return_value = zona_list

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
        ) as client:
            response = await client.get("/api/v1/zonas/?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_update_zona_success(sample_zona):
    """Prueba la actualización exitosa de una zona."""
    updated_zona = sample_zona
    updated_zona.nombre = "Terraza VIP"

    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.update_zona.return_value = updated_zona

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/v1/zonas/{sample_zona.id}",
                json={"nombre": "Terraza VIP"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Terraza VIP"


@pytest.mark.asyncio
async def test_update_zona_not_found():
    """Prueba error al actualizar zona inexistente."""
    zona_id = str(ULID())
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.update_zona.side_effect = ZonaNotFoundError(
            f"Zona con ID '{zona_id}' no encontrada"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.put(
                f"/api/v1/zonas/{zona_id}",
                json={"nombre": "Test"},
            )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_zona_success(sample_zona):
    """Prueba la eliminación exitosa de una zona."""
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.delete_zona.return_value = True

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/zonas/{sample_zona.id}")

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_zona_not_found():
    """Prueba error al eliminar zona inexistente."""
    zona_id = str(ULID())
    with patch(
        "src.api.controllers.zona_controller.ZonaService"
    ) as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service
        mock_service.delete_zona.side_effect = ZonaNotFoundError(
            f"Zona con ID '{zona_id}' no encontrada"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/v1/zonas/{zona_id}")

        assert response.status_code == 404
