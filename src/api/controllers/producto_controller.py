"""
Endpoints para gestión de productos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.menu.producto_service import ProductoService
from src.business_logic.menu.producto_img_service import ProductoImagenService
from src.api.schemas.producto_schema import (
    ProductoBase,
    ProductoCreate,
    ProductoResponse,
    ProductoUpdate,
    ProductoList,
    ProductoCardList,
    ProductoConOpcionesResponse,
    ProductoCompletoUpdateSchema,
    ProductoImagenResponse,
)
from src.business_logic.exceptions.producto_exceptions import (
    ProductoValidationError,
    ProductoNotFoundError,
    ProductoConflictError,
)
from src.business_logic.menu.producto_alergeno_service import ProductoAlergenoService
from src.core.auth_dependencies import get_current_admin

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="Crea un nuevo producto en el sistema con los datos proporcionados.",
)
async def create_producto(
    producto_data: ProductoCreate, session: AsyncSession = Depends(get_database_session)
) -> ProductoResponse:
    """
    Crea un nuevo producto en el sistema.

    Args:
        producto_data: Datos del producto a crear.
        session: Sesión de base de datos.

    Returns:
        El producto creado con todos sus datos.

    Raises:
        HTTPException:
            - 409: Si ya existe un producto con el mismo nombre.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.create_producto(producto_data)
    except ProductoConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.get(
    "/con-alergenos",
    status_code=status.HTTP_200_OK,
    summary="Listar todos los productos con sus alérgenos",
    description="Obtiene una lista de todos los productos, cada uno con su lista de alérgenos asociados.",
)
async def list_productos_con_alergenos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(100, gt=0, le=500, description="Número máximo de registros a retornar"),
    session: AsyncSession = Depends(get_database_session),
):
    """
    Lista todos los productos con sus alérgenos asociados.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista de productos, cada uno con su lista de alérgenos.
    """
    try:
        producto_service = ProductoService(session)
        producto_alergeno_service = ProductoAlergenoService(session)
        productos = await producto_service.get_productos(skip, limit)
        productos_con_alergenos = []
        for producto in productos.items:
            alergenos = await producto_alergeno_service.get_alergenos_by_producto(producto.id)
            productos_con_alergenos.append({
                "producto": producto,
                "alergenos": alergenos
            })
        return {
            "items": productos_con_alergenos,
            "total": productos.total
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.get(
    "/cards",
    response_model=ProductoCardList,
    status_code=status.HTTP_200_OK,
    summary="Listar todos los productos (formato card)",
    description="Obtiene una lista paginada de todos los productos en formato card con información de categoría.",
)
async def list_all_productos_cards(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoCardList:
    """
    Obtiene una lista paginada de TODOS los productos en formato card.

    Este endpoint devuelve todos los productos con información completa de categoría:
    - Datos del producto: ID, nombre, imagen, precio
    - Datos de la categoría: ID, nombre, imagen

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de productos en formato card con información de categoría.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.get_productos_cards_by_categoria(None, skip, limit)
    except ProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/categoria/{categoria_id}/cards",
    response_model=ProductoCardList,
    status_code=status.HTTP_200_OK,
    summary="Listar productos por categoría (formato card)",
    description="Obtiene una lista paginada de productos de una categoría específica en formato card con información completa.",
)
async def list_productos_cards_by_categoria(
    categoria_id: str,
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoCardList:
    """
    Obtiene una lista paginada de productos de una categoría específica en formato card.

    Este endpoint devuelve productos filtrados por categoría con información completa:
    - Datos del producto: ID, nombre, imagen, precio
    - Datos de la categoría: ID, nombre, imagen

    Args:
        categoria_id: ID de la categoría para filtrar productos.
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de productos en formato card con información de categoría.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.get_productos_cards_by_categoria(categoria_id, skip, limit)
    except ProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un producto por ID",
    description="Obtiene los detalles de un producto específico por su ID.",
)
async def get_producto(
    producto_id: str, session: AsyncSession = Depends(get_database_session)
) -> ProductoResponse:
    """
    Obtiene un producto específico por su ID.

    Args:
        producto_id: ID del producto a buscar.
        session: Sesión de base de datos.

    Returns:
        El producto encontrado con todos sus datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el producto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.get_producto_by_id(producto_id)
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{producto_id}/opciones",
    response_model=ProductoConOpcionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener producto con opciones agrupadas por tipo",
    description="Obtiene los detalles completos de un producto con todas sus opciones agrupadas por tipo de opción.",
)
async def get_producto_con_opciones(
    producto_id: str, session: AsyncSession = Depends(get_database_session)
):
    """
    Obtiene un producto específico por su ID con opciones agrupadas por tipo.

    Args:
        producto_id: ID del producto a buscar (ULID).
        session: Sesión de base de datos.

    Returns:
        El producto con descripción, precio y opciones agrupadas por tipo.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el producto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.get_producto_con_opciones(producto_id)
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "/{producto_id}/alergenos",
    status_code=status.HTTP_200_OK,
    summary="Obtener alérgenos de un producto",
    description="Obtiene todos los alérgenos asociados a un producto específico.",
)
async def get_alergenos_by_producto(
    producto_id: str, session: AsyncSession = Depends(get_database_session)
):
    """
    Obtiene todos los alérgenos asociados a un producto específico.

    Args:
        producto_id: ID del producto a buscar (ULID).
        session: Sesión de base de datos.

    Returns:
        Lista de alérgenos asociados al producto.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el producto o no tiene alérgenos.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_alergeno_service = ProductoAlergenoService(session)
        return await producto_alergeno_service.get_alergenos_by_producto(producto_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.get(
    "",
    response_model=ProductoList,
    status_code=status.HTTP_200_OK,
    summary="Listar productos",
    description="Obtiene una lista paginada de productos, opcionalmente filtrados por categoría.",
)
async def list_productos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(
        100, gt=0, le=500, description="Número máximo de registros a retornar"
    ),
    id_categoria: str = Query(None, description="Filtrar productos por ID de categoría"),
    id_mesa: Optional[str] = Query(None, description="ID de mesa (filtra por local de la mesa)"),
    id_local: Optional[str] = Query(None, description="ID de local (filtro directo)"),
    session: AsyncSession = Depends(get_database_session),
) -> ProductoList:
    """
    Obtiene una lista paginada de productos.

    Ejemplos:
    - GET /productos → Todos los productos
    - GET /productos?id_categoria=xyz → Productos de una categoría
    - GET /productos?id_mesa=abc123 → Productos del local de la mesa (con overrides)
    - GET /productos?id_local=xyz789 → Productos del local específico (con overrides)

    Los overrides incluyen: precio, nombre, descripción, disponibilidad.

    Args:
        skip: Número de registros a omitir (offset), por defecto 0.
        limit: Número máximo de registros a retornar, por defecto 100.
        id_categoria: ID de categoría para filtrar productos (opcional).
        id_mesa: ID de mesa para filtrar por su local (el backend resuelve local automáticamente).
        id_local: ID de local para filtrar directamente.
        session: Sesión de base de datos.

    Returns:
        Lista paginada de productos y el número total de registros.

    Raises:
        HTTPException:
            - 400: Si los parámetros de paginación son inválidos o la mesa no tiene local.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        return await producto_service.get_productos(skip, limit, id_categoria, id_mesa, id_local)
    except ProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )

@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un producto",
    description="Elimina un producto existente del sistema.",
)
async def delete_producto(
    producto_id: str, session: AsyncSession = Depends(get_database_session)
) -> None:
    """
    Elimina un producto existente.

    Args:
        producto_id: ID del producto a eliminar.
        session: Sesión de base de datos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el producto.
            - 500: Si ocurre un error interno del servidor.
    """
    try:
        producto_service = ProductoService(session)
        result = await producto_service.delete_producto(producto_id)
        # No es necesario verificar el resultado aquí ya que delete_producto
        # lanza ProductoNotFoundError si no encuentra el producto
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/{producto_id}/imagen",
    response_model=ProductoImagenResponse,
    status_code=status.HTTP_200_OK,
    summary="Subir imagen de producto",
    description="Sube una imagen para un producto específico. La imagen se guarda con el ID del producto como nombre.",
)
async def upload_producto_imagen(
    producto_id: str,
    file: UploadFile = File(..., description="Archivo de imagen (JPG, PNG, WEBP)"),
    session: AsyncSession = Depends(get_database_session),
    current_admin = Depends(get_current_admin)
) -> ProductoImagenResponse:
    """
    Sube una imagen para un producto específico.

    La imagen se guardará en app/static/images/ con el nombre {producto_id}.{extension}.
    Si ya existe una imagen para el producto, será reemplazada.

    Validaciones:
    - Formatos permitidos: JPG, JPEG, PNG, WEBP
    - Tamaño máximo: 5 MB
    - Dimensiones máximas: 2048x2048 px
    - La imagen será optimizada automáticamente

    Args:
        producto_id: ID del producto (ULID).
        file: Archivo de imagen a subir.
        session: Sesión de base de datos.
        current_admin: Usuario administrador autenticado.

    Returns:
        Información sobre la imagen guardada.

    Raises:
        HTTPException:
            - 400: Si el archivo no es válido o excede límites.
            - 401: Si no está autenticado como administrador.
            - 404: Si el producto no existe.
            - 500: Si ocurre un error al guardar la imagen.
    """
    if current_admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación de administrador"
        )

    try:
        # Verificar que el producto existe
        producto_service = ProductoService(session)
        producto = await producto_service.repository.get_by_id(producto_id)
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el producto con ID {producto_id}"
            )

        # Guardar imagen
        imagen_path = await ProductoImagenService.save_producto_image(
            producto_id=producto_id,
            file=file,
            optimize=True
        )

        # Actualizar el campo imagen_path directamente en el repositorio (sin validación de alérgenos)
        await producto_service.repository.update(producto_id, imagen_path=imagen_path)

        return ProductoImagenResponse(
            message="Imagen subida exitosamente",
            producto_id=producto_id,
            imagen_path=imagen_path,
            filename=file.filename
        )

    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise  # Re-lanzar excepciones HTTP ya creadas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la imagen: {str(e)}"
        )


@router.delete(
    "/{producto_id}/imagen",
    response_model=ProductoImagenResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar imagen de producto",
    description="Elimina la imagen asociada a un producto.",
)
async def delete_producto_imagen(
    producto_id: str,
    session: AsyncSession = Depends(get_database_session),
    current_admin = Depends(get_current_admin)
) -> ProductoImagenResponse:
    """
    Elimina la imagen asociada a un producto.

    Args:
        producto_id: ID del producto (ULID).
        session: Sesión de base de datos.
        current_admin: Usuario administrador autenticado.

    Returns:
        Confirmación de eliminación.

    Raises:
        HTTPException:
            - 401: Si no está autenticado como administrador.
            - 404: Si el producto o la imagen no existen.
            - 500: Si ocurre un error al eliminar.
    """
    if current_admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación de administrador"
        )

    try:
        producto_service = ProductoService(session)
        producto = await producto_service.repository.get_by_id(producto_id)
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el producto con ID {producto_id}"
            )

        deleted = ProductoImagenService.delete_producto_image(producto_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró ninguna imagen para este producto"
            )

        # Actualizar imagen_path a None directamente en el repositorio
        await producto_service.repository.update(producto_id, imagen_path=None)

        return ProductoImagenResponse(
            message="Imagen eliminada exitosamente",
            producto_id=producto_id,
            imagen_path=None,
            filename=None
        )

    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise  # Re-lanzar excepciones HTTP ya creadas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la imagen: {str(e)}"
        )


@router.put(
    "/{producto_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductoConOpcionesResponse,
    summary="Actualizar producto",
    description="Actualiza un producto con todos sus datos: alérgenos, secciones, tipos de opciones y opciones.",
)
async def update_producto(
    producto_id: str,
    producto_data: ProductoCompletoUpdateSchema,
    session: AsyncSession = Depends(get_database_session),
    current_admin = Depends(get_current_admin)
):
    """
    Actualiza completamente un producto con todos sus datos relacionados.

    Permite actualizar en una sola operación:
    - Datos básicos del producto (nombre, descripción, precio, etc.)
    - Lista de alérgenos asociados
    - Secciones del producto
    - Tipos de opciones con sus opciones correspondientes

    Args:
        producto_id: ID del producto a actualizar.
        producto_data: Schema con todos los datos del producto a actualizar.
        session: Sesión de base de datos.

    Returns:
        El producto actualizado con todas sus relaciones.

    Raises:
        HTTPException:
            - 400: Si los datos de entrada son inválidos.
            - 404: Si no se encuentra el producto.
            - 409: Si hay conflictos (ej. nombre duplicado).
            - 500: Si ocurre un error interno del servidor.
    """
    if current_admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas para realizar esta operación.",
        )

    try:
        producto_service = ProductoService(session)
        resultado = await producto_service.update_producto_completo(producto_id, producto_data)
        
        # Commit de la transacción si todo salió bien
        await session.commit()
        
        return resultado
    except ProductoValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ProductoNotFoundError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoConflictError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
