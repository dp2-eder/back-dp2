"""
Endpoints para gestión de zonas.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.zona_service import ZonaService
from src.api.schemas.zona_schema import (
    ZonaCreate,
    ZonaResponse,
    ZonaUpdate,
    ZonaList,
)
from src.business_logic.exceptions.zona_exceptions import (
    ZonaValidationError,
    ZonaNotFoundError,
    ZonaConflictError,
)

router = APIRouter(prefix="/zonas", tags=["Zonas"])


@router.post(
    "",
    response_model=ZonaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva zona",
    description="Crea una nueva zona en el sistema con los datos proporcionados.",
)
async def create_zona(
    zona_data: ZonaCreate, session: AsyncSession = Depends(get_database_session)
) -> ZonaResponse:
    """
    Crea una nueva zona en el sistema.

    Args:
        zona_data: Datos de la zona a crear.
        session: Sesión de base de datos.

    Returns:
        La zona creada con todos sus datos.

    Raises:
        HTTPException:
            - 400: Si la validación falla (local no existe, nivel inválido).
            - 409: Si hay un conflicto al crear la zona.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.create_zona(zona_data)
    except ZonaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ZonaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{zona_id}",
    response_model=ZonaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una zona por ID",
    description="Obtiene los detalles de una zona específica por su ID.",
)
async def get_zona(
    zona_id: str, session: AsyncSession = Depends(get_database_session)
) -> ZonaResponse:
    """
    Obtiene una zona específica por su ID.

    Args:
        zona_id: ID de la zona a buscar.
        session: Sesión de base de datos.

    Returns:
        La zona encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la zona.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.get_zona_by_id(zona_id)
    except ZonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/local/{local_id}",
    response_model=ZonaList,
    status_code=status.HTTP_200_OK,
    summary="Listar zonas por local",
    description="Obtiene una lista paginada de zonas de un local específico.",
)
async def list_zonas_by_local(
    local_id: str,
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ZonaList:
    """
    Obtiene una lista paginada de zonas de un local.

    Args:
        local_id: ID del local para filtrar zonas.
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de zonas y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.get_zonas_by_local(local_id, skip, limit)
    except ZonaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/nivel/{nivel}",
    response_model=ZonaList,
    status_code=status.HTTP_200_OK,
    summary="Listar zonas por nivel",
    description="Obtiene una lista paginada de zonas filtradas por nivel jerárquico.",
)
async def list_zonas_by_nivel(
    nivel: int,
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ZonaList:
    """
    Obtiene una lista paginada de zonas por nivel jerárquico.

    Args:
        nivel: Nivel jerárquico (0=principal, 1=sub-zona, 2=sub-sub-zona).
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de zonas y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.get_zonas_by_nivel(nivel, skip, limit)
    except ZonaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=ZonaList,
    status_code=status.HTTP_200_OK,
    summary="Listar zonas",
    description="Obtiene una lista paginada de zonas.",
)
async def list_zonas(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ZonaList:
    """
    Obtiene una lista paginada de zonas.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de zonas y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.get_zonas(skip, limit)
    except ZonaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{zona_id}",
    response_model=ZonaResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una zona",
    description="Actualiza los datos de una zona existente.",
)
async def update_zona(
    zona_id: str,
    zona_data: ZonaUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> ZonaResponse:
    """
    Actualiza una zona existente.

    Args:
        zona_id: ID de la zona a actualizar.
        zona_data: Datos de la zona a actualizar.
        session: Sesión de base de datos.

    Returns:
        La zona actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 400: Si la validación falla.
            - 404: Si no se encuentra la zona.
            - 409: Si hay un conflicto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        return await zona_service.update_zona(zona_id, zona_data)
    except ZonaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ZonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ZonaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{zona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una zona",
    description="Elimina una zona existente del sistema.",
)
async def delete_zona(
    zona_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una zona existente.

    Args:
        zona_id: ID de la zona a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la zona.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        zona_service = ZonaService(session)
        result = await zona_service.delete_zona(zona_id)
        # No es necesario verificar el resultado aquí ya que delete_zona
        # lanza ZonaNotFoundError si no encuentra la zona
    except ZonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
