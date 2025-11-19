"""
Endpoints para gestión de relaciones Local-Producto.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.locales_productos_service import (
    LocalesProductosService,
    LocalesProductosConflictError,
    LocalesProductosNotFoundError,
)
from src.api.schemas.locales_productos_schema import (
    LocalesProductosCreate,
    LocalesProductosUpdate,
    LocalesProductosResponse,
    LocalesProductosListResponse,
    ActivarProductoRequest,
    DesactivarProductoRequest,
    ActualizarOverridesRequest,
    ActivarProductosLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.producto_exceptions import ProductoNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError

router = APIRouter(prefix="/locales/{id_local}/productos", tags=["Local - Productos"])


@router.post(
    "",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear relación local-producto",
    description="Crea una nueva relación entre un local y un producto con overrides opcionales.",
)
async def create_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_data: LocalesProductosCreate = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Crea una nueva relación local-producto.

    Args:
        id_local: ID del local.
        relacion_data: Datos de la relación a crear.
        session: Sesión de base de datos.

    Returns:
        La relación creada.

    Raises:
        HTTPException:
            - 400: Si el ID del local no coincide.
            - 404: Si no existe el local o el producto.
            - 409: Si ya existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        if relacion_data.id_local != id_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID del local en la URL no coincide con el del body",
            )

        service = LocalesProductosService(session)
        return await service.create_relacion(relacion_data)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LocalesProductosConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=LocalesProductosListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar productos de un local",
    description="Obtiene todos los productos configurados para un local específico.",
)
async def list_productos_by_local(
    id_local: str = Path(..., description="ID del local"),
    activo: bool = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosListResponse:
    """
    Obtiene todos los productos configurados para un local.

    Args:
        id_local: ID del local.
        activo: Filtrar por estado activo/inactivo.
        skip: Número de registros a omitir.
        limit: Número máximo de registros.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de relaciones local-producto.

    Raises:
        HTTPException:
            - 404: Si no existe el local.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.get_productos_by_local(id_local, activo, skip, limit)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{relacion_id}",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener relación por ID",
    description="Obtiene una relación local-producto específica por su ID.",
)
async def get_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Obtiene una relación local-producto por su ID.

    Args:
        id_local: ID del local.
        relacion_id: ID de la relación.
        session: Sesión de base de datos.

    Returns:
        La relación encontrada.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.get_relacion_by_id(relacion_id)
    except LocalesProductosNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{relacion_id}",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar relación",
    description="Actualiza una relación local-producto existente.",
)
async def update_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    relacion_data: LocalesProductosUpdate = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Actualiza una relación local-producto.

    Args:
        id_local: ID del local.
        relacion_id: ID de la relación.
        relacion_data: Datos a actualizar.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.update_relacion(relacion_id, relacion_data)
    except LocalesProductosNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{relacion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar relación",
    description="Elimina una relación local-producto.",
)
async def delete_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una relación local-producto.

    Args:
        id_local: ID del local.
        relacion_id: ID de la relación.
        session: Sesión de base de datos.

    Returns:
        No retorna contenido (204).

    Raises:
        HTTPException:
            - 404: Si no se encuentra la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        await service.delete_relacion(relacion_id)
    except LocalesProductosNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/activar",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar producto",
    description="Activa un producto para el local con overrides opcionales.",
)
async def activar_producto(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarProductoRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Activa un producto para un local con overrides opcionales.

    Args:
        id_local: ID del local.
        request: Datos del producto a activar con overrides.
        session: Sesión de base de datos.

    Returns:
        La relación creada o actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe el local o el producto.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.activar_producto(id_local, request)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/desactivar",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar producto",
    description="Desactiva un producto para el local especificado.",
)
async def desactivar_producto(
    id_local: str = Path(..., description="ID del local"),
    request: DesactivarProductoRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Desactiva un producto para un local.

    Args:
        id_local: ID del local.
        request: ID del producto a desactivar.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.desactivar_producto(id_local, request.id_producto)
    except LocalesProductosNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch(
    "/overrides",
    response_model=LocalesProductosResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar overrides",
    description="Actualiza los valores override para un producto en el local.",
)
async def actualizar_overrides(
    id_local: str = Path(..., description="ID del local"),
    request: ActualizarOverridesRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosResponse:
    """
    Actualiza los valores override para un producto en un local.

    Args:
        id_local: ID del local.
        request: Nuevos valores de override.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.actualizar_overrides(id_local, request)
    except LocalesProductosNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/activar-lote",
    response_model=OperacionLoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar múltiples productos",
    description="Activa múltiples productos para el local en una sola operación.",
)
async def activar_productos_lote(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarProductosLoteRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> OperacionLoteResponse:
    """
    Activa múltiples productos para un local en lote.

    Args:
        id_local: ID del local.
        request: Lista de productos a activar con overrides.
        session: Sesión de base de datos.

    Returns:
        Resultado de la operación batch.

    Raises:
        HTTPException:
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosService(session)
        return await service.activar_productos_lote(id_local, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
