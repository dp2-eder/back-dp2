"""
Endpoints para gestión de relaciones producto-alérgeno.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.menu.producto_alergeno_service import ProductoAlergenoService
from src.api.schemas.producto_alergeno_schema import (
    ProductoAlergenoCreate,
    ProductoAlergenoResponse,
    ProductoAlergenoUpdate,
    ProductoAlergenoList,
)
from src.business_logic.exceptions.producto_alergeno_exceptions import (
    ProductoAlergenoValidationError,
    ProductoAlergenoNotFoundError,
    ProductoAlergenoConflictError,
)

router = APIRouter(prefix="/productos-alergenos", tags=["Productos-Alergenos"])


@router.post(
    "",
    response_model=ProductoAlergenoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva relación producto-alérgeno",
    description="Crea una nueva relación entre un producto y un alérgeno con los datos proporcionados.",
)
async def create_producto_alergeno(
    producto_alergeno_data: ProductoAlergenoCreate,
    session: AsyncSession = Depends(get_database_session)
) -> ProductoAlergenoResponse:
    """
    Crea una nueva relación producto-alérgeno en el sistema.

    Args:
        producto_alergeno_data: Datos de la relación producto-alérgeno a crear.
        session: Sesión de base de datos.

    Returns:
        La relación producto-alérgeno creada con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe una relación con los mismos IDs.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        return await producto_alergeno_service.create_producto_alergeno(producto_alergeno_data)
    except ProductoAlergenoConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{id_producto}/{id_alergeno}",
    response_model=ProductoAlergenoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una relación producto-alérgeno por IDs",
    description="Obtiene los detalles de una relación producto-alérgeno específica por sus IDs.",
)
async def get_producto_alergeno(
    id_producto: str,
    id_alergeno: str,
    session: AsyncSession = Depends(get_database_session)
) -> ProductoAlergenoResponse:
    """
    Obtiene una relación producto-alérgeno específica por sus IDs.

    Args:
        id_producto: ID del producto.
        id_alergeno: ID del alérgeno.
        session: Sesión de base de datos.

    Returns:
        La relación producto-alérgeno encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación producto-alérgeno.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        return await producto_alergeno_service.get_producto_alergeno_by_combination(id_producto, id_alergeno)
    except ProductoAlergenoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=ProductoAlergenoList,
    status_code=status.HTTP_200_OK,
    summary="Listar relaciones producto-alérgeno",
    description="Obtiene una lista paginada de relaciones producto-alérgeno.",
)
async def list_producto_alergenos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoAlergenoList:
    """
    Obtiene una lista paginada de relaciones producto-alérgeno.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de relaciones producto-alérgeno y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        return await producto_alergeno_service.get_producto_alergenos(skip, limit)
    except ProductoAlergenoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{id_producto}/{id_alergeno}",
    response_model=ProductoAlergenoResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una relación producto-alérgeno",
    description="Actualiza los datos de una relación producto-alérgeno existente.",
)
async def update_producto_alergeno(
    id_producto: str,
    id_alergeno: str,
    producto_alergeno_data: ProductoAlergenoUpdate,
    session: AsyncSession = Depends(get_database_session)
) -> ProductoAlergenoResponse:
    """
    Actualiza una relación producto-alérgeno existente.

    Args:
        id_producto: ID del producto.
        id_alergeno: ID del alérgeno.
        producto_alergeno_data: Datos de la relación producto-alérgeno a actualizar.
        session: Sesión de base de datos.

    Returns:
        La relación producto-alérgeno actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación producto-alérgeno.
            - 409: Si hay un conflicto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        return await producto_alergeno_service.update_producto_alergeno_by_combination(
            id_producto, id_alergeno, producto_alergeno_data
        )
    except ProductoAlergenoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoAlergenoConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{id_producto}/{id_alergeno}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una relación producto-alérgeno",
    description="Elimina una relación producto-alérgeno existente del sistema.",
)
async def delete_producto_alergeno(
    id_producto: str,
    id_alergeno: str,
    session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una relación producto-alérgeno existente.

    Args:
        id_producto: ID del producto.
        id_alergeno: ID del alérgeno.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación producto-alérgeno.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        result = await producto_alergeno_service.delete_producto_alergeno_by_combination(id_producto, id_alergeno)
        # No es necesario verificar el resultado aquí ya que delete_producto_alergeno_by_combination
        # lanza ProductoAlergenoNotFoundError si no encuentra la relación
    except ProductoAlergenoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
