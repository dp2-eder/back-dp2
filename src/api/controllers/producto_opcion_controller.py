"""
Endpoints para gestión de opciones de productos.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pedidos.producto_opcion_service import ProductoOpcionService
from src.api.schemas.producto_opcion_schema import (
    ProductoOpcionCreate,
    ProductoOpcionResponse,
    ProductoOpcionUpdate,
    ProductoOpcionList,
)
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionValidationError,
    ProductoOpcionNotFoundError,
    ProductoOpcionConflictError,
)

router = APIRouter(prefix="/producto-opciones", tags=["Producto Opciones"])


@router.post(
    "",
    response_model=ProductoOpcionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva opción de producto",
    description="Crea una nueva opción de producto en el sistema con los datos proporcionados.",
)
async def create_producto_opcion(
    producto_opcion_data: ProductoOpcionCreate, session: AsyncSession = Depends(get_database_session)
) -> ProductoOpcionResponse:
    """
    Crea una nueva opción de producto en el sistema.
    
    Args:
        producto_opcion_data: Datos de la opción de producto a crear.
        session: Sesión de base de datos.

    Returns:
        La opción de producto creada con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe una opción de producto con el mismo nombre.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_opcion_service = ProductoOpcionService(session)
        return await producto_opcion_service.create_producto_opcion(producto_opcion_data)
    except ProductoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{producto_opcion_id}",
    response_model=ProductoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una opción de producto por ID",
    description="Obtiene los detalles de una opción de producto específica por su ID.",
)
async def get_producto_opcion(
    producto_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> ProductoOpcionResponse:
    """
    Obtiene una opción de producto específica por su ID.

    Args:
        producto_opcion_id: ID de la opción de producto a buscar.
        session: Sesión de base de datos.

    Returns:
        La opción de producto encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de producto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_opcion_service = ProductoOpcionService(session)
        return await producto_opcion_service.get_producto_opcion_by_id(producto_opcion_id)
    except ProductoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=ProductoOpcionList,
    status_code=status.HTTP_200_OK,
    summary="Listar opciones de productos",
    description="Obtiene una lista paginada de opciones de productos.",
)
async def list_producto_opciones(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    id_mesa: Optional[str] = Query(None, description="ID de mesa (filtra por local de la mesa)"),
    id_local: Optional[str] = Query(None, description="ID de local (filtro directo)"),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoOpcionList:
    """
    Obtiene una lista paginada de opciones de productos.

    Ejemplos:
    - GET /producto-opciones → Todas las opciones de productos
    - GET /producto-opciones?id_mesa=abc123 → Opciones del local de la mesa (con override de precio_adicional)
    - GET /producto-opciones?id_local=xyz789 → Opciones del local específico (con override de precio_adicional)

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        id_mesa: ID de mesa para filtrar por su local (el backend resuelve local automáticamente).
        id_local: ID de local para filtrar directamente.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de opciones de productos y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos o la mesa no tiene local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_opcion_service = ProductoOpcionService(session)
        return await producto_opcion_service.get_producto_opciones(skip, limit, id_mesa, id_local)
    except ProductoOpcionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{producto_opcion_id}",
    response_model=ProductoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una opción de producto",
    description="Actualiza los datos de una opción de producto existente.",
)
async def update_producto_opcion(
    producto_opcion_id: str,
    producto_opcion_data: ProductoOpcionUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> ProductoOpcionResponse:
    """
    Actualiza una opción de producto existente.

    Args:
        producto_opcion_id: ID de la opción de producto a actualizar.
        producto_opcion_data: Datos de la opción de producto a actualizar.
        session: Sesión de base de datos.

    Returns:
        La opción de producto actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de producto.
            - 409: Si hay un conflicto (e.g., nombre duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_opcion_service = ProductoOpcionService(session)
        return await producto_opcion_service.update_producto_opcion(producto_opcion_id, producto_opcion_data)
    except ProductoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{producto_opcion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una opción de producto",
    description="Elimina una opción de producto existente del sistema.",
)
async def delete_producto_opcion(
    producto_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una opción de producto existente.

    Args:
        producto_opcion_id: ID de la opción de producto a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de producto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_opcion_service = ProductoOpcionService(session)
        result = await producto_opcion_service.delete_producto_opcion(producto_opcion_id)
        # No es necesario verificar el resultado aquí ya que delete_producto_opcion
        # lanza ProductoOpcionNotFoundError si no encuentra la opción
    except ProductoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
