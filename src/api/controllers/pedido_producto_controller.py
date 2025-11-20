"""
Endpoints para gestión de items de pedidos (pedido_producto).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pedidos.pedido_producto_service import PedidoProductoService
from src.api.schemas.pedido_producto_schema import (
    PedidoProductoCreate,
    PedidoProductoResponse,
    PedidoProductoUpdate,
    PedidoProductoList,
    PedidoItemList,
)
from src.business_logic.exceptions.pedido_producto_exceptions import (
    PedidoProductoValidationError,
    PedidoProductoNotFoundError,
    PedidoProductoConflictError,
)

router = APIRouter(prefix="/pedidos-productos", tags=["Pedidos Productos"])


@router.post(
    "",
    response_model=PedidoProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo item de pedido",
    description="Crea un nuevo item de pedido. El subtotal se calcula automáticamente.",
)
async def create_pedido_producto(
    item_data: PedidoProductoCreate,
    session: AsyncSession = Depends(get_database_session),
) -> PedidoProductoResponse:
    """
    Crea un nuevo item de pedido en el sistema.

    Args:
        item_data: Datos del item a crear.
        session: Sesión de base de datos.

    Returns:
        El item creado con todos sus datos.

    Raises:
        HTTPException:
            - 400: Si los datos son inválidos o el pedido/producto no existe.
            - 409: Si hay un conflicto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        return await service.create_pedido_producto(item_data)
    except PedidoProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PedidoProductoConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{item_id}",
    response_model=PedidoProductoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un item de pedido por ID",
    description="Obtiene los detalles de un item de pedido específico por su ID.",
)
async def get_pedido_producto(
    item_id: str, session: AsyncSession = Depends(get_database_session)
) -> PedidoProductoResponse:
    """
    Obtiene un item de pedido específico por su ID.

    Args:
        item_id: ID del item a buscar (ULID).
        session: Sesión de base de datos.

    Returns:
        El item encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el item.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        return await service.get_pedido_producto_by_id(item_id)
    except PedidoProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/pedido/{pedido_id}/items",
    response_model=PedidoItemList,
    status_code=status.HTTP_200_OK,
    summary="Obtener items de un pedido",
    description="Obtiene todos los items de un pedido específico con sus opciones.",
)
async def get_items_by_pedido(
    pedido_id: str, session: AsyncSession = Depends(get_database_session)
) -> PedidoItemList:
    """
    Obtiene todos los items de un pedido específico.

    Args:
        pedido_id: ID del pedido (ULID).
        session: Sesión de base de datos.

    Returns:
        Lista de items del pedido.

    Raises:
        HTTPException:
            - 400: Si el pedido no existe.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        return await service.get_productos_by_pedido(pedido_id)
    except PedidoProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=PedidoProductoList,
    status_code=status.HTTP_200_OK,
    summary="Listar items de pedidos",
    description="Obtiene una lista paginada de items de pedidos con filtros opcionales.",
)
async def list_pedidos_productos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    id_pedido: Optional[str] = Query(None, description="Filtrar por ID de pedido"),
    id_producto: Optional[str] = Query(None, description="Filtrar por ID de producto"),
    session: AsyncSession = Depends(get_database_session),
) -> PedidoProductoList:
    """
    Obtiene una lista paginada de items de pedidos.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        id_pedido: Filtrar por ID de pedido (opcional).
        id_producto: Filtrar por ID de producto (opcional).
        session: Sesión de base de datos.

    Returns:
        Lista paginada de items y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        return await service.get_pedidos_productos(skip, limit, id_pedido, id_producto)
    except PedidoProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{item_id}",
    response_model=PedidoProductoResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un item de pedido",
    description="Actualiza los datos de un item de pedido existente. El subtotal se recalcula automáticamente.",
)
async def update_pedido_producto(
    item_id: str,
    item_data: PedidoProductoUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> PedidoProductoResponse:
    """
    Actualiza un item de pedido existente.

    Args:
        item_id: ID del item a actualizar (ULID).
        item_data: Datos del item a actualizar.
        session: Sesión de base de datos.

    Returns:
        El item actualizado con todos sus datos.

    Raises:
        HTTPException:
            - 400: Si los datos son inválidos.
            - 404: Si no se encuentra el item.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        return await service.update_pedido_producto(item_id, item_data)
    except PedidoProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PedidoProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un item de pedido",
    description="Elimina un item de pedido existente del sistema.",
)
async def delete_pedido_producto(
    item_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina un item de pedido existente.

    Args:
        item_id: ID del item a eliminar (ULID).
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el item.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        service = PedidoProductoService(session)
        await service.delete_pedido_producto(item_id)
    except PedidoProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
