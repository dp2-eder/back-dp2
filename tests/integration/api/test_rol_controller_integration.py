"""
Pruebas de integración para el controlador de roles.

ARCHIVO DESHABILITADO PERMANENTEMENTE
======================================
Este archivo de test ha sido deshabilitado porque RolController fue eliminado del sistema.

El nuevo sistema de login simplificado no usa roles.
"""

import pytest
from ulid import ULID
from src.models.auth.rol_model import RolModel
from src.models.auth.usuario_model import UsuarioModel
from src.repositories.auth.rol_repository import RolRepository
from src.repositories.auth.usuario_repository import UsuarioRepository


@pytest.mark.asyncio
async def test_get_nombre_rol_usuario_integration(async_client, db_session):
    """
    Prueba de integración para obtener el nombre del rol de un usuario.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible y en estado limpio
        - Los modelos RolModel y UsuarioModel deben ser accesibles
    
    PROCESO:
        - Crea un rol directamente en la base de datos.
        - Crea un usuario con ese rol.
        - Envía una solicitud GET al endpoint.
        - Verifica la respuesta completa.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 200 (OK)
        - Los datos devueltos deben incluir el nombre del rol correcto
    """
    # Arrange - Create a rol in DB
    rol = RolModel(
        id=str(ULID()),
        nombre="COMENSAL_TEST",
        descripcion="Rol de prueba para comensales",
        activo=True
    )
    db_session.add(rol)
    await db_session.commit()

    # Create a usuario with that rol
    usuario = UsuarioModel(
        id=str(ULID()),
        nombre="Usuario Test",
        email="test@example.com",
        password="hashedpassword123",
        id_rol=rol.id,
        activo=True
    )
    db_session.add(usuario)
    await db_session.commit()

    # Act
    response = await async_client.get(f"/api/v1/roles/usuario/{usuario.id}/nombre")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "nombre_rol" in response_data
    assert response_data["nombre_rol"] == "COMENSAL_TEST"


@pytest.mark.asyncio
async def test_get_nombre_rol_usuario_not_found_integration(async_client, db_session):
    """
    Prueba de integración para obtener el rol de un usuario inexistente.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible
    
    PROCESO:
        - Genera un ID de usuario que no existe en la base de datos.
        - Envía una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que no se encontró el usuario
    """
    # Arrange
    usuario_id_inexistente = str(ULID())

    # Act
    response = await async_client.get(f"/api/v1/roles/usuario/{usuario_id_inexistente}/nombre")

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    assert "No se encontró el usuario" in response_data["detail"]


@pytest.mark.asyncio
async def test_get_nombre_rol_usuario_sin_rol_integration(async_client, db_session):
    """
    Prueba de integración para obtener el rol de un usuario sin rol asignado.
    
    PRECONDICIONES:
        - El cliente asincrónico (async_client) debe estar configurado
        - La sesión de base de datos (db_session) debe estar disponible
    
    PROCESO:
        - Crea un usuario sin rol asignado.
        - Envía una solicitud GET al endpoint.
        - Verifica que se retorne el código de error apropiado.
        
    POSTCONDICIONES:
        - La respuesta debe tener código HTTP 404 (Not Found)
        - El mensaje de error debe indicar que el usuario no tiene rol asignado
    """
    # Arrange - Create a usuario without rol
    usuario = UsuarioModel(
        id=str(ULID()),
        nombre="Usuario Sin Rol",
        email="sinrol@example.com",
        password="hashedpassword456",
        id_rol=None,
        activo=True
    )
    db_session.add(usuario)
    await db_session.commit()

    # Act
    response = await async_client.get(f"/api/v1/roles/usuario/{usuario.id}/nombre")

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert "detail" in response_data
    assert "no tiene un rol asignado" in response_data["detail"]
