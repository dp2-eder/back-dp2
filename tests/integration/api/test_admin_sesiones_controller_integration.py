"""
Tests de integración para admin_sesiones_controller.
"""

import pytest
from datetime import datetime, timedelta
from ulid import ULID

from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.models.mesas.mesa_model import MesaModel
from src.models.auth.usuario_model import UsuarioModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository


@pytest.mark.asyncio
async def test_get_estado_sesiones_sin_duplicados(async_client, db_session):
    """
    Prueba de integración para obtener estado de sesiones sin duplicados.
    
    PRECONDICIONES:
        - Cliente async configurado
        - Base de datos limpia
        - 2 mesas con 1 sesión activa cada una
        
    PROCESO:
        - Crea mesas y usuarios
        - Crea 1 sesión activa por mesa
        - Hace GET al endpoint de estado
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - total_mesas = 2
        - mesas_con_duplicados = 0
    """
    # Arrange - Crear usuarios
    usuario1 = UsuarioModel(
        email="usuario1@test.com",
        nombre="Usuario 1"
    )
    usuario2 = UsuarioModel(
        email="usuario2@test.com",
        nombre="Usuario 2"
    )
    db_session.add(usuario1)
    db_session.add(usuario2)
    await db_session.flush()
    
    # Crear mesas
    mesa1 = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa 1"
    )
    mesa2 = MesaModel(
        numero=2,
        capacidad=4,
        descripcion="Mesa 2"
    )
    db_session.add(mesa1)
    db_session.add(mesa2)
    await db_session.flush()
    
    # Crear sesiones activas
    sesion1 = SesionMesaModel(
        id_mesa=mesa1.id,
        id_usuario_creador=usuario1.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        duracion_minutos=120
    )
    sesion2 = SesionMesaModel(
        id_mesa=mesa2.id,
        id_usuario_creador=usuario2.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        duracion_minutos=120
    )
    db_session.add(sesion1)
    db_session.add(sesion2)
    await db_session.commit()
    
    # Act
    response = await async_client.get("/api/v1/admin/sesiones/estado")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["total_sesiones_activas"] == 2
    assert data["total_mesas"] == 2
    assert data["mesas_con_duplicados"] == 0
    assert len(data["detalles_duplicados"]) == 0
    assert len(data["sesiones_por_mesa"]) == 2


@pytest.mark.asyncio
async def test_get_estado_sesiones_con_duplicados(async_client, db_session):
    """
    Prueba de integración para obtener estado con sesiones duplicadas.
    
    PRECONDICIONES:
        - Cliente async configurado
        - Base de datos limpia
        - 1 mesa con 3 sesiones activas (duplicados)
        
    PROCESO:
        - Crea mesa y usuario
        - Crea 3 sesiones activas para la misma mesa
        - Hace GET al endpoint de estado
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - mesas_con_duplicados = 1
        - detalles_duplicados contiene la mesa con 3 sesiones
    """
    # Arrange - Crear usuario
    usuario = UsuarioModel(
        email="usuario@test.com",
        nombre="Usuario Test"
    )
    db_session.add(usuario)
    await db_session.flush()
    
    # Crear mesa
    mesa = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa Test"
    )
    db_session.add(mesa)
    await db_session.flush()
    
    # Crear 3 sesiones activas (duplicados)
    sesion1 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=3),
        duracion_minutos=120
    )
    sesion2 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=1),
        duracion_minutos=120
    )
    sesion3 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now(),
        duracion_minutos=120
    )
    db_session.add(sesion1)
    db_session.add(sesion2)
    db_session.add(sesion3)
    await db_session.commit()
    
    # Act
    response = await async_client.get("/api/v1/admin/sesiones/estado")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["total_sesiones_activas"] == 3
    assert data["total_mesas"] == 1
    assert data["mesas_con_duplicados"] == 1
    assert len(data["detalles_duplicados"]) == 1
    assert data["detalles_duplicados"][0]["sesiones_activas"] == 3


@pytest.mark.asyncio
async def test_fix_duplicate_sessions_sin_duplicados(async_client, db_session):
    """
    Prueba de integración para corregir sesiones cuando no hay duplicados.
    
    PRECONDICIONES:
        - Cliente async configurado
        - Base de datos con sesiones únicas por mesa
        
    PROCESO:
        - Hace POST al endpoint de corrección
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - success = True
        - mesas_procesadas = 0
        - sesiones_finalizadas = 0
    """
    # Arrange - Crear usuario y mesa con 1 sesión
    usuario = UsuarioModel(
        email="usuario@test.com",
        nombre="Usuario Test"
    )
    db_session.add(usuario)
    await db_session.flush()
    
    mesa = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa Test"
    )
    db_session.add(mesa)
    await db_session.flush()
    
    sesion = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        duracion_minutos=120
    )
    db_session.add(sesion)
    await db_session.commit()
    
    # Act
    response = await async_client.post("/api/v1/admin/sesiones/fix-duplicates")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["success"] is True
    assert data["mesas_procesadas"] == 0
    assert data["sesiones_finalizadas"] == 0


@pytest.mark.asyncio
async def test_fix_duplicate_sessions_con_duplicados(async_client, db_session):
    """
    Prueba de integración para corregir sesiones duplicadas.
    
    PRECONDICIONES:
        - Cliente async configurado
        - 1 mesa con 3 sesiones activas
        
    PROCESO:
        - Hace POST al endpoint de corrección
        - Verifica que solo quede 1 sesión activa
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - success = True
        - mesas_procesadas = 1
        - sesiones_finalizadas = 2
        - Solo la sesión más reciente queda activa
    """
    # Arrange - Crear usuario y mesa
    usuario = UsuarioModel(
        email="usuario@test.com",
        nombre="Usuario Test"
    )
    db_session.add(usuario)
    await db_session.flush()
    
    mesa = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa Test"
    )
    db_session.add(mesa)
    await db_session.flush()
    
    # Crear 3 sesiones duplicadas
    sesion1 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=3),
        duracion_minutos=120
    )
    sesion2 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=1),
        duracion_minutos=120
    )
    sesion3 = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now(),
        duracion_minutos=120
    )
    db_session.add(sesion1)
    db_session.add(sesion2)
    db_session.add(sesion3)
    await db_session.commit()
    
    sesion3_id = sesion3.id
    
    # Act
    response = await async_client.post("/api/v1/admin/sesiones/fix-duplicates")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["success"] is True
    assert data["mesas_procesadas"] == 1
    assert data["sesiones_finalizadas"] == 2
    assert data["sesiones_mantenidas"] == 1
    
    # Verificar en base de datos
    repo = SesionMesaRepository(db_session)
    sesion_activa = await repo.get_active_by_mesa(mesa.id)
    assert sesion_activa is not None
    assert sesion_activa.id == sesion3_id
    assert sesion_activa.estado == EstadoSesionMesa.ACTIVA


@pytest.mark.asyncio
async def test_finalizar_sesiones_expiradas_sin_expiradas(async_client, db_session):
    """
    Prueba de integración para finalizar sesiones cuando no hay expiradas.
    
    PRECONDICIONES:
        - Cliente async configurado
        - Sesiones activas válidas (no expiradas)
        
    PROCESO:
        - Hace POST al endpoint de finalizar expiradas
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - success = True
        - sesiones_finalizadas = 0
    """
    # Arrange - Crear sesión válida
    usuario = UsuarioModel(
        email="usuario@test.com",
        nombre="Usuario Test"
    )
    db_session.add(usuario)
    await db_session.flush()
    
    mesa = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa Test"
    )
    db_session.add(mesa)
    await db_session.flush()
    
    sesion = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(minutes=30),
        duracion_minutos=120
    )
    db_session.add(sesion)
    await db_session.commit()
    
    # Act
    response = await async_client.post("/api/v1/admin/sesiones/finalizar-expiradas")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["success"] is True
    assert data["sesiones_finalizadas"] == 0


@pytest.mark.asyncio
async def test_finalizar_sesiones_expiradas_con_expiradas(async_client, db_session):
    """
    Prueba de integración para finalizar sesiones expiradas.
    
    PRECONDICIONES:
        - Cliente async configurado
        - Sesiones activas expiradas
        
    PROCESO:
        - Hace POST al endpoint de finalizar expiradas
        - Verifica que las sesiones expiradas cambien a FINALIZADA
        
    POSTCONDICIONES:
        - Respuesta HTTP 200
        - success = True
        - sesiones_finalizadas > 0
        - Sesiones expiradas tienen estado FINALIZADA en BD
    """
    # Arrange - Crear sesión expirada
    usuario = UsuarioModel(
        email="usuario@test.com",
        nombre="Usuario Test"
    )
    db_session.add(usuario)
    await db_session.flush()
    
    mesa = MesaModel(
        numero=1,
        capacidad=4,
        descripcion="Mesa Test"
    )
    db_session.add(mesa)
    await db_session.flush()
    
    sesion_expirada = SesionMesaModel(
        id_mesa=mesa.id,
        id_usuario_creador=usuario.id,
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=3),
        duracion_minutos=120
    )
    db_session.add(sesion_expirada)
    await db_session.commit()
    
    sesion_id = sesion_expirada.id
    
    # Act
    response = await async_client.post("/api/v1/admin/sesiones/finalizar-expiradas")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["success"] is True
    assert data["sesiones_finalizadas"] == 1
    
    # Verificar en base de datos
    repo = SesionMesaRepository(db_session)
    sesion = await repo.get_by_id(sesion_id)
    assert sesion is not None
    assert sesion.estado == EstadoSesionMesa.FINALIZADA
    assert sesion.fecha_fin is not None
