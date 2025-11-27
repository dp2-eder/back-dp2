"""
Tests de integración para el controlador de login.

Verifica que el endpoint de login maneje correctamente:
- Mesa no encontrada (404)
- Mesa inactiva (404)
- Errores de validación (400)
- Login exitoso (200)
"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.models.mesas.mesa_model import MesaModel


@pytest.mark.asyncio
class TestLoginControllerIntegration:
    """Tests de integración para el endpoint POST /api/v1/login."""

    async def test_login_mesa_no_existe_retorna_404(self, db_session, async_client):
        """
        Test: Login con ID de mesa que no existe retorna HTTP 404.
        
        Verifica que:
        - El status code sea 404
        - El detalle incluya código MESA_NOT_FOUND
        """
        # Arrange
        login_data = {
            "email": "test@correo.com",
            "nombre": "Test Usuario"
        }

        # Act
        response = await async_client.post(
            "/api/v1/login",
            json=login_data,
            params={"id_mesa": "ID_INEXISTENTE_12345"}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "MESA_NOT_FOUND"

    async def test_login_mesa_inactiva_retorna_404(self, db_session, async_client):
        """
        Test: Login con mesa inactiva retorna HTTP 404.
        
        Verifica que:
        - El status code sea 404
        - El detalle incluya código MESA_INACTIVE
        """
        # Arrange
        mesa_inactiva = MesaModel(numero=88, capacidad=4, activo=False)
        db_session.add(mesa_inactiva)
        await db_session.commit()
        await db_session.refresh(mesa_inactiva)

        login_data = {
            "email": "test@correo.com",
            "nombre": "Test Usuario"
        }

        # Act
        response = await async_client.post(
            "/api/v1/login",
            json=login_data,
            params={"id_mesa": mesa_inactiva.id}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "MESA_INACTIVE"

    async def test_login_email_invalido_retorna_422(self, db_session, async_client):
        """
        Test: Login con email inválido retorna HTTP 422 (validación Pydantic).
        """
        # Arrange
        mesa = MesaModel(numero=89, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_data = {
            "email": "texto_sin_formato_valido",  # No contiene @, correo, ni mail
            "nombre": "Test Usuario"
        }

        # Act
        response = await async_client.post(
            "/api/v1/login",
            json=login_data,
            params={"id_mesa": mesa.id}
        )

        # Assert
        assert response.status_code == 422  # Validación de Pydantic

    async def test_login_exitoso_retorna_200(self, db_session, async_client):
        """
        Test: Login exitoso retorna HTTP 200 con datos de sesión.
        """
        # Arrange
        mesa = MesaModel(numero=90, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        login_data = {
            "email": "test@correo.com",
            "nombre": "Test Usuario"
        }

        # Act
        response = await async_client.post(
            "/api/v1/login",
            json=login_data,
            params={"id_mesa": mesa.id}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["code"] == "SUCCESS"
        assert "id_usuario" in data
        assert "id_sesion_mesa" in data
        assert "token_sesion" in data
        assert "fecha_expiracion" in data

    async def test_login_dos_usuarios_misma_mesa_comparten_token(
        self, db_session, async_client
    ):
        """
        Test: Dos usuarios en la misma mesa comparten el mismo token.
        """
        # Arrange
        mesa = MesaModel(numero=91, capacidad=4)
        db_session.add(mesa)
        await db_session.commit()
        await db_session.refresh(mesa)

        # Act
        response1 = await async_client.post(
            "/api/v1/login",
            json={"email": "user1@correo.com", "nombre": "Usuario 1"},
            params={"id_mesa": mesa.id}
        )

        response2 = await async_client.post(
            "/api/v1/login",
            json={"email": "user2@correo.com", "nombre": "Usuario 2"},
            params={"id_mesa": mesa.id}
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Mismo token y sesión
        assert data1["token_sesion"] == data2["token_sesion"]
        assert data1["id_sesion_mesa"] == data2["id_sesion_mesa"]
        # Diferentes usuarios
        assert data1["id_usuario"] != data2["id_usuario"]
