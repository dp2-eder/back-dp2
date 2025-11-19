"""
Endpoints para gestión de locales/restaurantes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.local_service import LocalService
from src.api.schemas.local_schema import (
    LocalCreate,
    LocalResponse,
    LocalUpdate,
    LocalList,
)
from src.business_logic.exceptions.local_exceptions import (
    LocalValidationError,
    LocalNotFoundError,
    LocalConflictError,
)

router = APIRouter(prefix="/locales", tags=["Locales"])


@router.post(
    "",
    response_model=LocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo local",
    description="Crea un nuevo local/restaurante en el sistema con los datos proporcionados.",
)
async def create_local(
    local_data: LocalCreate, session: AsyncSession = Depends(get_database_session)
) -> LocalResponse:
    """
    Crea un nuevo local en el sistema.

    Args:
        local_data: Datos del local a crear.
        session: Sesión de base de datos.

    Returns:
        El local creado con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe un local con el mismo código.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        return await local_service.create_local(local_data)
    except LocalConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{local_id}",
    response_model=LocalResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un local por ID",
    description="Obtiene los detalles de un local específico por su ID.",
)
async def get_local(
    local_id: str, session: AsyncSession = Depends(get_database_session)
) -> LocalResponse:
    """
    Obtiene un local específico por su ID.

    Args:
        local_id: ID del local a buscar.
        session: Sesión de base de datos.

    Returns:
        El local encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        return await local_service.get_local_by_id(local_id)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/codigo/{codigo}",
    response_model=LocalResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un local por código",
    description="Obtiene los detalles de un local específico por su código único.",
)
async def get_local_by_codigo(
    codigo: str, session: AsyncSession = Depends(get_database_session)
) -> LocalResponse:
    """
    Obtiene un local específico por su código único.

    Args:
        codigo: Código único del local a buscar (ej: CEV-001).
        session: Sesión de base de datos.

    Returns:
        El local encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        return await local_service.get_local_by_codigo(codigo)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=LocalList,
    status_code=status.HTTP_200_OK,
    summary="Listar locales",
    description="Obtiene una lista paginada de locales.",
)
async def list_locales(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> LocalList:
    """
    Obtiene una lista paginada de locales.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de locales y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        return await local_service.get_locales(skip, limit)
    except LocalValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{local_id}",
    response_model=LocalResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un local",
    description="Actualiza los datos de un local existente.",
)
async def update_local(
    local_id: str,
    local_data: LocalUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> LocalResponse:
    """
    Actualiza un local existente.

    Args:
        local_id: ID del local a actualizar.
        local_data: Datos del local a actualizar.
        session: Sesión de base de datos.

    Returns:
        El local actualizado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el local.
            - 409: Si hay un conflicto (e.g., código duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        return await local_service.update_local(local_id, local_data)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LocalConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{local_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un local",
    description="Elimina un local existente del sistema.",
)
async def delete_local(
    local_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina un local existente.

    Args:
        local_id: ID del local a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        local_service = LocalService(session)
        result = await local_service.delete_local(local_id)
        # No es necesario verificar el resultado aquí ya que delete_local
        # lanza LocalNotFoundError si no encuentra el local
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
