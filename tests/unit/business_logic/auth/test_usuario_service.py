"""
Pruebas unitarias para el servicio de usuarios y autenticación.

ARCHIVO REACTIVADO Y ACTUALIZADO
================================
Este archivo ha sido reactivado y actualizado para soportar el nuevo sistema
con roles y el rol COMENSAL por defecto en el registro.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ulid import ULID
from datetime import datetime

from src.business_logic.auth.usuario_service import UsuarioService
from src.models.auth.usuario_model import UsuarioModel
from src.models.auth.rol_model import RolModel
from src.api.schemas.usuario_schema import RegisterRequest, RegisterResponse
from src.business_logic.exceptions.usuario_exceptions import (
    UsuarioValidationError,
    UsuarioConflictError,
    UsuarioNotFoundError,
    InvalidCredentialsError,
    InactiveUserError,
)


@pytest.fixture
def mock_session():
    """Fixture para mock de sesión de base de datos."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_usuario_repository():
    """Fixture para mock del repositorio de usuarios."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_rol_repository():
    """Fixture para mock del repositorio de roles."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def usuario_service(mock_session):
    """Fixture para instancia de UsuarioService con repositorios mockeados."""
    with patch('src.business_logic.auth.usuario_service.UsuarioRepository') as mock_user_repo_class, \
         patch('src.business_logic.auth.usuario_service.RolRepository') as mock_rol_repo_class, \
         patch('src.business_logic.auth.usuario_service.get_settings') as mock_settings:
        
        mock_user_repo = AsyncMock()
        mock_rol_repo = AsyncMock()
        mock_user_repo_class.return_value = mock_user_repo
        mock_rol_repo_class.return_value = mock_rol_repo
        
        service = UsuarioService(mock_session)
        service.repository = mock_user_repo
        service.rol_repository = mock_rol_repo
        service.settings = mock_settings.return_value
        
        yield service, mock_user_repo, mock_rol_repo


@pytest.fixture
def rol_comensal():
    """Fixture para rol COMENSAL."""
    rol = RolModel(
        id=str(ULID()),
        nombre="COMENSAL",
        descripcion="Rol para clientes del restaurante",
        activo=True
    )
    return rol


@pytest.fixture
def register_request_comensal():
    """Fixture para RegisterRequest sin rol (debería asignar COMENSAL por defecto)."""
    return RegisterRequest(
        email="test@example.com",
        password="password123",
        nombre="Test User",
        telefono="123456789",
        id_rol=None  # No se proporciona rol
    )


@pytest.fixture
def register_request_con_rol():
    """Fixture para RegisterRequest con rol específico."""
    return RegisterRequest(
        email="admin@example.com",
        password="password123",
        nombre="Admin User",
        telefono="987654321",
        id_rol=str(ULID())  # Rol específico
    )


class TestUsuarioServiceRegister:
    """Pruebas para el método register de UsuarioService."""

    @pytest.mark.asyncio
    async def test_register_sin_rol_asigna_comensal_por_defecto(
        self, usuario_service, rol_comensal, register_request_comensal
    ):
        """Test que se asigna rol COMENSAL por defecto cuando no se proporciona rol."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        # Mocks
        mock_user_repo.get_by_email.return_value = None
        mock_rol_repo.get_default.return_value = rol_comensal  # Mock get_default
        
        mock_user_repo.create.return_value = UsuarioModel(
            id=str(ULID()),
            email=register_request_comensal.email,
            nombre=register_request_comensal.nombre,
            telefono=register_request_comensal.telefono,
            id_rol=rol_comensal.id,
            activo=True
        )
        
        # Ejecutar
        with patch('src.business_logic.auth.usuario_service.security') as mock_security:
            mock_security.get_password_hash.return_value = "hashed_password"
            result = await service.register(register_request_comensal)
        
        # Verificaciones
        assert isinstance(result, RegisterResponse)
        assert result.status == 201
        assert result.code == "SUCCESS"
        assert result.usuario.email == register_request_comensal.email
        
        # Verificar que se creó el usuario con el rol correcto
        mock_user_repo.create.assert_called_once()
        call_args = mock_user_repo.create.call_args[0][0]
        assert call_args.id_rol == rol_comensal.id
        
        # Verificar que se llamó a get_default
        mock_rol_repo.get_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_con_rol_especifico(
        self, usuario_service, register_request_con_rol
    ):
        """Test que se usa el rol proporcionado cuando se especifica."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        rol_especifico = RolModel(
            id=register_request_con_rol.id_rol,
            nombre="ADMIN",
            descripcion="Rol administrador",
            activo=True
        )
        
        # Mocks
        mock_rol_repo.get_by_id.return_value = rol_especifico
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = UsuarioModel(
            id=str(ULID()),
            email=register_request_con_rol.email,
            nombre=register_request_con_rol.nombre,
            telefono=register_request_con_rol.telefono,
            id_rol=rol_especifico.id,
            activo=True
        )
        
        # Ejecutar
        with patch('src.business_logic.auth.usuario_service.security') as mock_security:
            mock_security.get_password_hash.return_value = "hashed_password"
            result = await service.register(register_request_con_rol)
        
        # Verificaciones
        assert isinstance(result, RegisterResponse)
        assert result.usuario.id_rol == rol_especifico.id
        
        # Verificar que se buscó el rol por ID (no por nombre)
        mock_rol_repo.get_by_id.assert_called_once_with(register_request_con_rol.id_rol)
        mock_rol_repo.get_default.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_error_rol_comensal_no_existe(
        self, usuario_service, register_request_comensal
    ):
        """Test que falla cuando no existe el rol COMENSAL por defecto."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        # Mocks
        mock_rol_repo.get_default.return_value = None
        
        # Ejecutar y verificar excepción
        with pytest.raises(UsuarioValidationError) as exc_info:
            await service.register(register_request_comensal)
        
        assert "No existe un rol por defecto" in str(exc_info.value)
        mock_rol_repo.get_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_error_rol_especifico_no_existe(
        self, usuario_service, register_request_con_rol
    ):
        """Test que falla cuando no existe el rol específico proporcionado."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        # Mocks
        mock_rol_repo.get_by_id.return_value = None
        
        # Ejecutar y verificar excepción
        with pytest.raises(UsuarioValidationError) as exc_info:
            await service.register(register_request_con_rol)
        
        assert f"El rol con ID '{register_request_con_rol.id_rol}' no existe" in str(exc_info.value)
        mock_rol_repo.get_by_id.assert_called_once_with(register_request_con_rol.id_rol)

    @pytest.mark.asyncio
    async def test_register_error_email_ya_existe(
        self, usuario_service, rol_comensal, register_request_comensal
    ):
        """Test que falla cuando el email ya está registrado."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        # Mocks
        mock_rol_repo.get_by_nombre.return_value = rol_comensal
        usuario_existente = UsuarioModel(
            id=str(ULID()),
            email=register_request_comensal.email,
            nombre="Existing User"
        )
        mock_user_repo.get_by_email.return_value = usuario_existente
        
        # Ejecutar y verificar excepción
        with pytest.raises(UsuarioConflictError) as exc_info:
            await service.register(register_request_comensal)
        
        assert "Ya existe un usuario con el email" in str(exc_info.value)
        mock_user_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_error_email_vacio(
        self, usuario_service, register_request_comensal
    ):
        """Test que falla cuando el email está vacío."""
        service, mock_user_repo, mock_rol_repo = usuario_service
        
        register_request_comensal.email = ""
        
        # Ejecutar y verificar excepción
        with pytest.raises(UsuarioValidationError) as exc_info:
            await service.register(register_request_comensal)
        
        assert "El email es requerido" in str(exc_info.value)
        mock_rol_repo.get_by_nombre.assert_not_called()
        mock_user_repo.get_by_email.assert_not_called()


class TestRolRepositoryGetByNombre:
    """Pruebas para el método get_by_nombre de RolRepository."""

    @pytest.mark.asyncio
    async def test_get_by_nombre_rol_existe(self, mock_session):
        """Test que encuentra un rol por nombre."""
        from src.repositories.auth.rol_repository import RolRepository
        
        repo = RolRepository(mock_session)
        
        rol_mock = RolModel(
            id=str(ULID()),
            nombre="COMENSAL",
            descripcion="Rol comensal",
            activo=True
        )
        
        # Mock de la consulta - usar MagicMock en lugar de AsyncMock
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = rol_mock
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await repo.get_by_nombre("COMENSAL")
        
        # Verificar
        assert result == rol_mock
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_nombre_rol_no_existe(self, mock_session):
        """Test que no encuentra un rol por nombre."""
        from src.repositories.auth.rol_repository import RolRepository
        
        repo = RolRepository(mock_session)
        
        # Mock de la consulta que no encuentra resultados
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Ejecutar
        result = await repo.get_by_nombre("ROL_INEXISTENTE")
        
        # Verificar
        assert result is None
        mock_session.execute.assert_called_once()


class TestUsuarioModelWithRol:
    """Pruebas para el modelo Usuario con el nuevo campo id_rol."""

    def test_usuario_model_con_rol(self, rol_comensal):
        """Test que se puede crear un usuario con rol."""
        usuario = UsuarioModel(
            id=str(ULID()),
            email="test@example.com",
            nombre="Test User",
            id_rol=rol_comensal.id,
            activo=True
        )
        
        assert usuario.id_rol == rol_comensal.id
        assert usuario.rol is None  # No hay relación sin sesión

    def test_usuario_model_sin_rol(self):
        """Test que se puede crear un usuario sin rol (nullable)."""
        usuario = UsuarioModel(
            id=str(ULID()),
            email="test@example.com",
            nombre="Test User",
            id_rol=None,
            activo=True
        )
        
        assert usuario.id_rol is None
        assert usuario.rol is None

    def test_usuario_to_dict_incluye_rol(self, rol_comensal):
        """Test que to_dict incluye el campo id_rol."""
        usuario = UsuarioModel(
            id=str(ULID()),
            email="test@example.com",
            nombre="Test User",
            id_rol=rol_comensal.id,
            activo=True
        )
        
        result = usuario.to_dict()
        assert 'id_rol' in result
        assert result['id_rol'] == rol_comensal.id
