from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.admin_service import AdminService
from src.api.schemas.admin_schema import (
    AdminCreate,
    AdminResponse,
    AdminLoginRequest,
    TokenResponse
)
from src.business_logic.exceptions.admin_exceptions import (
    AdminNotFoundError,
    AdminConflictError,
)

# Definimos el router con prefijo y tag para la documentación
router = APIRouter(prefix="/admins", tags=["Admins"])


@router.post(
    "",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo administrador",
    description="Crea un nuevo administrador en el sistema. La contraseña será encriptada automáticamente.",
)
async def create_admin(
    admin_data: AdminCreate,
    session: AsyncSession = Depends(get_database_session)
) -> AdminResponse:
    """
    Crea un nuevo administrador.

    Args:
        admin_data: Datos del administrador (usuario, email, password).
        session: Sesión de base de datos inyectada.

    Returns:
        AdminResponse: Datos del administrador creado (sin password).

    Raises:
        HTTPException 409: Si el email o usuario ya existen.
        HTTPException 500: Error interno.
    """
    try:
        service = AdminService(session)
        return await service.create_admin(admin_data)
    except AdminConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


# Endpoint adicional opcional: Buscar por email (útil para validaciones)
@router.get(
    "/email/{email}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar administrador por email",
    description="Busca un administrador usando su dirección de correo electrónico.",
)
async def get_admin_by_email(
    email: str,
    session: AsyncSession = Depends(get_database_session)
) -> AdminResponse:
    try:
        service = AdminService(session)
        return await service.get_admin_by_email(email)
    except AdminNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión de administrador",
    description="Autentica un administrador usando usuario/email y contraseña. Devuelve un token JWT.",
)
async def login_admin(
    login_data: AdminLoginRequest,
    session: AsyncSession = Depends(get_database_session)
) -> TokenResponse:
    """
    Endpoint para login de administradores.

    Args:
        login_data: Credenciales (identifier + password).
        session: Sesión de base de datos.

    Returns:
        TokenResponse: Token de acceso.
    """
    try:
        service = AdminService(session)
        return await service.login(login_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno durante el login: {str(e)}",
        )
