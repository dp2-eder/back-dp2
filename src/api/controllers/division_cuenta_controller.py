"""
Controlador para la gestión de divisiones de cuenta en el sistema.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.pagos.division_cuenta_service import DivisionCuentaService
from src.api.schemas.division_cuenta_schema import (
    DivisionCuentaCreate,
    DivisionCuentaUpdate,
    DivisionCuentaResponse,
    DivisionCuentaSummary,
    DivisionCuentaList,
)
from src.business_logic.exceptions.division_cuenta_exceptions import (
    DivisionCuentaValidationError,
    DivisionCuentaNotFoundError,
    DivisionCuentaConflictError,
)

router = APIRouter(prefix="/api/v1/divisiones-cuenta", tags=["Divisiones de Cuenta"])


@router.post(
    "",
    response_model=DivisionCuentaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva división de cuenta",
)
async def create_division(
    division_data: DivisionCuentaCreate,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Crea una nueva división de cuenta para un pedido.

    - **id_pedido**: ID del pedido a dividir (ULID)
    - **tipo_division**: Tipo de división ('equitativa', 'por_items', 'manual')
    - **cantidad_personas**: Número de personas entre quienes dividir la cuenta
    - **notas**: Notas adicionales sobre la división (opcional)
    """
    try:
        service = DivisionCuentaService(session)
        division = await service.create_division(division_data)
        await session.commit()
        return division
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DivisionCuentaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{division_id}",
    response_model=DivisionCuentaResponse,
    summary="Obtener división por ID",
)
async def get_division(
    division_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene una división de cuenta por su ID.

    - **division_id**: Identificador único de la división (ULID)
    """
    try:
        service = DivisionCuentaService(session)
        return await service.get_division_by_id(division_id)
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/pedido/{pedido_id}",
    response_model=List[DivisionCuentaResponse],
    summary="Obtener divisiones por pedido",
)
async def get_divisiones_by_pedido(
    pedido_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene todas las divisiones asociadas a un pedido.

    - **pedido_id**: ID del pedido
    """
    service = DivisionCuentaService(session)
    return await service.get_divisiones_by_pedido(pedido_id)


@router.post(
    "/{division_id}/calcular-equitativa",
    response_model=DivisionCuentaResponse,
    summary="Calcular división equitativa",
)
async def calcular_division_equitativa(
    division_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Calcula y aplica una división equitativa del total del pedido entre todas las personas.

    Este endpoint divide el monto total del pedido en partes iguales según la cantidad
    de personas especificada en la división.

    - **division_id**: ID de la división a calcular
    """
    try:
        service = DivisionCuentaService(session)
        division = await service.calcular_division_equitativa(division_id)
        await session.commit()
        return division
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=DivisionCuentaList,
    summary="Listar todas las divisiones de cuenta",
)
async def list_divisiones(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Obtiene una lista paginada de todas las divisiones de cuenta.

    - **skip**: Número de registros a omitir (offset)
    - **limit**: Número máximo de registros a retornar
    """
    try:
        service = DivisionCuentaService(session)
        return await service.get_divisiones(skip, limit)
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/{division_id}",
    response_model=DivisionCuentaResponse,
    summary="Actualizar división de cuenta",
)
async def update_division(
    division_id: str,
    division_data: DivisionCuentaUpdate,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Actualiza una división de cuenta existente.

    - **division_id**: ID de la división a actualizar (ULID)
    - Solo se actualizan los campos proporcionados (actualización parcial)
    """
    try:
        service = DivisionCuentaService(session)
        division = await service.update_division(division_id, division_data)
        await session.commit()
        return division
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DivisionCuentaValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DivisionCuentaConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{division_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar división de cuenta",
)
async def delete_division(
    division_id: str,
    session: AsyncSession = Depends(get_database_session),
):
    """
    Elimina una división de cuenta por su ID.

    - **division_id**: ID de la división a eliminar (ULID)
    """
    try:
        service = DivisionCuentaService(session)
        await service.delete_division(division_id)
        await session.commit()
        return None
    except DivisionCuentaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
