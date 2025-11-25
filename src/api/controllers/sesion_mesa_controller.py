"""
Controlador para gestionar las operaciones CRUD de sesiones de mesa.

Provee endpoints REST para crear, leer, actualizar y eliminar sesiones de mesa.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.sesion_mesa_service import SesionMesaService
from src.api.schemas.sesion_mesa_schema import (
    SesionMesaUpdate,
    SesionMesaResponse,
    SesionMesaListResponse,
)
from src.business_logic.exceptions.sesion_mesa_exceptions import (
    SesionMesaValidationError,
    SesionMesaNotFoundError,
    SesionMesaConflictError,
)
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.core.auth_dependencies import get_current_admin

router = APIRouter(prefix="/sesiones-mesas", tags=["Sesiones de Mesa"])


@router.get(
    "/",
    response_model=SesionMesaListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar sesiones de mesa",
    description="Obtiene una lista paginada de sesiones de mesa con filtros opcionales por mesa y estado.",
)
async def list_sesiones_mesa(
    skip: int = 0,
    limit: int = 100,
    id_mesa: str | None = None,
    estado: EstadoSesionMesa | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> SesionMesaListResponse:
    """
    Lista sesiones de mesa con paginación y filtros opcionales.

    Parameters
    ----------
    skip : int, optional
        Número de registros a omitir (offset), por defecto 0.
    limit : int, optional
        Número máximo de registros a retornar, por defecto 100.
    id_mesa : str | None, optional
        Filtrar por ID de mesa específica (ULID).
    estado : EstadoSesionMesa | None, optional
        Filtrar por estado de la sesión (activa, inactiva, cerrada, finalizada).
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionMesaListResponse
        Lista paginada de sesiones de mesa con metadatos (total, page, limit).

    Raises
    ------
    HTTPException
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        return await service.get_sesiones_list(
            skip=skip,
            limit=limit,
            id_mesa=id_mesa,
            estado=estado
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.get(
    "/{sesion_id}",
    response_model=SesionMesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener sesión de mesa por ID",
    description="Obtiene los detalles de una sesión de mesa específica por su ID (ULID de la sesión, no el id_mesa).",
)
async def get_sesion_mesa(
    sesion_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> SesionMesaResponse:
    """
    Obtiene una sesión de mesa por su ID.

    Parameters
    ----------
    sesion_id : str
        ID (ULID) de la sesión de mesa a buscar. Este es el campo 'id' de SesionMesaModel,
        NO el 'id_mesa'. Ejemplo: "01HXXX000000000000000000AA"
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionMesaResponse
        La sesión de mesa encontrada.

    Raises
    ------
    HTTPException
        404 si no se encuentra la sesión de mesa.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        return await service.get_sesion_by_id(sesion_id)
    except SesionMesaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.patch(
    "/{sesion_id}",
    response_model=SesionMesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar sesión de mesa",
    description="Actualiza parcialmente una sesión de mesa existente. Permite cambiar el estado (ACTIVA, INACTIVA, CERRADA) y otros campos.",
)
async def update_sesion_mesa(
    sesion_id: str,
    sesion_data: SesionMesaUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> SesionMesaResponse:
    """
    Actualiza una sesión de mesa existente.

    Permite actualizar el estado de la sesión. Si se cambia el estado a CERRADA o FINALIZADA,
    se actualiza automáticamente la fecha_fin.

    Parameters
    ----------
    sesion_id : str
        ID (ULID) de la sesión de mesa a actualizar. Este es el campo 'id' de SesionMesaModel,
        NO el 'id_mesa'. Ejemplo: "01HXXX000000000000000000AA"
    sesion_data : SesionMesaUpdate
        Datos a actualizar (estado, fecha_fin).
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionMesaResponse
        La sesión de mesa actualizada.

    Raises
    ------
    HTTPException
        400 si los datos no son válidos.
        404 si no se encuentra la sesión de mesa.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        sesion = await service.update_sesion_mesa(sesion_id, sesion_data)
        await session.commit()
        return sesion
    except SesionMesaNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SesionMesaValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.patch(
    "/{sesion_id}/cerrar",
    response_model=SesionMesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión de mesa",
    description="Cierra una sesión de mesa cambiando su estado a CERRADO y actualizando la fecha_fin.",
)
async def cerrar_sesion_mesa(
    sesion_id: str,
    session: AsyncSession = Depends(get_database_session),
    current_admin = Depends(get_current_admin)
) -> SesionMesaResponse:
    """
    Cierra una sesión de mesa.

    Cambia el estado de la sesión a CERRADO y establece la fecha_fin al momento actual.
    Una sesión cerrada no puede ser reactivada.

    Parameters
    ----------
    sesion_id : str
        ID (ULID) de la sesión de mesa a cerrar. Este es el campo 'id' de SesionMesaModel,
        NO el 'id_mesa'. Ejemplo: "01HXXX000000000000000000AA"
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionMesaResponse
        La sesión de mesa cerrada.

    Raises
    ------
    HTTPException
        400 si la sesión ya está cerrada.
        404 si no se encuentra la sesión de mesa.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        sesion = await service.cerrar_sesion(sesion_id)
        await session.commit()
        return sesion
    except SesionMesaNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SesionMesaValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.patch(
    "/cerrar-por-token/{token_sesion}",
    response_model=SesionMesaResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión de mesa por token",
    description="Cierra una sesión de mesa usando el token compartido. "
    "Este endpoint permite a los clientes cerrar su sesión cuando terminan de consumir.",
)
async def cerrar_sesion_mesa_por_token(
    token_sesion: str,
    session: AsyncSession = Depends(get_database_session),
) -> SesionMesaResponse:
    """
    Cierra una sesión de mesa usando el token.

    Cambia el estado de la sesión a CERRADO y establece la fecha_fin al momento actual.
    Una sesión cerrada no puede ser reactivada.

    Parameters
    ----------
    token_sesion : str
        Token de la sesión de mesa a cerrar (ULID de 26 caracteres).
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Returns
    -------
    SesionMesaResponse
        La sesión de mesa cerrada.

    Raises
    ------
    HTTPException
        400 si la sesión ya está cerrada.
        404 si no se encuentra la sesión de mesa.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        sesion = await service.cerrar_sesion_por_token(token_sesion)
        await session.commit()
        return sesion
    except SesionMesaNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SesionMesaValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )


@router.delete(
    "/{sesion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar sesión de mesa",
    description="Elimina una sesión de mesa del sistema.",
)
async def delete_sesion_mesa(
    sesion_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una sesión de mesa.

    Parameters
    ----------
    sesion_id : str
        ID (ULID) de la sesión de mesa a eliminar. Este es el campo 'id' de SesionMesaModel,
        NO el 'id_mesa'. Ejemplo: "01HXXX000000000000000000AA"
    session : AsyncSession
        Sesión de base de datos proporcionada por FastAPI.

    Raises
    ------
    HTTPException
        404 si no se encuentra la sesión de mesa.
        500 si ocurre un error inesperado.
    """
    try:
        service = SesionMesaService(session)
        await service.delete_sesion_mesa(sesion_id)
        await session.commit()
    except SesionMesaNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )

