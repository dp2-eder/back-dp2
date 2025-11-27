"""
Endpoints para gestión de relaciones Local-TipoOpcion.
"""

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.locales_tipos_opciones_service import (
    LocalesTiposOpcionesService,
    LocalesTiposOpcionesConflictError,
    LocalesTiposOpcionesNotFoundError,
)
from src.api.schemas.locales_tipos_opciones_schema import (
    LocalesTiposOpcionesCreate,
    LocalesTiposOpcionesUpdate,
    LocalesTiposOpcionesResponse,
    LocalesTiposOpcionesListResponse,
    ActivarTipoOpcionRequest,
    DesactivarTipoOpcionRequest,
    ActivarTiposOpcionesLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.tipo_opciones_exceptions import TipoOpcionNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError

router = APIRouter(
    prefix="/locales/{id_local}/tipos-opciones", tags=["Local - Tipos de Opciones"]
)


@router.post(
    "",
    response_model=LocalesTiposOpcionesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear relación local-tipo_opcion",
    description="Crea una nueva relación entre un local y un tipo de opción.",
)
async def create_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_data: LocalesTiposOpcionesCreate = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesResponse:
    """
    Crea una nueva relación local-tipo_opcion.

    Args:
        id_local: ID del local.
        relacion_data: Datos de la relación a crear.
        session: Sesión de base de datos.

    Returns:
        La relación creada.

    Raises:
        HTTPException:
            - 400: Si el ID del local no coincide.
            - 404: Si no existe el local o el tipo de opción.
            - 409: Si ya existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        if relacion_data.id_local != id_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID del local en la URL no coincide con el del body",
            )

        service = LocalesTiposOpcionesService(session)
        return await service.create_relacion(relacion_data)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TipoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LocalesTiposOpcionesConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=LocalesTiposOpcionesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar tipos de opciones de un local",
    description="Obtiene todos los tipos de opciones configurados para un local específico.",
)
async def list_tipos_opciones_by_local(
    id_local: str = Path(..., description="ID del local"),
    activo: bool = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesListResponse:
    """
    Obtiene todos los tipos de opciones configurados para un local.

    Args:
        id_local: ID del local.
        activo: Filtrar por estado activo/inactivo.
        skip: Número de registros a omitir.
        limit: Número máximo de registros.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de relaciones local-tipo_opcion.

    Raises:
        HTTPException:
            - 404: Si no existe el local.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesTiposOpcionesService(session)
        return await service.get_tipos_opciones_by_local(id_local, activo, skip, limit)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{relacion_id}",
    response_model=LocalesTiposOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener relación por ID",
    description="Obtiene una relación local-tipo_opcion específica por su ID.",
)
async def get_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesResponse:
    """
    Obtiene una relación local-tipo_opcion por su ID.

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
        service = LocalesTiposOpcionesService(session)
        return await service.get_relacion_by_id(relacion_id)
    except LocalesTiposOpcionesNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{relacion_id}",
    response_model=LocalesTiposOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar relación",
    description="Actualiza una relación local-tipo_opcion existente.",
)
async def update_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    relacion_data: LocalesTiposOpcionesUpdate = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesResponse:
    """
    Actualiza una relación local-tipo_opcion.

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
        service = LocalesTiposOpcionesService(session)
        return await service.update_relacion(relacion_id, relacion_data)
    except LocalesTiposOpcionesNotFoundError as e:
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
    description="Elimina una relación local-tipo_opcion.",
)
async def delete_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una relación local-tipo_opcion.

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
        service = LocalesTiposOpcionesService(session)
        await service.delete_relacion(relacion_id)
    except LocalesTiposOpcionesNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/activar",
    response_model=LocalesTiposOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar tipo de opción",
    description="Activa un tipo de opción para el local especificado.",
)
async def activar_tipo_opcion(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarTipoOpcionRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesResponse:
    """
    Activa un tipo de opción para un local.

    Args:
        id_local: ID del local.
        request: Datos del tipo de opción a activar.
        session: Sesión de base de datos.

    Returns:
        La relación creada o actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe el local o el tipo de opción.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesTiposOpcionesService(session)
        return await service.activar_tipo_opcion(id_local, request)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TipoOpcionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/desactivar",
    response_model=LocalesTiposOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar tipo de opción",
    description="Desactiva un tipo de opción para el local especificado.",
)
async def desactivar_tipo_opcion(
    id_local: str = Path(..., description="ID del local"),
    request: DesactivarTipoOpcionRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesTiposOpcionesResponse:
    """
    Desactiva un tipo de opción para un local.

    Args:
        id_local: ID del local.
        request: ID del tipo de opción a desactivar.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesTiposOpcionesService(session)
        return await service.desactivar_tipo_opcion(id_local, request.id_tipo_opcion)
    except LocalesTiposOpcionesNotFoundError as e:
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
    summary="Activar múltiples tipos de opciones",
    description="Activa múltiples tipos de opciones para el local en una sola operación.",
)
async def activar_tipos_opciones_lote(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarTiposOpcionesLoteRequest = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> OperacionLoteResponse:
    """
    Activa múltiples tipos de opciones para un local en lote.

    Args:
        id_local: ID del local.
        request: Lista de tipos de opciones a activar.
        session: Sesión de base de datos.

    Returns:
        Resultado de la operación batch.

    Raises:
        HTTPException:
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesTiposOpcionesService(session)
        return await service.activar_tipos_opciones_lote(id_local, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
