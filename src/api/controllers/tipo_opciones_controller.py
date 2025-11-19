"""
Endpoints para gestión de tipos de opciones.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pedidos.tipo_opciones_service import TipoOpcionService
from src.api.schemas.tipo_opciones_schema import (
    TipoOpcionCreate,
    TipoOpcionResponse,
    TipoOpcionUpdate,
    TipoOpcionList,
)
from src.business_logic.exceptions.tipo_opciones_exceptions import (
    TipoOpcionValidationError,
    TipoOpcionNotFoundError,
    TipoOpcionConflictError,
)

router = APIRouter(prefix="/tipos-opciones", tags=["Tipos de Opciones"])


@router.post(
    "",
    response_model=TipoOpcionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo tipo de opción",
    description="Crea un nuevo tipo de opción en el sistema con los datos proporcionados.",
)
async def create_tipo_opcion(
    tipo_opcion_data: TipoOpcionCreate, session: AsyncSession = Depends(get_database_session)
) -> TipoOpcionResponse:
    """
    Crea un nuevo tipo de opción en el sistema.
    
    Args:
        tipo_opcion_data: Datos del tipo de opción a crear.
        session: Sesión de base de datos.

    Returns:
        El tipo de opción creado con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe un tipo de opción con el mismo código.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        tipo_opcion_service = TipoOpcionService(session)
        return await tipo_opcion_service.create_tipo_opcion(tipo_opcion_data)
    except TipoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{tipo_opcion_id}",
    response_model=TipoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un tipo de opción por ID",
    description="Obtiene los detalles de un tipo de opción específico por su ID.",
)
async def get_tipo_opcion(
    tipo_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> TipoOpcionResponse:
    """
    Obtiene un tipo de opción específico por su ID.

    Args:
        tipo_opcion_id: ID del tipo de opción a buscar.
        session: Sesión de base de datos.

    Returns:
        El tipo de opción encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el tipo de opción.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        tipo_opcion_service = TipoOpcionService(session)
        return await tipo_opcion_service.get_tipo_opcion_by_id(tipo_opcion_id)
    except TipoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=TipoOpcionList,
    status_code=status.HTTP_200_OK,
    summary="Listar tipos de opciones",
    description="Obtiene una lista paginada de tipos de opciones.",
)
async def list_tipos_opciones(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    id_mesa: Optional[str] = Query(None, description="ID de mesa (filtra por local de la mesa)"),
    id_local: Optional[str] = Query(None, description="ID de local (filtro directo)"),
    session: AsyncSession = Depends(get_database_session),
) -> TipoOpcionList:
    """
    Obtiene una lista paginada de tipos de opciones.

    Ejemplos:
    - GET /tipos-opciones → Todos los tipos de opciones
    - GET /tipos-opciones?id_mesa=abc123 → Tipos de opciones del local de la mesa
    - GET /tipos-opciones?id_local=xyz789 → Tipos de opciones del local específico

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        id_mesa: ID de mesa para filtrar por su local (el backend resuelve local automáticamente).
        id_local: ID de local para filtrar directamente.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de tipos de opciones y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos o la mesa no tiene local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        tipo_opcion_service = TipoOpcionService(session)
        return await tipo_opcion_service.get_tipos_opciones(skip, limit, id_mesa, id_local)
    except TipoOpcionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{tipo_opcion_id}",
    response_model=TipoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un tipo de opción",
    description="Actualiza los datos de un tipo de opción existente.",
)
async def update_tipo_opcion(
    tipo_opcion_id: str,
    tipo_opcion_data: TipoOpcionUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> TipoOpcionResponse:
    """
    Actualiza un tipo de opción existente.

    Args:
        tipo_opcion_id: ID del tipo de opción a actualizar.
        tipo_opcion_data: Datos del tipo de opción a actualizar.
        session: Sesión de base de datos.

    Returns:
        El tipo de opción actualizado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el tipo de opción.
            - 409: Si hay un conflicto (e.g., código duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        tipo_opcion_service = TipoOpcionService(session)
        return await tipo_opcion_service.update_tipo_opcion(tipo_opcion_id, tipo_opcion_data)
    except TipoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TipoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{tipo_opcion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un tipo de opción",
    description="Elimina un tipo de opción existente del sistema.",
)
async def delete_tipo_opcion(
    tipo_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina un tipo de opción existente.

    Args:
        tipo_opcion_id: ID del tipo de opción a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el tipo de opción.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        tipo_opcion_service = TipoOpcionService(session)
        result = await tipo_opcion_service.delete_tipo_opcion(tipo_opcion_id)
        # No es necesario verificar el resultado aquí ya que delete_tipo_opcion
        # lanza TipoOpcionNotFoundError si no encuentra el tipo de opción
    except TipoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

