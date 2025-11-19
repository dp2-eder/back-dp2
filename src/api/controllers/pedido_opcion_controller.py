"""
Endpoints para gestión de opciones de pedidos.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pedidos.pedido_opcion_service import PedidoOpcionService
from src.api.schemas.pedido_opcion_schema import (
    PedidoOpcionCreate,
    PedidoOpcionResponse,
    PedidoOpcionUpdate,
    PedidoOpcionList,
)
from src.business_logic.exceptions.pedido_opcion_exceptions import (
    PedidoOpcionValidationError,
    PedidoOpcionNotFoundError,
    PedidoOpcionConflictError,
)

router = APIRouter(prefix="/pedido-opciones", tags=["Pedido Opciones"])


@router.post(
    "",
    response_model=PedidoOpcionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva opción de pedido",
    description="Crea una nueva opción de pedido en el sistema con los datos proporcionados.",
)
async def create_pedido_opcion(
    pedido_opcion_data: PedidoOpcionCreate, session: AsyncSession = Depends(get_database_session)
) -> PedidoOpcionResponse:
    """
    Crea una nueva opción de pedido en el sistema.

    Args:
        pedido_opcion_data: Datos de la opción de pedido a crear.
        session: Sesión de base de datos.

    Returns:
        La opción de pedido creada con todos sus datos.

    Raises:
        HTTPException:
            - 400: Si los datos de validación son inválidos.
            - 409: Si hay un conflicto al crear la opción.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        return await pedido_opcion_service.create_pedido_opcion(pedido_opcion_data)
    except PedidoOpcionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PedidoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{pedido_opcion_id}",
    response_model=PedidoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una opción de pedido por ID",
    description="Obtiene los detalles de una opción de pedido específica por su ID.",
)
async def get_pedido_opcion(
    pedido_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> PedidoOpcionResponse:
    """
    Obtiene una opción de pedido específica por su ID.

    Args:
        pedido_opcion_id: ID de la opción de pedido a buscar.
        session: Sesión de base de datos.

    Returns:
        La opción de pedido encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de pedido.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        return await pedido_opcion_service.get_pedido_opcion_by_id(pedido_opcion_id)
    except PedidoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/pedido-producto/{pedido_producto_id}/opciones",
    response_model=PedidoOpcionList,
    status_code=status.HTTP_200_OK,
    summary="Obtener opciones de un item de pedido",
    description="Obtiene todas las opciones asociadas a un item de pedido específico.",
)
async def get_opciones_by_pedido_producto(
    pedido_producto_id: str, session: AsyncSession = Depends(get_database_session)
) -> PedidoOpcionList:
    """
    Obtiene todas las opciones de un item de pedido específico.

    Args:
        pedido_producto_id: ID del item de pedido.
        session: Sesión de base de datos.

    Returns:
        Lista de opciones del item de pedido.

    Raises:
        HTTPException:
            - 400: Si el item de pedido no existe.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        return await pedido_opcion_service.get_opciones_by_pedido_producto(pedido_producto_id)
    except PedidoOpcionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=PedidoOpcionList,
    status_code=status.HTTP_200_OK,
    summary="Listar opciones de pedidos",
    description="Obtiene una lista paginada de opciones de pedidos.",
)
async def list_pedido_opciones(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> PedidoOpcionList:
    """
    Obtiene una lista paginada de opciones de pedidos.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de opciones de pedidos y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        return await pedido_opcion_service.get_pedido_opciones(skip, limit)
    except PedidoOpcionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{pedido_opcion_id}",
    response_model=PedidoOpcionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una opción de pedido",
    description="Actualiza los datos de una opción de pedido existente.",
)
async def update_pedido_opcion(
    pedido_opcion_id: str,
    pedido_opcion_data: PedidoOpcionUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> PedidoOpcionResponse:
    """
    Actualiza una opción de pedido existente.

    Args:
        pedido_opcion_id: ID de la opción de pedido a actualizar.
        pedido_opcion_data: Datos de la opción de pedido a actualizar.
        session: Sesión de base de datos.

    Returns:
        La opción de pedido actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de pedido.
            - 409: Si hay un conflicto (e.g., datos inválidos).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        return await pedido_opcion_service.update_pedido_opcion(pedido_opcion_id, pedido_opcion_data)
    except PedidoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PedidoOpcionConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{pedido_opcion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una opción de pedido",
    description="Elimina una opción de pedido existente del sistema.",
)
async def delete_pedido_opcion(
    pedido_opcion_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una opción de pedido existente.

    Args:
        pedido_opcion_id: ID de la opción de pedido a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la opción de pedido.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        pedido_opcion_service = PedidoOpcionService(session)
        result = await pedido_opcion_service.delete_pedido_opcion(pedido_opcion_id)
        # No es necesario verificar el resultado aquí ya que delete_pedido_opcion
        # lanza PedidoOpcionNotFoundError si no encuentra la opción
    except PedidoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
