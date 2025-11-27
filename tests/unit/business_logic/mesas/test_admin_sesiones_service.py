"""
Tests unitarios para AdminSesionesService.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from ulid import ULID

from src.business_logic.mesas.admin_sesiones_service import AdminSesionesService
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa


@pytest.fixture
def mock_session():
    """Fixture para mock de sesión de base de datos."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_repository(mocker):
    """Fixture para mock del repositorio."""
    return mocker.patch('src.business_logic.mesas.admin_sesiones_service.SesionMesaRepository')


@pytest.fixture
def service(mock_session):
    """Fixture para instancia del servicio."""
    return AdminSesionesService(mock_session)


@pytest.mark.asyncio
async def test_get_estado_sesiones_sin_duplicados(service, mock_session):
    """
    Verifica que get_estado_sesiones retorne correctamente cuando no hay duplicados.
    
    PRECONDICIONES:
        - Servicio inicializado con sesión mock
        - Base de datos con 2 mesas, cada una con 1 sesión activa
        
    PROCESO:
        - Ejecuta método get_estado_sesiones
        
    POSTCONDICIONES:
        - Retorna total_sesiones_activas = 2
        - Retorna total_mesas = 2
        - Retorna mesas_con_duplicados = 0
        - Lista de detalles_duplicados está vacía
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(id_mesa=str(ULID()), count=1),
        MagicMock(id_mesa=str(ULID()), count=1),
    ]
    mock_session.execute.return_value = mock_result
    
    # Act
    resultado = await service.get_estado_sesiones()
    
    # Assert
    assert resultado["total_sesiones_activas"] == 2
    assert resultado["total_mesas"] == 2
    assert resultado["mesas_con_duplicados"] == 0
    assert len(resultado["detalles_duplicados"]) == 0
    assert len(resultado["sesiones_por_mesa"]) == 2


@pytest.mark.asyncio
async def test_get_estado_sesiones_con_duplicados(service, mock_session):
    """
    Verifica que get_estado_sesiones identifique correctamente las mesas con duplicados.
    
    PRECONDICIONES:
        - Servicio inicializado con sesión mock
        - Base de datos con 1 mesa con 3 sesiones activas (duplicados)
        
    PROCESO:
        - Ejecuta método get_estado_sesiones
        
    POSTCONDICIONES:
        - Retorna mesas_con_duplicados = 1
        - detalles_duplicados contiene la mesa con 3 sesiones
    """
    # Arrange
    id_mesa_duplicada = str(ULID())
    mock_result = MagicMock()
    mock_result.all.return_value = [
        MagicMock(id_mesa=id_mesa_duplicada, count=3),
    ]
    mock_session.execute.return_value = mock_result
    
    # Act
    resultado = await service.get_estado_sesiones()
    
    # Assert
    assert resultado["total_sesiones_activas"] == 3
    assert resultado["total_mesas"] == 1
    assert resultado["mesas_con_duplicados"] == 1
    assert len(resultado["detalles_duplicados"]) == 1
    assert resultado["detalles_duplicados"][0]["id_mesa"] == id_mesa_duplicada
    assert resultado["detalles_duplicados"][0]["sesiones_activas"] == 3


@pytest.mark.asyncio
async def test_fix_duplicate_active_sessions_sin_duplicados(service, mock_session):
    """
    Verifica que fix_duplicate_active_sessions maneje correctamente cuando no hay duplicados.
    
    PRECONDICIONES:
        - Servicio inicializado
        - No hay mesas con sesiones duplicadas
        
    PROCESO:
        - Ejecuta método fix_duplicate_active_sessions
        
    POSTCONDICIONES:
        - Retorna success = True
        - Retorna mesas_procesadas = 0
        - Retorna sesiones_finalizadas = 0
    """
    # Arrange
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    # Act
    resultado = await service.fix_duplicate_active_sessions()
    
    # Assert
    assert resultado["success"] is True
    assert resultado["mesas_procesadas"] == 0
    assert resultado["sesiones_finalizadas"] == 0
    assert len(resultado["detalles"]) == 0


@pytest.mark.asyncio
async def test_fix_duplicate_active_sessions_con_duplicados(service, mock_session):
    """
    Verifica que fix_duplicate_active_sessions corrija correctamente sesiones duplicadas.
    
    PRECONDICIONES:
        - Servicio inicializado
        - 1 mesa con 3 sesiones activas
        
    PROCESO:
        - Ejecuta método fix_duplicate_active_sessions
        - Debe mantener la sesión más reciente
        - Debe finalizar las 2 sesiones más antiguas
        
    POSTCONDICIONES:
        - Retorna success = True
        - Retorna mesas_procesadas = 1
        - Retorna sesiones_finalizadas = 2
        - Retorna sesiones_mantenidas = 1
    """
    # Arrange
    id_mesa = str(ULID())
    
    # Mock para la primera consulta (contar duplicados)
    mock_count_result = MagicMock()
    mock_count_result.all.return_value = [
        MagicMock(id_mesa=id_mesa, count=3)
    ]
    
    # Crear sesiones mock
    sesion1 = SesionMesaModel(
        id_mesa=id_mesa,
        id_usuario_creador=str(ULID()),
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=3),
        duracion_minutos=120
    )
    sesion2 = SesionMesaModel(
        id_mesa=id_mesa,
        id_usuario_creador=str(ULID()),
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=1),
        duracion_minutos=120
    )
    sesion3 = SesionMesaModel(
        id_mesa=id_mesa,
        id_usuario_creador=str(ULID()),
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now(),
        duracion_minutos=120
    )
    
    # Mock para la segunda consulta (obtener sesiones)
    mock_sesiones_result = MagicMock()
    mock_sesiones_result.scalars.return_value.all.return_value = [sesion3, sesion2, sesion1]
    
    # Configurar el mock para retornar diferentes resultados
    mock_session.execute.side_effect = [mock_count_result, mock_sesiones_result]
    
    # Act
    resultado = await service.fix_duplicate_active_sessions()
    
    # Assert
    assert resultado["success"] is True
    assert resultado["mesas_procesadas"] == 1
    assert resultado["sesiones_finalizadas"] == 2
    assert resultado["sesiones_mantenidas"] == 1
    assert len(resultado["detalles"]) == 1
    
    # Verificar que las sesiones antiguas fueron marcadas como finalizadas
    assert sesion1.estado == EstadoSesionMesa.FINALIZADA
    assert sesion2.estado == EstadoSesionMesa.FINALIZADA
    assert sesion3.estado == EstadoSesionMesa.ACTIVA
    
    # Verificar commit
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_finalizar_sesiones_expiradas_sin_expiradas(service, mock_session):
    """
    Verifica que finalizar_sesiones_expiradas maneje correctamente cuando no hay expiradas.
    
    PRECONDICIONES:
        - Servicio inicializado
        - Hay sesiones activas pero ninguna expirada
        
    PROCESO:
        - Ejecuta método finalizar_sesiones_expiradas
        
    POSTCONDICIONES:
        - Retorna success = True
        - Retorna sesiones_finalizadas = 0
    """
    # Arrange
    sesion_valida = SesionMesaModel(
        id_mesa=str(ULID()),
        id_usuario_creador=str(ULID()),
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(minutes=30),
        duracion_minutos=120
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sesion_valida]
    mock_session.execute.return_value = mock_result
    
    # Act
    resultado = await service.finalizar_sesiones_expiradas()
    
    # Assert
    assert resultado["success"] is True
    assert resultado["sesiones_finalizadas"] == 0
    assert len(resultado["detalles"]) == 0


@pytest.mark.asyncio
async def test_finalizar_sesiones_expiradas_con_expiradas(service, mock_session):
    """
    Verifica que finalizar_sesiones_expiradas finalice correctamente sesiones expiradas.
    
    PRECONDICIONES:
        - Servicio inicializado
        - Hay sesiones activas expiradas
        
    PROCESO:
        - Ejecuta método finalizar_sesiones_expiradas
        
    POSTCONDICIONES:
        - Retorna success = True
        - Retorna sesiones_finalizadas > 0
        - Las sesiones expiradas cambian a estado FINALIZADA
    """
    # Arrange
    sesion_expirada = SesionMesaModel(
        id_mesa=str(ULID()),
        id_usuario_creador=str(ULID()),
        token_sesion=str(ULID()),
        estado=EstadoSesionMesa.ACTIVA,
        fecha_inicio=datetime.now() - timedelta(hours=3),
        duracion_minutos=120
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sesion_expirada]
    mock_session.execute.return_value = mock_result
    
    # Act
    resultado = await service.finalizar_sesiones_expiradas()
    
    # Assert
    assert resultado["success"] is True
    assert resultado["sesiones_finalizadas"] == 1
    assert len(resultado["detalles"]) == 1
    assert sesion_expirada.estado == EstadoSesionMesa.FINALIZADA
    assert sesion_expirada.fecha_fin is not None
    mock_session.commit.assert_called_once()
