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
from src.core.auth_dependencies import get_current_admin

router = APIRouter(prefix="/categorias", tags=["Categorías"])


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
    current_admin = Depends(get_current_admin)
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
