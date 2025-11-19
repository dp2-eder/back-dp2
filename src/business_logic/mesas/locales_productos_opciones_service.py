"""
Servicio para la gestión de relaciones Local-ProductoOpcion.
"""

from typing import List, Tuple, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.locales_productos_opciones_repository import (
    LocalesProductosOpcionesRepository,
)
from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.locales_productos_opciones_model import (
    LocalesProductosOpcionesModel,
)
from src.api.schemas.locales_productos_opciones_schema import (
    LocalesProductosOpcionesCreate,
    LocalesProductosOpcionesUpdate,
    LocalesProductosOpcionesResponse,
    LocalesProductosOpcionesSummary,
    LocalesProductosOpcionesListResponse,
    ActivarProductoOpcionRequest,
    ActualizarPrecioAdicionalRequest,
    ActivarProductosOpcionesLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionNotFoundError,
)
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError


class LocalesProductosOpcionesConflictError(Exception):
    """Excepción para conflictos en relaciones local-producto_opcion."""
    pass


class LocalesProductosOpcionesNotFoundError(Exception):
    """Excepción cuando no se encuentra una relación local-producto_opcion."""
    pass


class LocalesProductosOpcionesService:
    """Servicio para la gestión de relaciones Local-ProductoOpcion.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con la activación y configuración de opciones de producto por local,
    incluyendo overrides de precio adicional.

    Attributes
    ----------
    repository : LocalesProductosOpcionesRepository
        Repositorio para acceso a datos de relaciones local-producto_opcion.
    producto_opcion_repository : ProductoOpcionRepository
        Repositorio para validar existencia de opciones de producto.
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
        self.repository = LocalesProductosOpcionesRepository(session)
        self.producto_opcion_repository = ProductoOpcionRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_relacion(
        self, relacion_data: LocalesProductosOpcionesCreate
    ) -> LocalesProductosOpcionesResponse:
        """
        Crea una nueva relación local-producto_opcion.

        Parameters
        ----------
        relacion_data : LocalesProductosOpcionesCreate
            Datos para crear la relación.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Esquema de respuesta con los datos de la relación creada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        ProductoOpcionNotFoundError
            Si no existe la opción de producto especificada.
        LocalesProductosOpcionesConflictError
            Si ya existe la relación.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(relacion_data.id_local)
        if not local:
            raise LocalNotFoundError(
                f"No se encontró el local con ID {relacion_data.id_local}"
            )

        # Validar que la opción de producto existe
        producto_opcion = await self.producto_opcion_repository.get_by_id(
            relacion_data.id_producto_opcion
        )
        if not producto_opcion:
            raise ProductoOpcionNotFoundError(
                f"No se encontró la opción de producto con ID {relacion_data.id_producto_opcion}"
            )

        try:
            # Crear modelo desde los datos
            relacion = LocalesProductosOpcionesModel(
                id_local=relacion_data.id_local,
                id_producto_opcion=relacion_data.id_producto_opcion,
                activo=relacion_data.activo,
                precio_adicional_override=relacion_data.precio_adicional_override,
            )

            # Persistir en la base de datos
            created_relacion = await self.repository.create(relacion)

            # Convertir y retornar como esquema de respuesta
            return LocalesProductosOpcionesResponse.model_validate(created_relacion)
        except IntegrityError:
            raise LocalesProductosOpcionesConflictError(
                f"Ya existe una relación entre el local {relacion_data.id_local} "
                f"y la opción de producto {relacion_data.id_producto_opcion}"
            )

    async def get_relacion_by_id(
        self, relacion_id: str
    ) -> LocalesProductosOpcionesResponse:
        """
        Obtiene una relación por su ID.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        LocalesProductosOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        relacion = await self.repository.get_by_id(relacion_id)

        if not relacion:
            raise LocalesProductosOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        return LocalesProductosOpcionesResponse.model_validate(relacion)

    async def get_productos_opciones_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> LocalesProductosOpcionesListResponse:
        """
        Obtiene todas las opciones de producto configuradas para un local.

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
        LocalesProductosOpcionesListResponse
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

        relaciones, total = await self.repository.get_productos_opciones_by_local(
            id_local, activo, skip, limit
        )

        items = [
            LocalesProductosOpcionesSummary.model_validate(r) for r in relaciones
        ]

        return LocalesProductosOpcionesListResponse(items=items, total=total)

    async def update_relacion(
        self, relacion_id: str, relacion_data: LocalesProductosOpcionesUpdate
    ) -> LocalesProductosOpcionesResponse:
        """
        Actualiza una relación local-producto_opcion existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        relacion_data : LocalesProductosOpcionesUpdate
            Datos a actualizar.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Esquema de respuesta con los datos actualizados.

        Raises
        ------
        LocalesProductosOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        existing = await self.repository.get_by_id(relacion_id)
        if not existing:
            raise LocalesProductosOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        # Actualizar solo los campos proporcionados
        update_data = relacion_data.model_dump(exclude_unset=True)
        updated_relacion = await self.repository.update(relacion_id, **update_data)

        return LocalesProductosOpcionesResponse.model_validate(updated_relacion)

    async def delete_relacion(self, relacion_id: str) -> bool:
        """
        Elimina una relación local-producto_opcion.

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
        LocalesProductosOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        relacion = await self.repository.get_by_id(relacion_id)
        if not relacion:
            raise LocalesProductosOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        result = await self.repository.delete(relacion_id)
        return result

    async def activar_producto_opcion(
        self, id_local: str, request: ActivarProductoOpcionRequest
    ) -> LocalesProductosOpcionesResponse:
        """
        Activa una opción de producto para un local específico con override opcional.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarProductoOpcionRequest
            Datos de la opción a activar con precio override.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Relación creada o actualizada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        ProductoOpcionNotFoundError
            Si no existe la opción de producto especificada.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        # Validar que la opción de producto existe
        producto_opcion = await self.producto_opcion_repository.get_by_id(
            request.id_producto_opcion
        )
        if not producto_opcion:
            raise ProductoOpcionNotFoundError(
                f"No se encontró la opción de producto con ID {request.id_producto_opcion}"
            )

        # Activar o actualizar la relación con override
        relacion = await self.repository.activate_producto_opcion_for_local(
            id_local, request.id_producto_opcion, request.precio_adicional_override
        )

        return LocalesProductosOpcionesResponse.model_validate(relacion)

    async def desactivar_producto_opcion(
        self, id_local: str, id_producto_opcion: str
    ) -> LocalesProductosOpcionesResponse:
        """
        Desactiva una opción de producto para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Relación actualizada.

        Raises
        ------
        LocalesProductosOpcionesNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.deactivate_producto_opcion_for_local(
            id_local, id_producto_opcion
        )

        if not relacion:
            raise LocalesProductosOpcionesNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y la opción de producto {id_producto_opcion}"
            )

        return LocalesProductosOpcionesResponse.model_validate(relacion)

    async def actualizar_precio_adicional(
        self, id_local: str, request: ActualizarPrecioAdicionalRequest
    ) -> LocalesProductosOpcionesResponse:
        """
        Actualiza el precio adicional override para una opción en un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActualizarPrecioAdicionalRequest
            Nuevo precio adicional override.

        Returns
        -------
        LocalesProductosOpcionesResponse
            Relación actualizada.

        Raises
        ------
        LocalesProductosOpcionesNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.update_precio_adicional_override(
            id_local, request.id_producto_opcion, request.precio_adicional_override
        )

        if not relacion:
            raise LocalesProductosOpcionesNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y la opción de producto {request.id_producto_opcion}"
            )

        return LocalesProductosOpcionesResponse.model_validate(relacion)

    async def activar_productos_opciones_lote(
        self, id_local: str, request: ActivarProductosOpcionesLoteRequest
    ) -> OperacionLoteResponse:
        """
        Activa múltiples opciones de producto para un local en una sola operación.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarProductosOpcionesLoteRequest
            Lista de opciones a activar con sus precios override.

        Returns
        -------
        OperacionLoteResponse
            Resultado de la operación batch.
        """
        exitosos = 0
        fallidos = 0
        detalles = []

        for opcion_request in request.productos_opciones:
            try:
                relacion = await self.activar_producto_opcion(id_local, opcion_request)
                detalles.append(relacion)
                exitosos += 1
            except Exception:
                fallidos += 1

        return OperacionLoteResponse(
            exitosos=exitosos, fallidos=fallidos, detalles=detalles
        )
