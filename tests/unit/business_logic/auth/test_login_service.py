"""
Pruebas unitarias para LoginService.

Verifica la lógica de negocio del login simplificado,
incluyendo validación de mesa y manejo de sesiones expiradas.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError

from src.business_logic.auth.login_service import LoginService
from src.api.schemas.login_schema import LoginRequest, LoginResponse
from src.models.auth.usuario_model import UsuarioModel
from src.models.mesas.mesa_model import MesaModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.business_logic.exceptions.mesa_exceptions import MesaNotFoundError


@pytest.fixture
def mock_session():
    """Mock de AsyncSession."""
    return AsyncMock()


@pytest.fixture
def login_service(mock_session):
    """Crea una instancia de LoginService con mocks."""
    service = LoginService(mock_session)
    # Mockear los repositorios
    service.usuario_repository = AsyncMock()
    service.sesion_mesa_repository = AsyncMock()
    service.mesa_repository = AsyncMock()
    return service


@pytest.fixture
def valid_login_request():
    """Request de login válido."""
    return LoginRequest(
        email="test@correo.com",
        nombre="Test Usuario"
    )


@pytest.fixture
def mock_mesa():
    """Mock de una mesa activa."""
    mesa = MagicMock(spec=MesaModel)
    mesa.id = "01MESA123"
    mesa.numero = "5"
    mesa.activo = True
    return mesa


@pytest.fixture
def mock_usuario():
    """Mock de un usuario."""
    usuario = MagicMock(spec=UsuarioModel)
    usuario.id = "01USER123"
    usuario.email = "test@correo.com"
    usuario.nombre = "Test Usuario"
    return usuario


@pytest.fixture
def mock_usuario_existente():
    """Mock de un usuario existente (para cuando get_by_email lo encuentra)."""
    usuario = MagicMock(spec=UsuarioModel)
    usuario.id = "01USER123"
    usuario.email = "test@correo.com"
    usuario.nombre = "Test Usuario"
    return usuario


@pytest.fixture
def mock_sesion_activa():
    """Mock de una sesión activa no expirada."""
    sesion = MagicMock(spec=SesionMesaModel)
    sesion.id = "01SESION123"
    sesion.token_sesion = "TOKEN123"
    sesion.estado = EstadoSesionMesa.ACTIVA
    sesion.fecha_inicio = datetime.now()
    sesion.duracion_minutos = 120
    sesion.esta_expirada = MagicMock(return_value=False)
    sesion.calcular_fecha_expiracion = MagicMock(
        return_value=datetime.now() + timedelta(hours=2)
    )
    return sesion


@pytest.fixture
def mock_sesion_expirada():
    """Mock de una sesión expirada."""
    sesion = MagicMock(spec=SesionMesaModel)
    sesion.id = "01SESION_OLD"
    sesion.token_sesion = "TOKEN_OLD"
    sesion.estado = EstadoSesionMesa.ACTIVA
    sesion.fecha_inicio = datetime.now() - timedelta(hours=3)  # 3 horas atrás
    sesion.duracion_minutos = 120
    sesion.esta_expirada = MagicMock(return_value=True)
    return sesion


class TestLoginServiceValidacionMesa:
    """Tests para validación de mesa antes de login."""

    @pytest.mark.asyncio
    async def test_login_mesa_no_existe_lanza_error(
        self, login_service, valid_login_request
    ):
        """
        Test: Login con ID de mesa que no existe debe lanzar MesaNotFoundError.
        
        Verifica que:
        - Se valida la existencia de la mesa ANTES de crear/buscar usuario
        - Se lanza MesaNotFoundError con código MESA_NOT_FOUND
        """
        # Arrange
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=None)
        
        # Act & Assert
        with pytest.raises(MesaNotFoundError) as exc_info:
            await login_service.login(valid_login_request, "ID_INEXISTENTE")
        
        assert "MESA_NOT_FOUND" in str(exc_info.value.error_code)
        
        # Verificar que NO se intentó crear usuario
        login_service.usuario_repository.get_by_email.assert_not_called()
        login_service.usuario_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_mesa_inactiva_lanza_error(
        self, login_service, valid_login_request, mock_mesa
    ):
        """
        Test: Login con mesa inactiva debe lanzar MesaNotFoundError.
        
        Verifica que:
        - Se valida que la mesa esté activa
        - Se lanza MesaNotFoundError con código MESA_INACTIVE
        """
        # Arrange
        mock_mesa.activo = False
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        
        # Act & Assert
        with pytest.raises(MesaNotFoundError) as exc_info:
            await login_service.login(valid_login_request, mock_mesa.id)
        
        assert "MESA_INACTIVE" in str(exc_info.value.error_code)
        
        # Verificar que NO se intentó crear usuario
        login_service.usuario_repository.get_by_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_email_invalido_lanza_validation_error(
        self, login_service, mock_mesa
    ):
        """
        Test: Login con email inválido debe lanzar ValidationError de Pydantic.
        
        Nota: La validación de email se hace en el schema Pydantic (LoginRequest),
        por lo que lanza ValidationError antes de llegar al servicio.
        """
        # Arrange & Act & Assert
        # La validación ocurre al crear LoginRequest
        with pytest.raises(Exception):  # Pydantic ValidationError
            LoginRequest(
                email="invalido",  # Sin @, correo, o mail
                nombre="Test"
            )


class TestLoginServiceSesionExpirada:
    """Tests para manejo de sesiones expiradas."""

    @pytest.mark.asyncio
    async def test_login_sesion_expirada_marca_como_finalizada(
        self, login_service, valid_login_request, mock_mesa, 
        mock_usuario, mock_sesion_expirada
    ):
        """
        Test: Cuando hay una sesión expirada, debe marcarla como FINALIZADA
        y crear una nueva sesión.
        
        Verifica que:
        - Se llama a finalizar_sesion para la sesión expirada
        - Se crea una nueva sesión
        - Se retorna la nueva sesión
        """
        # Arrange
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        login_service.usuario_repository.get_by_email = AsyncMock(return_value=mock_usuario)
        # IMPORTANTE: update_ultimo_acceso debe retornar el usuario con id string
        login_service.usuario_repository.update_ultimo_acceso = AsyncMock(return_value=mock_usuario)
        login_service.sesion_mesa_repository.get_active_by_mesa = AsyncMock(
            return_value=mock_sesion_expirada
        )
        login_service.sesion_mesa_repository.finalizar_sesion = AsyncMock()
        
        # Mock para la nueva sesión creada
        nueva_sesion = MagicMock(spec=SesionMesaModel)
        nueva_sesion.id = "01NUEVA_SESION"
        nueva_sesion.token_sesion = "NUEVO_TOKEN"
        nueva_sesion.calcular_fecha_expiracion = MagicMock(
            return_value=datetime.now() + timedelta(hours=2)
        )
        login_service.sesion_mesa_repository.create = AsyncMock(return_value=nueva_sesion)
        login_service.sesion_mesa_repository.add_usuario_to_sesion = AsyncMock()
        
        # Act
        response = await login_service.login(valid_login_request, mock_mesa.id)
        
        # Assert
        # Verificar que se finalizó la sesión expirada
        login_service.sesion_mesa_repository.finalizar_sesion.assert_called_once_with(
            mock_sesion_expirada.id
        )
        
        # Verificar que se creó una nueva sesión
        login_service.sesion_mesa_repository.create.assert_called_once()
        
        # Verificar que el token es el de la nueva sesión
        assert response.token_sesion == "NUEVO_TOKEN"
        assert response.id_sesion_mesa == "01NUEVA_SESION"

    @pytest.mark.asyncio
    async def test_login_sesion_activa_valida_no_crea_nueva(
        self, login_service, valid_login_request, mock_mesa,
        mock_usuario, mock_sesion_activa
    ):
        """
        Test: Cuando hay una sesión activa válida (no expirada),
        debe reutilizarla sin crear una nueva.
        
        Verifica que:
        - NO se llama a finalizar_sesion
        - NO se crea una nueva sesión
        - Se retorna la sesión existente
        """
        # Arrange
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        login_service.usuario_repository.get_by_email = AsyncMock(return_value=mock_usuario)
        # IMPORTANTE: update_ultimo_acceso debe retornar el usuario con id string
        login_service.usuario_repository.update_ultimo_acceso = AsyncMock(return_value=mock_usuario)
        login_service.sesion_mesa_repository.get_active_by_mesa = AsyncMock(
            return_value=mock_sesion_activa
        )
        login_service.sesion_mesa_repository.usuario_in_sesion = AsyncMock(return_value=True)
        
        # Act
        response = await login_service.login(valid_login_request, mock_mesa.id)
        
        # Assert
        # Verificar que NO se finalizó ninguna sesión
        login_service.sesion_mesa_repository.finalizar_sesion.assert_not_called()
        
        # Verificar que NO se creó una nueva sesión
        login_service.sesion_mesa_repository.create.assert_not_called()
        
        # Verificar que se retorna la sesión existente
        assert response.token_sesion == mock_sesion_activa.token_sesion

    @pytest.mark.asyncio
    async def test_login_sin_sesion_crea_nueva(
        self, login_service, valid_login_request, mock_mesa, mock_usuario
    ):
        """
        Test: Cuando no hay sesión activa para la mesa,
        debe crear una nueva sesión.
        """
        # Arrange
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        login_service.usuario_repository.get_by_email = AsyncMock(return_value=mock_usuario)
        # IMPORTANTE: update_ultimo_acceso debe retornar el usuario con id string
        login_service.usuario_repository.update_ultimo_acceso = AsyncMock(return_value=mock_usuario)
        login_service.sesion_mesa_repository.get_active_by_mesa = AsyncMock(return_value=None)
        
        nueva_sesion = MagicMock(spec=SesionMesaModel)
        nueva_sesion.id = "01NUEVA"
        nueva_sesion.token_sesion = "TOKEN_NUEVO"
        nueva_sesion.calcular_fecha_expiracion = MagicMock(
            return_value=datetime.now() + timedelta(hours=2)
        )
        login_service.sesion_mesa_repository.create = AsyncMock(return_value=nueva_sesion)
        login_service.sesion_mesa_repository.add_usuario_to_sesion = AsyncMock()
        
        # Act
        response = await login_service.login(valid_login_request, mock_mesa.id)
        
        # Assert
        login_service.sesion_mesa_repository.create.assert_called_once()
        assert response.token_sesion == "TOKEN_NUEVO"


class TestLoginServiceUsuario:
    """Tests para gestión de usuarios en login."""

    @pytest.mark.asyncio
    async def test_login_usuario_nuevo_se_crea(
        self, login_service, valid_login_request, mock_mesa
    ):
        """
        Test: Si el usuario no existe, debe crearse uno nuevo.
        """
        # Arrange
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        login_service.usuario_repository.get_by_email = AsyncMock(return_value=None)
        
        nuevo_usuario = MagicMock(spec=UsuarioModel)
        nuevo_usuario.id = "01NEW_USER"
        login_service.usuario_repository.create = AsyncMock(return_value=nuevo_usuario)
        login_service.sesion_mesa_repository.get_active_by_mesa = AsyncMock(return_value=None)
        
        nueva_sesion = MagicMock(spec=SesionMesaModel)
        nueva_sesion.id = "01SESION"
        nueva_sesion.token_sesion = "TOKEN"
        nueva_sesion.calcular_fecha_expiracion = MagicMock(
            return_value=datetime.now() + timedelta(hours=2)
        )
        login_service.sesion_mesa_repository.create = AsyncMock(return_value=nueva_sesion)
        login_service.sesion_mesa_repository.add_usuario_to_sesion = AsyncMock()
        
        # Act
        response = await login_service.login(valid_login_request, mock_mesa.id)
        
        # Assert
        login_service.usuario_repository.create.assert_called_once()
        assert response.id_usuario == "01NEW_USER"

    @pytest.mark.asyncio
    async def test_login_usuario_existente_nombre_diferente_actualiza(
        self, login_service, mock_mesa
    ):
        """
        Test: Si el usuario existe con nombre diferente, debe actualizarse.
        """
        # Arrange
        login_request = LoginRequest(
            email="test@correo.com",
            nombre="Nuevo Nombre"
        )
        
        usuario_existente = MagicMock(spec=UsuarioModel)
        usuario_existente.id = "01USER"
        usuario_existente.nombre = "Nombre Viejo"
        
        usuario_actualizado = MagicMock(spec=UsuarioModel)
        usuario_actualizado.id = "01USER"
        usuario_actualizado.nombre = "Nuevo Nombre"
        
        login_service.mesa_repository.get_by_id = AsyncMock(return_value=mock_mesa)
        login_service.usuario_repository.get_by_email = AsyncMock(
            return_value=usuario_existente
        )
        login_service.usuario_repository.update = AsyncMock(
            return_value=usuario_actualizado
        )
        login_service.sesion_mesa_repository.get_active_by_mesa = AsyncMock(return_value=None)
        
        nueva_sesion = MagicMock(spec=SesionMesaModel)
        nueva_sesion.id = "01SESION"
        nueva_sesion.token_sesion = "TOKEN"
        nueva_sesion.calcular_fecha_expiracion = MagicMock(
            return_value=datetime.now() + timedelta(hours=2)
        )
        login_service.sesion_mesa_repository.create = AsyncMock(return_value=nueva_sesion)
        login_service.sesion_mesa_repository.add_usuario_to_sesion = AsyncMock()
        
        # Act
        await login_service.login(login_request, mock_mesa.id)
        
        # Assert
        login_service.usuario_repository.update.assert_called_once()
