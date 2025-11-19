"""
Controlador para gestionar las operaciones CRUD de sesiones.

Provee endpoints REST para crear, leer, actualizar y eliminar sesiones.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.sesion_service import SesionService
from src.api.schemas.sesion_schema import (
    SesionCreate,
    SesionUpdate,
    SesionResponse,
    SesionList,
)
from src.core.enums.sesion_enums import EstadoSesion
from src.business_logic.exceptions.sesion_exceptions import (
    SesionValidationError,
    SesionNotFoundError,
    SesionConflictError,
)

router = APIRouter(prefix="/sesiones", tags=["Sesiones"])


@router.post(
    "/",
    response_model=SesionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva sesión",
    description="Crea una nueva sesión en el sistema con los datos proporcionados.",
)
async def create_sesion(
    sesion_data: SesionCreate,
    session: AsyncSession = Depends(get_database_session),
) -> SesionResponse:
    """
    Crea una nueva sesión.

    Parameters
    ----------
    sesion_data : SesionCreate
        Datos de la sesión a crear.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionResponse
        La sesión creada.

    Raises
    ------
    HTTPException
        400 si los datos no son válidos.
        409 si hay un conflicto al crear la sesión.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        sesion = await service.create_sesion(sesion_data)
        await session.commit()
        return sesion
    except SesionValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SesionConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.get(
    "/{sesion_id}",
    response_model=SesionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener sesión por ID",
    description="Obtiene los detalles de una sesión específica por su ID.",
)
async def get_sesion(
    sesion_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> SesionResponse:
    """
    Obtiene una sesión por su ID.

    Parameters
    ----------
    sesion_id : str
        ID de la sesión a buscar.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionResponse
        La sesión encontrada.

    Raises
    ------
    HTTPException
        404 si no se encuentra la sesión.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        return await service.get_sesion_by_id(sesion_id)
    except SesionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.get(
    "/",
    response_model=SesionList,
    status_code=status.HTTP_200_OK,
    summary="Listar sesiones",
    description="Obtiene una lista paginada de sesiones con filtros opcionales.",
)
async def list_sesiones(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número de registros a retornar"),
    estado: Optional[EstadoSesion] = Query(None, description="Filtrar por estado de la sesión"),
    session: AsyncSession = Depends(get_database_session),
) -> SesionList:
    """
    Lista todas las sesiones con paginación y filtro opcional por estado.

    Parameters
    ----------
    skip : int
        Número de registros a omitir (offset).
    limit : int
        Número máximo de registros a retornar.
    estado : Optional[EstadoSesion]
        Estado para filtrar sesiones (opcional).
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionList
        Lista de sesiones con total.

    Raises
    ------
    HTTPException
        400 si los parámetros no son válidos.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        return await service.get_sesiones(skip=skip, limit=limit, estado=estado)
    except SesionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.get(
    "/local/{local_id}",
    response_model=SesionList,
    status_code=status.HTTP_200_OK,
    summary="Listar sesiones por local",
    description="Obtiene una lista paginada de sesiones filtradas por local.",
)
async def list_sesiones_by_local(
    local_id: str,
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número de registros a retornar"),
    session: AsyncSession = Depends(get_database_session),
) -> SesionList:
    """
    Lista sesiones filtradas por local con paginación.

    Parameters
    ----------
    local_id : str
        ID del local para filtrar.
    skip : int
        Número de registros a omitir (offset).
    limit : int
        Número máximo de registros a retornar.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionList
        Lista de sesiones del local con total.

    Raises
    ------
    HTTPException
        400 si los parámetros no son válidos.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        return await service.get_sesiones_by_local(local_id, skip=skip, limit=limit)
    except SesionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.get(
    "/estado/{estado}",
    response_model=SesionList,
    status_code=status.HTTP_200_OK,
    summary="Listar sesiones por estado",
    description="Obtiene una lista paginada de sesiones filtradas por estado.",
)
async def list_sesiones_by_estado(
    estado: EstadoSesion,
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número de registros a retornar"),
    session: AsyncSession = Depends(get_database_session),
) -> SesionList:
    """
    Lista sesiones filtradas por estado con paginación.

    Parameters
    ----------
    estado : EstadoSesion
        Estado para filtrar (ACTIVO, INACTIVO, CERRADO).
    skip : int
        Número de registros a omitir (offset).
    limit : int
        Número máximo de registros a retornar.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionList
        Lista de sesiones con ese estado con total.

    Raises
    ------
    HTTPException
        400 si los parámetros no son válidos.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        return await service.get_sesiones_by_estado(estado, skip=skip, limit=limit)
    except SesionValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.patch(
    "/{sesion_id}",
    response_model=SesionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar sesión",
    description="Actualiza parcialmente una sesión existente.",
)
async def update_sesion(
    sesion_id: str,
    sesion_data: SesionUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> SesionResponse:
    """
    Actualiza una sesión existente.

    Parameters
    ----------
    sesion_id : str
        ID de la sesión a actualizar.
    sesion_data : SesionUpdate
        Datos a actualizar.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionResponse
        La sesión actualizada.

    Raises
    ------
    HTTPException
        400 si los datos no son válidos.
        404 si no se encuentra la sesión.
        409 si hay un conflicto al actualizar.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        sesion = await service.update_sesion(sesion_id, sesion_data)
        await session.commit()
        return sesion
    except SesionNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SesionValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SesionConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.delete(
    "/{sesion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar sesión",
    description="Elimina una sesión del sistema.",
)
async def delete_sesion(
    sesion_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una sesión.

    Parameters
    ----------
    sesion_id : str
        ID de la sesión a eliminar.
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Raises
    ------
    HTTPException
        404 si no se encuentra la sesión.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionService(session)
        await service.delete_sesion(sesion_id)
        await session.commit()
    except SesionNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )
