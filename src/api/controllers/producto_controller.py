"""Endpoints para gestión de productos."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.core.auth_dependencies import get_current_admin
from src.business_logic.menu.producto_service import ProductoService
from src.business_logic.menu.producto_img_service import ProductoImagenService
from src.api.schemas.producto_schema import (
    ProductoCreate,
    ProductoResponse,
    ProductoList,
    ProductoCardList,
    ProductoConOpcionesResponse,
    ProductoCompletoUpdateSchema,
    ProductoImagenResponse,
    ProductoUpdate,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def create_producto(
    producto_data: ProductoCreate,
    session: AsyncSession = Depends(get_database_session),
) -> ProductoResponse:
    """Crea un nuevo producto."""
    service = ProductoService(session)
    return await service.create_producto(producto_data)


@router.get("/cards", response_model=ProductoCardList)
async def list_all_productos_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoCardList:
    """Lista todos los productos en formato card."""
    service = ProductoService(session)
    return await service.get_productos_cards_by_categoria(None, skip, limit)


@router.get("/categoria/{categoria_id}/cards", response_model=ProductoCardList)
async def list_productos_cards_by_categoria(
    categoria_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoCardList:
    """Lista productos de una categoría en formato card."""
    service = ProductoService(session)
    return await service.get_productos_cards_by_categoria(categoria_id, skip, limit)


@router.get("/{producto_id}", response_model=ProductoResponse)
async def get_producto(
    producto_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> ProductoResponse:
    """Obtiene un producto por su ID."""
    service = ProductoService(session)
    return await service.get_producto_by_id(producto_id)


@router.get("/{producto_id}/opciones", response_model=ProductoConOpcionesResponse)
async def get_producto_con_opciones(
    producto_id: str,
    session: AsyncSession = Depends(get_database_session),
) -> ProductoConOpcionesResponse:
    """Obtiene un producto con sus opciones agrupadas por tipo."""
    service = ProductoService(session)
    return await service.get_producto_con_opciones(producto_id)


@router.get("", response_model=ProductoList)
async def list_productos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, gt=0, le=500),
    id_categoria: Optional[str] = Query(None),
    id_mesa: Optional[str] = Query(None),
    id_local: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoList:
    """Lista productos con filtros opcionales por categoría, mesa o local."""
    service = ProductoService(session)
    return await service.get_productos(skip, limit, id_categoria, id_mesa, id_local)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_producto(
    producto_id: str,
    session: AsyncSession = Depends(get_database_session),
    _: str = Depends(get_current_admin),
) -> None:
    """Elimina un producto."""
    service = ProductoService(session)
    await service.delete_producto(producto_id)


@router.post("/{producto_id}/imagen", response_model=ProductoImagenResponse)
async def upload_producto_imagen(
    producto_id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_database_session),
    _: str = Depends(get_current_admin),
) -> ProductoImagenResponse:
    """Sube una imagen para un producto. Formatos: JPG, PNG, WEBP. Máx: 5MB."""
    service = ProductoService(session)
    await service.get_producto_by_id(producto_id)
    imagen_path = await ProductoImagenService.save_producto_image(producto_id, file)
    await service.update_producto(
        producto_id=producto_id, producto_data=ProductoUpdate(imagen_path=imagen_path)
    )

    return ProductoImagenResponse(
        message="Imagen subida exitosamente",
        producto_id=producto_id,
        imagen_path=imagen_path,
        filename=file.filename,
    )


@router.put("/{producto_id}", response_model=ProductoConOpcionesResponse)
async def update_producto(
    producto_id: str,
    producto_data: ProductoCompletoUpdateSchema,
    session: AsyncSession = Depends(get_database_session),
    _: str = Depends(get_current_admin),
) -> ProductoConOpcionesResponse:
    """Actualiza completamente un producto con sus alérgenos, tipos de opciones y opciones."""
    service = ProductoService(session)
    await service.update_producto_completo(producto_id, producto_data)
    await session.commit()
    return await service.get_producto_con_opciones(producto_id)
