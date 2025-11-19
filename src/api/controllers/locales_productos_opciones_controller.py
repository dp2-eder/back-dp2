"""
Endpoints para gestión de relaciones Local-ProductoOpcion.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.locales_productos_opciones_service import (
    LocalesProductosOpcionesService,
    LocalesProductosOpcionesConflictError,
    LocalesProductosOpcionesNotFoundError,
)
from src.api.schemas.locales_productos_opciones_schema import (
    LocalesProductosOpcionesCreate,
    LocalesProductosOpcionesUpdate,
    LocalesProductosOpcionesResponse,
    LocalesProductosOpcionesListResponse,
    ActivarProductoOpcionRequest,
    DesactivarProductoOpcionRequest,
    ActualizarPrecioAdicionalRequest,
    ActivarProductosOpcionesLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionNotFoundError,
)
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError

router = APIRouter(
    prefix="/locales/{id_local}/productos-opciones",
    tags=["Local - Opciones de Productos"],
)


@router.post(
    "",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear relación local-producto_opcion",
    description="Crea una nueva relación entre un local y una opción de producto.",
)
async def create_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_data: LocalesProductosOpcionesCreate = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Crea una nueva relación local-producto_opcion.

    Args:
        id_local: ID del local.
        relacion_data: Datos de la relación a crear.
        session: Sesión de base de datos.

    Returns:
        La relación creada.

    Raises:
        HTTPException:
            - 400: Si el ID del local no coincide.
            - 404: Si no existe el local o la opción de producto.
            - 409: Si ya existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        if relacion_data.id_local != id_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID del local en la URL no coincide con el del body",
            )

        service = LocalesProductosOpcionesService(session)
        return await service.create_relacion(relacion_data)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LocalesProductosOpcionesConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=LocalesProductosOpcionesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar opciones de productos de un local",
    description="Obtiene todas las opciones de productos configuradas para un local específico.",
)
async def list_productos_opciones_by_local(
    id_local: str = Path(..., description="ID del local"),
    activo: bool = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesListResponse:
    """
    Obtiene todas las opciones de productos configuradas para un local.

    Args:
        id_local: ID del local.
        activo: Filtrar por estado activo/inactivo.
        skip: Número de registros a omitir.
        limit: Número máximo de registros.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de relaciones local-producto_opcion.

    Raises:
        HTTPException:
            - 404: Si no existe el local.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosOpcionesService(session)
        return await service.get_productos_opciones_by_local(
            id_local, activo, skip, limit
        )
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{relacion_id}",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener relación por ID",
    description="Obtiene una relación local-producto_opcion específica por su ID.",
)
async def get_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Obtiene una relación local-producto_opcion por su ID.

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
        service = LocalesProductosOpcionesService(session)
        return await service.get_relacion_by_id(relacion_id)
    except LocalesProductosOpcionesNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{relacion_id}",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar relación",
    description="Actualiza una relación local-producto_opcion existente.",
)
async def update_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    relacion_data: LocalesProductosOpcionesUpdate = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Actualiza una relación local-producto_opcion.

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
        service = LocalesProductosOpcionesService(session)
        return await service.update_relacion(relacion_id, relacion_data)
    except LocalesProductosOpcionesNotFoundError as e:
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
    description="Elimina una relación local-producto_opcion.",
)
async def delete_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una relación local-producto_opcion.

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
        service = LocalesProductosOpcionesService(session)
        await service.delete_relacion(relacion_id)
    except LocalesProductosOpcionesNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/activar",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar opción de producto",
    description="Activa una opción de producto para el local con override opcional de precio.",
)
async def activar_producto_opcion(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarProductoOpcionRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Activa una opción de producto para un local con override opcional.

    Args:
        id_local: ID del local.
        request: Datos de la opción a activar con precio override.
        session: Sesión de base de datos.

    Returns:
        La relación creada o actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe el local o la opción de producto.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosOpcionesService(session)
        return await service.activar_producto_opcion(id_local, request)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/desactivar",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar opción de producto",
    description="Desactiva una opción de producto para el local especificado.",
)
async def desactivar_producto_opcion(
    id_local: str = Path(..., description="ID del local"),
    request: DesactivarProductoOpcionRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Desactiva una opción de producto para un local.

    Args:
        id_local: ID del local.
        request: ID de la opción a desactivar.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosOpcionesService(session)
        return await service.desactivar_producto_opcion(
            id_local, request.id_producto_opcion
        )
    except LocalesProductosOpcionesNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.patch(
    "/precio-adicional",
    response_model=LocalesProductosOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar precio adicional",
    description="Actualiza el precio adicional override para una opción en el local.",
)
async def actualizar_precio_adicional(
    id_local: str = Path(..., description="ID del local"),
    request: ActualizarPrecioAdicionalRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesProductosOpcionesResponse:
    """
    Actualiza el precio adicional override para una opción en un local.

    Args:
        id_local: ID del local.
        request: Nuevo precio adicional override.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosOpcionesService(session)
        return await service.actualizar_precio_adicional(id_local, request)
    except LocalesProductosOpcionesNotFoundError as e:
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
    summary="Activar múltiples opciones de productos",
    description="Activa múltiples opciones de productos para el local en una sola operación.",
)
async def activar_productos_opciones_lote(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarProductosOpcionesLoteRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> OperacionLoteResponse:
    """
    Activa múltiples opciones de productos para un local en lote.

    Args:
        id_local: ID del local.
        request: Lista de opciones a activar con precios override.
        session: Sesión de base de datos.

    Returns:
        Resultado de la operación batch.

    Raises:
        HTTPException:
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesProductosOpcionesService(session)
        return await service.activar_productos_opciones_lote(id_local, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
