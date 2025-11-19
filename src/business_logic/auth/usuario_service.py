"""
Servicio para la gestión de usuarios y autenticación en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
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
        if not usuario.activo:
            raise InactiveUserError("El usuario está inactivo. Contacte al administrador.")

        # Verificar contraseña
        if not usuario.password_hash:
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        if not security.verify_password(login_data.password, usuario.password_hash):
            raise InvalidCredentialsError("Email o contraseña incorrectos")

        # Actualizar último acceso
        await self.repository.update_ultimo_acceso(usuario.id)

        # Generar tokens
        token_data = {
            "sub": usuario.id,
            "email": usuario.email,
            "rol_id": usuario.id_rol,
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
        # Validar que el email no esté vacío
        if not register_data.email:
            raise UsuarioValidationError("El email es requerido")

        # Validar que el rol existe
        rol = await self.rol_repository.get_by_id(register_data.id_rol)
        if not rol:
            raise UsuarioValidationError(
                f"El rol con ID '{register_data.id_rol}' no existe"
            )

        # Verificar si ya existe un usuario con ese email
        existing_usuario = await self.repository.get_by_email(register_data.email)
        if existing_usuario:
            raise UsuarioConflictError(
                f"Ya existe un usuario con el email '{register_data.email}'"
            )

        # Hash de la contraseña
        password_hash = security.get_password_hash(register_data.password)

        try:
            # Crear modelo de usuario desde los datos
            usuario = UsuarioModel(
                email=register_data.email,
                password_hash=password_hash,
                nombre=register_data.nombre,
                telefono=register_data.telefono,
                id_rol=register_data.id_rol,
                activo=True,
            )

            # Persistir en la base de datos
            created_usuario = await self.repository.create(usuario)

            # Convertir y retornar como esquema de respuesta
            usuario_response = UsuarioResponse.model_validate(created_usuario)

            return RegisterResponse(
                status=201,
                code="SUCCESS",
                usuario=usuario_response,
                message="Usuario registrado exitosamente",
            )
        except IntegrityError as e:
            raise UsuarioConflictError(f"Error al crear el usuario: {str(e)}")

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

        if not usuario.activo:
            raise InactiveUserError("El usuario está inactivo")

        # Generar nuevo access token
        token_data = {
            "sub": usuario.id,
            "email": usuario.email,
            "rol_id": usuario.id_rol,
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

    async def get_usuarios(self, skip: int = 0, limit: int = 100) -> list[UsuarioSummary]:
        """
        Obtiene una lista paginada de usuarios.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        list[UsuarioSummary]
            Lista de usuarios resumidos.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise UsuarioValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise UsuarioValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener usuarios desde el repositorio
        usuarios, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        usuario_summaries = [UsuarioSummary.model_validate(usuario) for usuario in usuarios]

        return usuario_summaries

    async def update_usuario(
        self, usuario_id: str, usuario_data: UsuarioUpdate
    ) -> UsuarioResponse:
        """
        Actualiza un usuario existente.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a actualizar (ULID).
        usuario_data : UsuarioUpdate
            Datos para actualizar el usuario.

        Returns
        -------
        UsuarioResponse
            Esquema de respuesta con los datos del usuario actualizado.

        Raises
        ------
        UsuarioNotFoundError
            Si no se encuentra un usuario con el ID proporcionado.
        UsuarioValidationError
            Si el rol especificado no existe o el email ya está en uso.
        UsuarioConflictError
            Si hay un conflicto al actualizar el usuario.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = usuario_data.model_dump(exclude_none=True)

        # Si se actualiza la contraseña, hacer hash
        if "password" in update_data:
            update_data["password_hash"] = security.get_password_hash(update_data["password"])
            del update_data["password"]

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el usuario actual
            return await self.get_usuario_by_id(usuario_id)

        # Validar id_rol si se proporciona
        if "id_rol" in update_data:
            rol = await self.rol_repository.get_by_id(update_data["id_rol"])
            if not rol:
                raise UsuarioValidationError(
                    f"El rol con ID '{update_data['id_rol']}' no existe"
                )

        # Validar email si se proporciona
        if "email" in update_data:
            existing_usuario = await self.repository.get_by_email(update_data["email"])
            if existing_usuario and existing_usuario.id != usuario_id:
                raise UsuarioConflictError(
                    f"Ya existe un usuario con el email '{update_data['email']}'"
                )

        try:
            # Actualizar el usuario
            updated_usuario = await self.repository.update(usuario_id, **update_data)

            # Verificar si el usuario fue encontrado
            if not updated_usuario:
                raise UsuarioNotFoundError(f"No se encontró el usuario con ID {usuario_id}")

            # Convertir y retornar como esquema de respuesta
            return UsuarioResponse.model_validate(updated_usuario)
        except IntegrityError as e:
            raise UsuarioConflictError(f"Error al actualizar el usuario: {str(e)}")

    async def delete_usuario(self, usuario_id: str) -> bool:
        """
        Elimina un usuario por su ID.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a eliminar (ULID).

        Returns
        -------
        bool
            True si el usuario fue eliminado correctamente.

        Raises
        ------
        UsuarioNotFoundError
            Si no se encuentra un usuario con el ID proporcionado.
        """
        # Verificar primero si el usuario existe
        usuario = await self.repository.get_by_id(usuario_id)
        if not usuario:
            raise UsuarioNotFoundError(f"No se encontró el usuario con ID {usuario_id}")

        # Eliminar el usuario
        result = await self.repository.delete(usuario_id)
        return result

