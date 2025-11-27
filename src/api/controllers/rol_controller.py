"""
Endpoints para gestión de roles.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.rol_service import RolService
from src.api.schemas.rol_schema import (
    RolCreate,
    RolResponse,
    RolUpdate,
    RolList,
)
from src.business_logic.exceptions.rol_exceptions import (
    RolValidationError,
    RolNotFoundError,
    RolConflictError,
)

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post(
    "",
    response_model=RolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo rol",
    description="Crea un nuevo rol en el sistema con los datos proporcionados.",
)
async def create_rol(
    rol_data: RolCreate, session: AsyncSession = Depends(get_database_session)
) -> RolResponse:
    """
    Crea un nuevo rol en el sistema.
    
    Args:
        rol_data: Datos del rol a crear.
        session: Sesión de base de datos.

    Returns:
        El rol creado con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe un rol con el mismo nombre.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        return await rol_service.create_rol(rol_data)
    except RolConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{rol_id}",
    response_model=RolResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un rol por ID",
    description="Obtiene los detalles de un rol específico por su ID.",
)
async def get_rol(
    rol_id: str, session: AsyncSession = Depends(get_database_session)
) -> RolResponse:
    """
    Obtiene un rol específico por su ID.

    Args:
        rol_id: ID del rol a buscar.
        session: Sesión de base de datos.

    Returns:
        El rol encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el rol.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        return await rol_service.get_rol_by_id(rol_id)
    except RolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/usuario/{usuario_id}/nombre",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Obtener nombre del rol de un usuario",
    description="Obtiene el nombre del rol asignado a un usuario específico por su ID.",
)
async def get_nombre_rol_usuario(
    usuario_id: str, session: AsyncSession = Depends(get_database_session)
) -> dict:
    """
    Obtiene el nombre del rol de un usuario específico.

    Args:
        usuario_id: ID del usuario para obtener su rol.
        session: Sesión de base de datos.

    Returns:
        Diccionario con el nombre del rol: {"nombre_rol": "COMENSAL"}

    Raises:
        HTTPException:
            - 404: Si no se encuentra el usuario, no tiene rol asignado, o el rol no existe.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        return await rol_service.get_nombre_rol_by_usuario_id(usuario_id)
    except RolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=RolList,
    status_code=status.HTTP_200_OK,
    summary="Listar roles",
    description="Obtiene una lista paginada de roles.",
)
async def list_roles(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> RolList:
    """
    Obtiene una lista paginada de roles.
    
    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de roles y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        return await rol_service.get_roles(skip, limit)
    except RolValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{rol_id}",
    response_model=RolResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un rol",
    description="Actualiza los datos de un rol existente.",
)
async def update_rol(
    rol_id: str,
    rol_data: RolUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> RolResponse:
    """
    Actualiza un rol existente.

    Args:
        rol_id: ID del rol a actualizar.
        rol_data: Datos del rol a actualizar.
        session: Sesión de base de datos.

    Returns:
        El rol actualizado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el rol.
            - 409: Si hay un conflicto (e.g., nombre duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        return await rol_service.update_rol(rol_id, rol_data)
    except RolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RolConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{rol_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un rol",
    description="Elimina un rol existente del sistema.",
)
async def delete_rol(
    rol_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina un rol existente.

    Args:
        rol_id: ID del rol a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el rol.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        rol_service = RolService(session)
        result = await rol_service.delete_rol(rol_id)
        # No es necesario verificar el resultado aquí ya que delete_rol
        # lanza RolNotFoundError si no encuentra el rol
    except RolNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
