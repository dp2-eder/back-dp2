"""Endpoints para gestión de roles."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.rol_service import RolService
from src.api.schemas.rol_schema import RolCreate, RolResponse, RolUpdate, RolList

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
async def create_rol(
    rol_data: RolCreate, 
    session: AsyncSession = Depends(get_database_session)
) -> RolResponse:
    """Crea un nuevo rol en el sistema."""
    service = RolService(session)
    return await service.create_rol(rol_data)


@router.get("/{rol_id}", response_model=RolResponse)
async def get_rol(
    rol_id: str, 
    session: AsyncSession = Depends(get_database_session)
) -> RolResponse:
    """Obtiene un rol por su ID."""
    service = RolService(session)
    return await service.get_rol_by_id(rol_id)


@router.get("/usuario/{usuario_id}/nombre", response_model=dict)
async def get_nombre_rol_usuario(
    usuario_id: str, 
    session: AsyncSession = Depends(get_database_session)
) -> dict:
    """Obtiene el nombre del rol asignado a un usuario."""
    service = RolService(session)
    return await service.get_nombre_rol_by_usuario_id(usuario_id)


@router.get("", response_model=RolList)
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    session: AsyncSession = Depends(get_database_session),
) -> RolList:
    """Lista roles con paginación."""
    service = RolService(session)
    return await service.get_roles(skip, limit)


@router.put("/{rol_id}", response_model=RolResponse)
async def update_rol(
    rol_id: str,
    rol_data: RolUpdate,
    session: AsyncSession = Depends(get_database_session),
) -> RolResponse:
    """Actualiza un rol existente."""
    service = RolService(session)
    return await service.update_rol(rol_id, rol_data)


@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rol(
    rol_id: str, 
    session: AsyncSession = Depends(get_database_session)
) -> None:
    """Elimina un rol."""
    service = RolService(session)
    await service.delete_rol(rol_id)
