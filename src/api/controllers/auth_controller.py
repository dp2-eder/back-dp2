"""
Controlador para gestión de autenticación y usuarios.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.usuario_service import UsuarioService
from src.core.security import security
from src.api.schemas.usuario_schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    UsuarioResponse,
    UsuarioUpdate,
    UsuarioCreate,
    UsuarioSummary,
)
from src.business_logic.exceptions.usuario_exceptions import (
    UsuarioValidationError,
    UsuarioNotFoundError,
    UsuarioConflictError,
    InvalidCredentialsError,
    InactiveUserError,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# OAuth2 scheme para extraer el token del header Authorization
# Usamos auto_error=False para evitar errores durante la inicialización
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_database_session),
) -> UsuarioResponse:
    """
    Dependency para obtener el usuario actual desde el token JWT.

    Parameters
    ----------
    token : Optional[str]
        Token JWT del header Authorization.
    session : AsyncSession
        Sesión de base de datos.

    Returns
    -------
    UsuarioResponse
        Datos del usuario autenticado.

    Raises
    ------
    HTTPException
        401 si el token es inválido o el usuario no existe.
    """
    # Verificar que el token existe (necesario con auto_error=False)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "UNAUTHORIZED",
                "detail": "Token de autenticación requerido"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar el token
    payload = security.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "UNAUTHORIZED",
                "detail": "Token inválido o expirado"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que es un access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "UNAUTHORIZED",
                "detail": "Token no es un access token válido"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener el ID del usuario
    usuario_id = payload.get("sub")
    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "UNAUTHORIZED",
                "detail": "Token inválido: falta información del usuario"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Obtener el usuario
    usuario_service = UsuarioService(session)
    try:
        usuario = await usuario_service.get_usuario_by_id(usuario_id)
        
        # Verificar que el usuario esté activo
        # (esto se hace en el schema, pero verificamos por seguridad)
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status": 401,
                    "code": "INACTIVE_USER",
                    "detail": "Usuario inactivo"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return usuario
    except UsuarioNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "UNAUTHORIZED",
                "detail": "Usuario no encontrado"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description="Autentica un usuario con email y contraseña, devuelve tokens JWT.",
)
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_database_session),
) -> LoginResponse:
    """
    Endpoint para iniciar sesión.

    Parameters
    ----------
    login_data : LoginRequest
        Datos de login (email y contraseña).
    session : AsyncSession
        Sesión de base de datos.

    Returns
    -------
    LoginResponse
        Tokens de acceso y refresh junto con información del usuario.

    Raises
    ------
    HTTPException
        401 si las credenciales son inválidas o el usuario está inactivo.
        500 si ocurre un error inesperado.
    """
    try:
        usuario_service = UsuarioService(session)
        result = await usuario_service.login(login_data)
        await session.commit()
        return result
    except InvalidCredentialsError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "INVALID_CREDENTIALS",
                "detail": str(e)
            },
        )
    except InactiveUserError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "INACTIVE_USER",
                "detail": str(e)
            },
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": 500,
                "code": "INTERNAL_ERROR",
                "detail": f"Error inesperado: {str(e)}"
            },
        )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Registra un nuevo usuario en el sistema.",
)
async def register(
    register_data: RegisterRequest,
    session: AsyncSession = Depends(get_database_session),
) -> RegisterResponse:
    """
    Endpoint para registrar un nuevo usuario.

    Parameters
    ----------
    register_data : RegisterRequest
        Datos del usuario a registrar.
    session : AsyncSession
        Sesión de base de datos.

    Returns
    -------
    RegisterResponse
        Usuario creado y mensaje de confirmación.

    Raises
    ------
    HTTPException
        400 si los datos no son válidos.
        409 si ya existe un usuario con el mismo email.
        500 si ocurre un error inesperado.
    """
    try:
        usuario_service = UsuarioService(session)
        result = await usuario_service.register(register_data)
        await session.commit()
        return result
    except UsuarioValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": 400,
                "code": "VALIDATION_ERROR",
                "detail": str(e)
            }
        )
    except UsuarioConflictError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "status": 409,
                "code": "USUARIO_CONFLICT",
                "detail": str(e)
            }
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": 500,
                "code": "INTERNAL_ERROR",
                "detail": f"Error inesperado: {str(e)}"
            },
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar access token",
    description="Renueva el access token usando un refresh token válido.",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_database_session),
) -> RefreshTokenResponse:
    """
    Endpoint para renovar el access token.

    Parameters
    ----------
    refresh_data : RefreshTokenRequest
        Refresh token para renovar el acceso.
    session : AsyncSession
        Sesión de base de datos.

    Returns
    -------
    RefreshTokenResponse
        Nuevo access token.

    Raises
    ------
    HTTPException
        401 si el refresh token es inválido.
        500 si ocurre un error inesperado.
    """
    try:
        usuario_service = UsuarioService(session)
        return await usuario_service.refresh_token(refresh_data)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "INVALID_CREDENTIALS",
                "detail": str(e)
            },
        )
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": 401,
                "code": "INACTIVE_USER",
                "detail": str(e)
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": 500,
                "code": "INTERNAL_ERROR",
                "detail": f"Error inesperado: {str(e)}"
            },
        )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario actual",
    description="Obtiene la información del usuario autenticado.",
)
async def get_current_user_info(
    current_user: UsuarioResponse = Depends(get_current_user),
) -> UsuarioResponse:
    """
    Endpoint para obtener información del usuario actual.

    Parameters
    ----------
    current_user : UsuarioResponse
        Usuario autenticado (obtenido del token JWT).

    Returns
    -------
    UsuarioResponse
        Información del usuario autenticado.
    """
    return current_user

