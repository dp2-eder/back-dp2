"""
Controlador para la gestión de detalles de división de cuenta en el sistema.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pagos.division_cuenta_detalle_service import DivisionCuentaDetalleService
from src.api.schemas.division_cuenta_detalle_schema import (
    DivisionCuentaDetalleCreate,
    DivisionCuentaDetalleUpdate,
    DivisionCuentaDetalleResponse,
)
from src.business_logic.exceptions.division_cuenta_exceptions import (
    DivisionCuentaValidationError,
    DivisionCuentaNotFoundError,
    DivisionCuentaConflictError,
)

router = APIRouter(
    prefix="/api/v1/divisiones-cuenta-detalle",
    tags=["Detalles de División de Cuenta"],
)


@router.post(
    "",
    response_model=DivisionCuentaDetalleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo detalle de división",
)
async def create_detalle(
    detalle_data: DivisionCuentaDetalleCreate,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Crea un nuevo detalle de división de cuenta.

    - **id_division_cuenta**: ID de la división a la que pertenece (ULID)
    - **id_pedido_producto**: ID del producto del pedido asignado (ULID)
    - **persona_numero**: Número de la persona (1 a N)
    - **monto_asignado**: Monto asignado a esta persona para este item
    """
    try:
        service = DivisionCuentaDetalleService(session)
        detalle = await service.create_detalle(detalle_data)
        await session.commit()
        return detalle
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DivisionCuentaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{detalle_id}",
    response_model=DivisionCuentaDetalleResponse,
    summary="Obtener detalle por ID",
)
async def get_detalle(
    detalle_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene un detalle de división por su ID.

    - **detalle_id**: Identificador único del detalle (ULID)
    """
    try:
        service = DivisionCuentaDetalleService(session)
        return await service.get_detalle_by_id(detalle_id)
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/division/{division_id}",
    response_model=List[DivisionCuentaDetalleResponse],
    summary="Obtener detalles por división",
)
async def get_detalles_by_division(
    division_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene todos los detalles asociados a una división de cuenta.

    - **division_id**: ID de la división de cuenta
    """
    service = DivisionCuentaDetalleService(session)
    return await service.get_detalles_by_division(division_id)


@router.get(
    "/division/{division_id}/persona/{persona_numero}",
    response_model=List[DivisionCuentaDetalleResponse],
    summary="Obtener detalles asignados a una persona",
)
async def get_detalles_by_persona(
    division_id: str,
    persona_numero: int,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene todos los items asignados a una persona específica en una división.

    - **division_id**: ID de la división de cuenta
    - **persona_numero**: Número identificador de la persona (1 a N)
    """
    service = DivisionCuentaDetalleService(session)
    return await service.get_detalles_by_persona(division_id, persona_numero)


@router.patch(
    "/{detalle_id}",
    response_model=DivisionCuentaDetalleResponse,
    summary="Actualizar detalle de división",
)
async def update_detalle(
    detalle_id: str,
    detalle_data: DivisionCuentaDetalleUpdate,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Actualiza un detalle de división existente.

    - **detalle_id**: ID del detalle a actualizar (ULID)
    - Solo se actualizan los campos proporcionados (actualización parcial)
    """
    try:
        service = DivisionCuentaDetalleService(session)
        detalle = await service.update_detalle(detalle_id, detalle_data)
        await session.commit()
        return detalle
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DivisionCuentaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{detalle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar detalle de división",
)
async def delete_detalle(
    detalle_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina un detalle de división por su ID.

    - **detalle_id**: ID del detalle a eliminar (ULID)
    """
    try:
        service = DivisionCuentaDetalleService(session)
        await service.delete_detalle(detalle_id)
        await session.commit()
        return None
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
