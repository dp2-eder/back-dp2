"""Endpoints para gestión de alérgenos."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.alergeno_schema import AlergenoList
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.business_logic.menu.alergeno_service import AlergenoService
from src.core.database import get_database_session

router = APIRouter(prefix="/alergenos", tags=["Alérgenos"])


@router.get(
    "",
    response_model=AlergenoList,
    status_code=status.HTTP_200_OK,
    summary="Listar alérgenos",
    description="Obtiene una lista paginada de alérgenos.",
)
async def list_alergenos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_database_session),
) -> AlergenoList:
    """Obtiene lista paginada de alérgenos.

    Args:
        skip: Offset de paginación (por defecto 0)
        limit: Límite de registros (por defecto 100, máximo 500)
        session: Sesión de base de datos (inyectada)

    Returns:
        Lista paginada de alérgenos y total de registros

    Raises:
        HTTPException: 400 si los parámetros son inválidos, 500 si hay error interno
    """
    try:
        service = AlergenoService(session)
        return await service.get_alergenos(skip, limit)
    except AlergenoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}",
        )
