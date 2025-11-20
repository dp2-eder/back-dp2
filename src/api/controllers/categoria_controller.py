"""
Endpoints para gestión de categorías.
"""

from typing import Optional
from src.business_logic.menu.categoria_service import CategoriaService
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.api.schemas.categoria_schema import (
    CategoriaCreate,
    CategoriaResponse,
    CategoriaUpdate,
    CategoriaList,
    CategoriaConProductosCardList
)
from src.business_logic.exceptions.categoria_exceptions import (
    CategoriaValidationError,
    CategoriaNotFoundError,
    CategoriaConflictError,
)

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva categoría",
    description="Crea una nueva categoría en el sistema con los datos proporcionados.",
)
async def create_categoria(
    categoria_data: CategoriaCreate, session: AsyncSession = Depends(get_database_session)
) -> CategoriaResponse:
    """
    Crea una nueva categoría en el sistema.

    Args:
        categoria_data: Datos de la categoría a crear.
        session: Sesión de base de datos.

    Returns:
        La categoría creada con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe una categoría con el mismo nombre.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        categoria_service = CategoriaService(session)
        return await categoria_service.create_categoria(categoria_data)
    except CategoriaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=CategoriaList,
    status_code=status.HTTP_200_OK,
    summary="Listar categorías",
    description="Obtiene una lista paginada de categorías.",
)
async def list_categorias(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    activas_only: bool = Query(False, description="Mostrar solo categorías activas"),
    id_mesa: Optional[str] = Query(None, description="ID de mesa (filtra por local de la mesa)"),
    id_local: Optional[str] = Query(None, description="ID de local (filtro directo)"),
    session: AsyncSession = Depends(get_database_session),
) -> CategoriaList:
    """
    Obtiene una lista paginada de categorías.

    Ejemplos:
    - GET /categorias → Todas las categorías
    - GET /categorias?id_mesa=abc123 → Categorías del local de la mesa
    - GET /categorias?id_local=xyz789 → Categorías del local específico

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        activas_only: Si True, solo muestra categorías activas.
        id_mesa: ID de mesa para filtrar por su local (el backend resuelve local automáticamente).
        id_local: ID de local para filtrar directamente.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de categorías y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos o la mesa no tiene local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        categoria_service = CategoriaService(session)
        if activas_only:
            return await categoria_service.get_categorias_activas(skip, limit)
        else:
            return await categoria_service.get_categorias(skip, limit, id_mesa, id_local)
    except CategoriaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una categoría por ID",
    description="Obtiene los detalles de una categoría específica por su ID.",
)
async def get_categoria(
    categoria_id: str, session: AsyncSession = Depends(get_database_session)
) -> CategoriaResponse:
    """
    Obtiene una categoría específica por su ID.

    Args:
        categoria_id: ID de la categoría a buscar.
        session: Sesión de base de datos.

    Returns:
        La categoría encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la categoría.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        categoria_service = CategoriaService(session)
        return await categoria_service.get_categoria_by_id(categoria_id)
    except CategoriaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una categoría",
    description="Actualiza los datos de una categoría existente.",
)
async def update_categoria(
    categoria_id: str,
    categoria_data: CategoriaUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> CategoriaResponse:
    """
    Actualiza una categoría existente.

    Args:
        categoria_id: ID de la categoría a actualizar.
        categoria_data: Datos de la categoría a actualizar.
        session: Sesión de base de datos.

    Returns:
        La categoría actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la categoría.
            - 409: Si hay un conflicto (e.g., nombre duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        categoria_service = CategoriaService(session)
        return await categoria_service.update_categoria(categoria_id, categoria_data)
    except CategoriaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CategoriaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una categoría",
    description="Elimina una categoría existente del sistema.",
)
async def delete_categoria(
    categoria_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una categoría existente.

    Args:
        categoria_id: ID de la categoría a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la categoría.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        categoria_service = CategoriaService(session)
        result = await categoria_service.delete_categoria(categoria_id)
        # No es necesario verificar el resultado aquí ya que delete_categoria
        # lanza CategoriaNotFoundError si no encuentra la categoría
    except CategoriaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.get(
    "/productos/cards",
    response_model=CategoriaConProductosCardList,
    status_code=status.HTTP_200_OK,
    summary="Listar categorías con productos (Cards)",
    description="Obtiene categorías activas incluyendo sus productos.",
)
async def get_categorias_con_productos_cards(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> CategoriaConProductosCardList:
    """
    Obtiene el menú visual (categorías + productos minimal).
    """
    try:
        categoria_service = CategoriaService(session)
        return await categoria_service.get_categorias_con_productos_cards(skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
