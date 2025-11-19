"""
Endpoints para gestión de relaciones Local-Categoría.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.locales_categorias_service import (
    LocalesCategoriasService,
    LocalesCategoriasConflictError,
    LocalesCategoriasNotFoundError,
)
from src.api.schemas.locales_categorias_schema import (
    LocalesCategoriasCreate,
    LocalesCategoriasUpdate,
    LocalesCategoriasResponse,
    LocalesCategoriasListResponse,
    ActivarCategoriaRequest,
    DesactivarCategoriaRequest,
    ActivarCategoriasLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.categoria_exceptions import CategoriaNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError

router = APIRouter(
    prefix="/locales/{id_local}/categorias", tags=["Local - Categorías"]
)


@router.post(
    "",
    response_model=LocalesCategoriasResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear relación local-categoría",
    description="Crea una nueva relación entre un local y una categoría.",
)
async def create_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_data: LocalesCategoriasCreate = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasResponse:
    """
    Crea una nueva relación local-categoría.

    Args:
        id_local: ID del local.
        relacion_data: Datos de la relación a crear.
        session: Sesión de base de datos.

    Returns:
        La relación creada.

    Raises:
        HTTPException:
            - 404: Si no existe el local o la categoría.
            - 409: Si ya existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        # Validar que el id_local en el path coincide con el del body
        if relacion_data.id_local != id_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ID del local en la URL no coincide con el del body",
            )

        service = LocalesCategoriasService(session)
        return await service.create_relacion(relacion_data)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CategoriaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except LocalesCategoriasConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=LocalesCategoriasListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar categorías de un local",
    description="Obtiene todas las categorías configuradas para un local específico.",
)
async def list_categorias_by_local(
    id_local: str = Path(..., description="ID del local"),
    activo: bool = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasListResponse:
    """
    Obtiene todas las categorías configuradas para un local.

    Args:
        id_local: ID del local.
        activo: Filtrar por estado activo/inactivo.
        skip: Número de registros a omitir.
        limit: Número máximo de registros.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de relaciones local-categoría.

    Raises:
        HTTPException:
            - 404: Si no existe el local.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesCategoriasService(session)
        return await service.get_categorias_by_local(id_local, activo, skip, limit)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{relacion_id}",
    response_model=LocalesCategoriasResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener relación por ID",
    description="Obtiene una relación local-categoría específica por su ID.",
)
async def get_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasResponse:
    """
    Obtiene una relación local-categoría por su ID.

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
        service = LocalesCategoriasService(session)
        return await service.get_relacion_by_id(relacion_id)
    except LocalesCategoriasNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{relacion_id}",
    response_model=LocalesCategoriasResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar relación",
    description="Actualiza una relación local-categoría existente.",
)
async def update_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    relacion_data: LocalesCategoriasUpdate = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasResponse:
    """
    Actualiza una relación local-categoría.

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
        service = LocalesCategoriasService(session)
        return await service.update_relacion(relacion_id, relacion_data)
    except LocalesCategoriasNotFoundError as e:
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
    description="Elimina una relación local-categoría.",
)
async def delete_relacion(
    id_local: str = Path(..., description="ID del local"),
    relacion_id: str = Path(..., description="ID de la relación"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una relación local-categoría.

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
        service = LocalesCategoriasService(session)
        await service.delete_relacion(relacion_id)
    except LocalesCategoriasNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/activar",
    response_model=LocalesCategoriasResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar categoría",
    description="Activa una categoría para el local especificado.",
)
async def activar_categoria(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarCategoriaRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasResponse:
    """
    Activa una categoría para un local.

    Args:
        id_local: ID del local.
        request: Datos de la categoría a activar.
        session: Sesión de base de datos.

    Returns:
        La relación creada o actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe el local o la categoría.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesCategoriasService(session)
        return await service.activar_categoria(id_local, request)
    except LocalNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CategoriaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/desactivar",
    response_model=LocalesCategoriasResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar categoría",
    description="Desactiva una categoría para el local especificado.",
)
async def desactivar_categoria(
    id_local: str = Path(..., description="ID del local"),
    request: DesactivarCategoriaRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> LocalesCategoriasResponse:
    """
    Desactiva una categoría para un local.

    Args:
        id_local: ID del local.
        request: ID de la categoría a desactivar.
        session: Sesión de base de datos.

    Returns:
        La relación actualizada.

    Raises:
        HTTPException:
            - 404: Si no existe la relación.
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesCategoriasService(session)
        return await service.desactivar_categoria(id_local, request.id_categoria)
    except LocalesCategoriasNotFoundError as e:
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
    summary="Activar múltiples categorías",
    description="Activa múltiples categorías para el local en una sola operación.",
)
async def activar_categorias_lote(
    id_local: str = Path(..., description="ID del local"),
    request: ActivarCategoriasLoteRequest = ...,
    session: AsyncSession = Depends(get_database_session),
) -> OperacionLoteResponse:
    """
    Activa múltiples categorías para un local en lote.

    Args:
        id_local: ID del local.
        request: Lista de categorías a activar.
        session: Sesión de base de datos.

    Returns:
        Resultado de la operación batch.

    Raises:
        HTTPException:
            - 500: Error interno del servidor.
    """
    try:
        service = LocalesCategoriasService(session)
        return await service.activar_categorias_lote(id_local, request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
