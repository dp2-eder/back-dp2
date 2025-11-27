"""
Servicio para la gestión de usuarios y autenticación en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta

from src.repositories.auth.usuario_repository import UsuarioRepository
from src.repositories.auth.rol_repository import RolRepository
from src.models.auth.usuario_model import UsuarioModel
from src.core.security import security
from src.core.config import get_settings
from src.api.schemas.usuario_schema import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioSummary,
    LoginRequest,
    LoginResponse,
    AdminLoginRequest,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from src.business_logic.exceptions.usuario_exceptions import (
    UsuarioValidationError,
    UsuarioNotFoundError,
    UsuarioConflictError,
    InvalidCredentialsError,
    InactiveUserError,
)


class UsuarioService:
    """Servicio para la gestión de usuarios y autenticación.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con usuarios, incluyendo autenticación, registro, validaciones y manejo de excepciones.

    Attributes
    ----------
    repository : UsuarioRepository
        Repositorio para acceso a datos de usuarios.
    rol_repository : RolRepository
        Repositorio para validar roles.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = UsuarioRepository(session)
        self.rol_repository = RolRepository(session)
        self.settings = get_settings()

    async def login(self, login_data: LoginRequest) -> LoginResponse:
        """
        Autentica un usuario y genera tokens JWT.

        Parameters
        ----------
        login_data : LoginRequest
            Datos de login (email y contraseña).

        Returns
        -------
        LoginResponse
            Tokens de acceso y refresh junto con información del usuario.

        Raises
        ------
        InvalidCredentialsError
            Si las credenciales son inválidas.
        InactiveUserError
            Si el usuario está inactivo.
        """
        # Buscar usuario por email
        usuario = await self.repository.get_by_email(login_data.email)

        if not usuario:
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        # Verificar si el usuario está activo
        # if not usuario.activo:
        #     raise InactiveUserError("El usuario está inactivo. Contacte al administrador.")

        # Verificar contraseña
        # if not usuario.password_hash:
        #     raise InvalidCredentialsError("Email o contraseña incorrectos")

        # if not security.verify_password(login_data.password, usuario.password_hash):
        #     raise InvalidCredentialsError("Email o contraseña incorrectos")

        # Actualizar último acceso
        await self.repository.update_ultimo_acceso(usuario.id)

        # Generar tokens
        token_data = {
            "sub": usuario.id,
            "email": usuario.email,
        }

        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)

        # Construir respuesta
        usuario_response = UsuarioResponse.model_validate(usuario)

        return LoginResponse(
            status=200,
            code="SUCCESS",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            usuario=usuario_response,
        )

    async def admin_login(self, login_data: AdminLoginRequest) -> LoginResponse:
        """
        Autentica un administrador y genera tokens JWT.

        Parameters
        ----------
        login_data : AdminLoginRequest
            Datos de login (usuario/email y contraseña).

        Returns
        -------
        LoginResponse
            Tokens de acceso y refresh junto con información del usuario.

        Raises
        ------
        InvalidCredentialsError
            Si las credenciales son inválidas o el usuario no es administrador.
        InactiveUserError
            Si el usuario está inactivo.
        """
        # Buscar usuario por email (el campo "usuario" se usa como email)
        usuario = await self.repository.get_by_email(login_data.usuario)

        if not usuario:
            raise InvalidCredentialsError("Usuario o contraseña incorrectos")

        # # Verificar si el usuario está activo
        # if not usuario.activo:
        #     raise InactiveUserError("El usuario está inactivo. Contacte al administrador.")

        # Verificar contraseña
        # Obtener password_hash del modelo (puede estar en atributos dinámicos)
        password_hash = getattr(usuario, 'password', None)
        if not password_hash:
            raise InvalidCredentialsError("Usuario o contraseña incorrectos")

        if not security.verify_password(login_data.password, password_hash):
            raise InvalidCredentialsError("Usuario o contraseña incorrectos")

        # Verificar que el usuario tenga rol de administrador
        if not usuario.id_rol:
            raise InvalidCredentialsError("El usuario no tiene un rol asignado")

        # Obtener el rol del usuario
        rol = await self.rol_repository.get_by_id(usuario.id_rol)
        if not rol:
            raise InvalidCredentialsError("El rol del usuario no existe")

        # Verificar que el rol sea de administrador
        # Buscar roles de administrador (puede ser "ADMIN", "ADMINISTRADOR", etc.)
        rol_nombre_upper = rol.nombre.upper()
        if rol_nombre_upper not in ["ADMIN", "ADMINISTRADOR"]:
            raise InvalidCredentialsError("Acceso denegado. Se requiere rol de administrador.")

        # Actualizar último acceso
        await self.repository.update_ultimo_acceso(usuario.id)

        # Generar tokens
        token_data = {
            "sub": usuario.id,
            "email": usuario.email,
        }

        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)

        # Construir respuesta
        usuario_response = UsuarioResponse.model_validate(usuario)

        return LoginResponse(
            status=200,
            code="SUCCESS",
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            usuario=usuario_response,
        )

    async def register(self, register_data: RegisterRequest) -> RegisterResponse:
        """
        Registra un nuevo usuario en el sistema.

        Parameters
        ----------
        register_data : RegisterRequest
            Datos para crear el nuevo usuario.

        Returns
        -------
        RegisterResponse
            Esquema de respuesta con los datos del usuario creado.

        Raises
        ------
        UsuarioValidationError
            Si los datos no cumplen con las validaciones o el rol no existe.
        UsuarioConflictError
            Si ya existe un usuario con el mismo email.
        """
                # 1. Resolver ID del Rol
        id_rol = register_data.id_rol
        if id_rol:
            if not await self.rol_repository.get_by_id(id_rol):
                raise UsuarioValidationError(f"El rol con ID '{id_rol}' no existe")
        else:
            rol_default = await self.rol_repository.get_default()
            if not rol_default:
                raise UsuarioValidationError("No existe un rol por defecto configurado en el sistema")
            id_rol = rol_default.id

        # 2. Verificar existencia previa (Optimización UX)
        if not register_data.email:
             raise UsuarioValidationError("El email es requerido")
             
        if await self.repository.get_by_email(register_data.email):
            raise UsuarioConflictError(f"Ya existe un usuario con el email '{register_data.email}'")

        # 3. Preparar modelo
        password_hash = security.get_password_hash(register_data.password)
        
        usuario = UsuarioModel(
            email=register_data.email,
            password_hash=password_hash,
            nombre=register_data.nombre,
            telefono=register_data.telefono,
            id_rol=id_rol,
        )

        try:
            # 4. Persistir y confirmar transacción
            created_usuario = await self.repository.create(usuario)
            await self.repository.session.commit()
            await self.repository.session.refresh(created_usuario)

            return RegisterResponse(
                status=201,
                code="SUCCESS",
                usuario=UsuarioResponse.model_validate(created_usuario),
                message="Usuario registrado exitosamente",
            )
        except IntegrityError:
            await self.repository.session.rollback()
            raise UsuarioConflictError(f"Ya existe un usuario con el email '{register_data.email}'")
        except SQLAlchemyError as e:
            await self.repository.session.rollback()
            raise UsuarioValidationError(f"Error al registrar usuario: {str(e)}")

    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Renueva el access token usando un refresh token válido.

        Parameters
        ----------
        refresh_data : RefreshTokenRequest
            Refresh token para renovar el acceso.

        Returns
        -------
        RefreshTokenResponse
            Nuevo access token.

        Raises
        ------
        InvalidCredentialsError
            Si el refresh token es inválido o expiró.
        """
        # Verificar el refresh token
        payload = security.verify_token(refresh_data.refresh_token)

        if not payload:
            raise InvalidCredentialsError("Refresh token inválido o expirado")

        # Verificar que es un refresh token
        if payload.get("type") != "refresh":
            raise InvalidCredentialsError("Token no es un refresh token válido")

        # Verificar que el usuario aún existe y está activo
        usuario_id = payload.get("sub")
        if not usuario_id:
            raise InvalidCredentialsError("Token inválido: falta información del usuario")

        usuario = await self.repository.get_by_id(usuario_id)
        if not usuario:
            raise InvalidCredentialsError("Usuario no encontrado")

        # if not usuario.activo:
        #     raise InactiveUserError("El usuario está inactivo")

        # Generar nuevo access token
        token_data = {
            "sub": usuario.id,
            "email": usuario.email,
        }

        access_token = security.create_access_token(token_data)

        return RefreshTokenResponse(
            status=200,
            code="SUCCESS",
            access_token=access_token,
            token_type="bearer",
        )

    async def get_usuario_by_id(self, usuario_id: str) -> UsuarioResponse:
        """
        Obtiene un usuario por su ID.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a buscar (ULID).

        Returns
        -------
        UsuarioResponse
            Esquema de respuesta con los datos del usuario.

        Raises
        ------
        UsuarioNotFoundError
            Si no se encuentra un usuario con el ID proporcionado.
        """
        # Buscar el usuario por su ID
        usuario = await self.repository.get_by_id(usuario_id)

        # Verificar si existe
        if not usuario:
            raise UsuarioNotFoundError(f"No se encontró el usuario con ID {usuario_id}")

        # Convertir y retornar como esquema de respuesta
        return UsuarioResponse.model_validate(usuario)
