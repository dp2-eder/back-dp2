"""
Servicio para la gestión de relaciones Local-Producto.
"""

from typing import List, Tuple, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.locales_productos_repository import LocalesProductosRepository
from src.repositories.menu.producto_repository import ProductoRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.locales_productos_model import LocalesProductosModel
from src.api.schemas.locales_productos_schema import (
    LocalesProductosCreate,
    LocalesProductosUpdate,
    LocalesProductosResponse,
    LocalesProductosSummary,
    LocalesProductosListResponse,
    ActivarProductoRequest,
    ActualizarOverridesRequest,
    ActivarProductosLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.producto_exceptions import ProductoNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError


class LocalesProductosConflictError(Exception):
    """Excepción para conflictos en relaciones local-producto."""
    pass


class LocalesProductosNotFoundError(Exception):
    """Excepción cuando no se encuentra una relación local-producto."""
    pass


class LocalesProductosService:
    """Servicio para la gestión de relaciones Local-Producto.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con la activación y configuración de productos por local, incluyendo
    overrides de precio, nombre, descripción y disponibilidad.

    Attributes
    ----------
    repository : LocalesProductosRepository
        Repositorio para acceso a datos de relaciones local-producto.
    producto_repository : ProductoRepository
        Repositorio para validar existencia de productos.
    local_repository : LocalRepository
        Repositorio para validar existencia de locales.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy.
        """
        self.repository = LocalesProductosRepository(session)
        self.producto_repository = ProductoRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_relacion(
        self, relacion_data: LocalesProductosCreate
    ) -> LocalesProductosResponse:
        """
        Crea una nueva relación local-producto.

        Parameters
        ----------
        relacion_data : LocalesProductosCreate
            Datos para crear la relación.

        Returns
        -------
        LocalesProductosResponse
            Esquema de respuesta con los datos de la relación creada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        ProductoNotFoundError
            Si no existe el producto especificado.
        LocalesProductosConflictError
            Si ya existe la relación.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(relacion_data.id_local)
        if not local:
            raise LocalNotFoundError(
                f"No se encontró el local con ID {relacion_data.id_local}"
            )

        # Validar que el producto existe
        producto = await self.producto_repository.get_by_id(relacion_data.id_producto)
        if not producto:
            raise ProductoNotFoundError(
                f"No se encontró el producto con ID {relacion_data.id_producto}"
            )

        try:
            # Crear modelo desde los datos
            relacion = LocalesProductosModel(
                id_local=relacion_data.id_local,
                id_producto=relacion_data.id_producto,
                activo=relacion_data.activo,
                precio_override=relacion_data.precio_override,
                disponible_override=relacion_data.disponible_override,
                nombre_override=relacion_data.nombre_override,
                descripcion_override=relacion_data.descripcion_override,
            )

            # Persistir en la base de datos
            created_relacion = await self.repository.create(relacion)

            # Convertir y retornar como esquema de respuesta
            return LocalesProductosResponse.model_validate(created_relacion)
        except IntegrityError:
            raise LocalesProductosConflictError(
                f"Ya existe una relación entre el local {relacion_data.id_local} "
                f"y el producto {relacion_data.id_producto}"
            )

    async def get_relacion_by_id(self, relacion_id: str) -> LocalesProductosResponse:
        """
        Obtiene una relación por su ID.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        LocalesProductosResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        LocalesProductosNotFoundError
            Si no se encuentra la relación.
        """
        relacion = await self.repository.get_by_id(relacion_id)

        if not relacion:
            raise LocalesProductosNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        return LocalesProductosResponse.model_validate(relacion)

    async def get_productos_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> LocalesProductosListResponse:
        """
        Obtiene todos los productos configurados para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        LocalesProductosListResponse
            Lista paginada de relaciones.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        relaciones, total = await self.repository.get_productos_by_local(
            id_local, activo, skip, limit
        )

        items = [LocalesProductosSummary.model_validate(r) for r in relaciones]

        return LocalesProductosListResponse(items=items, total=total)

    async def update_relacion(
        self, relacion_id: str, relacion_data: LocalesProductosUpdate
    ) -> LocalesProductosResponse:
        """
        Actualiza una relación local-producto existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        relacion_data : LocalesProductosUpdate
            Datos a actualizar.

        Returns
        -------
        LocalesProductosResponse
            Esquema de respuesta con los datos actualizados.

        Raises
        ------
        LocalesProductosNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        existing = await self.repository.get_by_id(relacion_id)
        if not existing:
            raise LocalesProductosNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        # Actualizar solo los campos proporcionados
        update_data = relacion_data.model_dump(exclude_unset=True)
        updated_relacion = await self.repository.update(relacion_id, **update_data)

        return LocalesProductosResponse.model_validate(updated_relacion)

    async def delete_relacion(self, relacion_id: str) -> bool:
        """
        Elimina una relación local-producto.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        bool
            True si fue eliminada correctamente.

        Raises
        ------
        LocalesProductosNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        relacion = await self.repository.get_by_id(relacion_id)
        if not relacion:
            raise LocalesProductosNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        result = await self.repository.delete(relacion_id)
        return result

    async def activar_producto(
        self, id_local: str, request: ActivarProductoRequest
    ) -> LocalesProductosResponse:
        """
        Activa un producto para un local específico con overrides opcionales.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarProductoRequest
            Datos del producto a activar con overrides.

        Returns
        -------
        LocalesProductosResponse
            Relación creada o actualizada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        ProductoNotFoundError
            Si no existe el producto especificado.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        # Validar que el producto existe
        producto = await self.producto_repository.get_by_id(request.id_producto)
        if not producto:
            raise ProductoNotFoundError(
                f"No se encontró el producto con ID {request.id_producto}"
            )

        # Activar o actualizar la relación con overrides
        relacion = await self.repository.activate_producto_for_local(
            id_local,
            request.id_producto,
            request.precio_override,
            request.disponible_override,
            request.nombre_override,
            request.descripcion_override,
        )

        return LocalesProductosResponse.model_validate(relacion)

    async def desactivar_producto(
        self, id_local: str, id_producto: str
    ) -> LocalesProductosResponse:
        """
        Desactiva un producto para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.

        Returns
        -------
        LocalesProductosResponse
            Relación actualizada.

        Raises
        ------
        LocalesProductosNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.deactivate_producto_for_local(
            id_local, id_producto
        )

        if not relacion:
            raise LocalesProductosNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y el producto {id_producto}"
            )

        return LocalesProductosResponse.model_validate(relacion)

    async def actualizar_overrides(
        self, id_local: str, request: ActualizarOverridesRequest
    ) -> LocalesProductosResponse:
        """
        Actualiza los valores de override para un producto en un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActualizarOverridesRequest
            Nuevos valores de override.

        Returns
        -------
        LocalesProductosResponse
            Relación actualizada.

        Raises
        ------
        LocalesProductosNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.update_overrides(
            id_local,
            request.id_producto,
            request.precio_override,
            request.disponible_override,
            request.nombre_override,
            request.descripcion_override,
        )

        if not relacion:
            raise LocalesProductosNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y el producto {request.id_producto}"
            )

        return LocalesProductosResponse.model_validate(relacion)

    async def activar_productos_lote(
        self, id_local: str, request: ActivarProductosLoteRequest
    ) -> OperacionLoteResponse:
        """
        Activa múltiples productos para un local en una sola operación.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarProductosLoteRequest
            Lista de productos a activar con sus overrides.

        Returns
        -------
        OperacionLoteResponse
            Resultado de la operación batch.
        """
        exitosos = 0
        fallidos = 0
        detalles = []

        for prod_request in request.productos:
            try:
                relacion = await self.activar_producto(id_local, prod_request)
                detalles.append(relacion)
                exitosos += 1
            except Exception:
                fallidos += 1

        return OperacionLoteResponse(
            exitosos=exitosos, fallidos=fallidos, detalles=detalles
        )
