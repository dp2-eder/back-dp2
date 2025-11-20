from typing import List


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_database_session
from src.business_logic.mesas.mesa_service import MesaService
from src.api.schemas.mesa_schema import (
    MesaCreate,
    MesaResponse,
    MesaUpdate,
    MesaList,
)
from src.business_logic.exceptions.mesa_exceptions import (
    MesaValidationError,
    MesaNotFoundError,
    MesaConflictError,
)

router = APIRouter(prefix="/mesas", tags=["Mesas"])

@router.post(
    "/batch",
    response_model=List[MesaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Crear múltiples mesas (batch)",
    description="Crea varias mesas en una sola operación batch.",
)
async def batch_create_mesas(
    mesas_data: List[MesaCreate],
    session: AsyncSession = Depends(get_database_session),
) -> List[MesaResponse]:
    """
    Crea múltiples mesas en una sola operación batch.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.batch_create_mesas(mesas_data)
    except MesaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.delete(
    "/batch",
    status_code=status.HTTP_200_OK,
    summary="Eliminar múltiples mesas (batch)",
    description="Elimina varias mesas en una sola operación batch.",
)
async def batch_delete_mesas(
    mesa_ids: List[str],
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """
    Elimina múltiples mesas en una sola operación batch.
    """
    try:
        mesa_service = MesaService(session)
        deleted_count = await mesa_service.batch_delete_mesas(mesa_ids)
        return {"deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
"""
Endpoints para gestión de mesas.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.mesa_service import MesaService
from src.api.schemas.mesa_schema import (
    MesaCreate,
    MesaResponse,
    MesaUpdate,
    MesaList,
)
from src.api.schemas.mesa_schema_detalle import MesaDetalleResponse
from src.api.schemas.local_schema import LocalResponse
from src.business_logic.exceptions.mesa_exceptions import (
    MesaValidationError,
    MesaNotFoundError,
    MesaConflictError,
)

router = APIRouter(prefix="/mesas", tags=["Mesas"])


@router.post(
    "",
    response_model=MesaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva mesa",
    description="Crea una nueva mesa en el sistema con los datos proporcionados.",
)
async def create_mesa(
    mesa_data: MesaCreate, session: AsyncSession = Depends(get_database_session)
) -> MesaResponse:
    """
    Crea una nueva mesa en el sistema.

    Args:
        mesa_data: Datos de la mesa a crear.
        session: Sesión de base de datos.

    Returns:
        La mesa creada con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe una mesa con el mismo número.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.create_mesa(mesa_data)
    except MesaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{mesa_id}",
    response_model=MesaDetalleResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una mesa por ID",
    description="Obtiene los detalles de una mesa específica por su ID.",
)
async def get_mesa(
    mesa_id: str, session: AsyncSession = Depends(get_database_session)
) -> MesaDetalleResponse:
    """
    Obtiene una mesa específica por su ID.

    Args:
        mesa_id: ID de la mesa a buscar.
        session: Sesión de base de datos.

    Returns:
        La mesa encontrada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la mesa.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.get_mesa_by_id(mesa_id)
    except MesaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=MesaList,
    status_code=status.HTTP_200_OK,
    summary="Listar mesas",
    description="Obtiene una lista paginada de mesas.",
)
async def list_mesas(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> MesaList:
    """
    Obtiene una lista paginada de mesas.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de mesas y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.get_mesas(skip, limit)
    except MesaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.put(
    "/{mesa_id}",
    response_model=MesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una mesa",
    description="Actualiza los datos de una mesa existente.",
)
async def update_mesa(
    mesa_id: str,
    mesa_data: MesaUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> MesaResponse:
    """
    Actualiza una mesa existente.

    Args:
        mesa_id: ID de la mesa a actualizar.
        mesa_data: Datos de la mesa a actualizar.
        session: Sesión de base de datos.

    Returns:
        La mesa actualizada con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la mesa.
            - 409: Si hay un conflicto (e.g., nombre duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.update_mesa(mesa_id, mesa_data)
    except MesaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MesaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.delete(
    "/{mesa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una mesa",
    description="Elimina una mesa existente del sistema.",
)
async def delete_mesa(
    mesa_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina una mesa existente.

    Args:
        mesa_id: ID de la mesa a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la mesa.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        result = await mesa_service.delete_mesa(mesa_id)
        # No es necesario verificar el resultado aquí ya que delete_mesa
        # lanza MesaNotFoundError si no encuentra la mesa
    except MesaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{mesa_id}/local",
    response_model=LocalResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener local por mesa",
    description="Obtiene el local asociado a una mesa (via zona).",
)
async def get_local_by_mesa(
    mesa_id: str, session: AsyncSession = Depends(get_database_session)
) -> LocalResponse:
    """
    Obtiene el local asociado a una mesa específica.

    El local se obtiene siguiendo la relación: Mesa → Zona → Local.

    Args:
        mesa_id: ID de la mesa.
        session: Sesión de base de datos.

    Returns:
        El local completo con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra la mesa.
            - 400: Si la mesa no tiene zona o la zona no tiene local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        return await mesa_service.get_local_by_mesa(mesa_id)
    except MesaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MesaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/qr/urls",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Listar URLs de QR para todas las mesas",
    description="Genera las URLs de QR para todas las mesas del sistema.",
)
async def list_qr_urls(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> List[dict]:
    """
    Genera las URLs de QR para todas las mesas.

    Retorna una lista con el ID de cada mesa y su URL de QR correspondiente.
    Formato: https://front-dp2.onrender.com/login?{idMesa}

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista con objetos conteniendo id_mesa, numero_mesa y qr_url.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        mesa_service = MesaService(session)
        mesas_list = await mesa_service.get_mesas(skip, limit)

        qr_urls = []
        for mesa in mesas_list.items:
            qr_urls.append({
                "id_mesa": mesa.id,
                "numero_mesa": mesa.numero,
                "qr_url": f"https://front-dp2.onrender.com/login?{mesa.id}"
            })

        return qr_urls
    except MesaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
