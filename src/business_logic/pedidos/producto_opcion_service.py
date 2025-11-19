"""
Servicio para la gestión de opciones de productos en el sistema.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.repositories.mesas.mesa_repository import MesaRepository
from src.repositories.mesas.locales_productos_opciones_repository import LocalesProductosOpcionesRepository
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.api.schemas.producto_opcion_schema import (
    ProductoOpcionCreate,
    ProductoOpcionUpdate,
    ProductoOpcionResponse,
    ProductoOpcionSummary,
    ProductoOpcionList,
)
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionValidationError,
    ProductoOpcionNotFoundError,
    ProductoOpcionConflictError,
)


class ProductoOpcionService:
    """Servicio para la gestión de opciones de productos en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con opciones de productos, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : ProductoOpcionRepository
        Repositorio para acceso a datos de opciones de productos.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.session = session
        self.repository = ProductoOpcionRepository(session)
        self.mesa_repository = MesaRepository(session)
        self.locales_productos_opciones_repository = LocalesProductosOpcionesRepository(session)

    async def create_producto_opcion(self, producto_opcion_data: ProductoOpcionCreate) -> ProductoOpcionResponse:
        """
        Crea una nueva opción de producto en el sistema.
        
        Parameters
        ----------
        producto_opcion_data : ProductoOpcionCreate
            Datos para crear la nueva opción de producto.

        Returns
        -------
        ProductoOpcionResponse
            Esquema de respuesta con los datos de la opción de producto creada.

        Raises
        ------
        ProductoOpcionConflictError
            Si ya existe una opción de producto con la misma combinación de datos.
        """
        try:
            # Crear modelo de opción de producto desde los datos
            producto_opcion = ProductoOpcionModel(
                id_producto=producto_opcion_data.id_producto,
                id_tipo_opcion=producto_opcion_data.id_tipo_opcion,
                nombre=producto_opcion_data.nombre,
                precio_adicional=producto_opcion_data.precio_adicional,
                activo=producto_opcion_data.activo,
                orden=producto_opcion_data.orden
            )

            # Persistir en la base de datos
            created_producto_opcion = await self.repository.create(producto_opcion)

            # Convertir y retornar como esquema de respuesta
            return ProductoOpcionResponse.model_validate(created_producto_opcion)
        except IntegrityError:
            # Capturar errores de integridad
            raise ProductoOpcionConflictError(
                f"Ya existe una opción de producto con el nombre '{producto_opcion_data.nombre}'"
            )

    async def get_producto_opcion_by_id(self, producto_opcion_id: str) -> ProductoOpcionResponse:
        """
        Obtiene una opción de producto por su ID.

        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a buscar.

        Returns
        -------
        ProductoOpcionResponse
            Esquema de respuesta con los datos de la opción de producto.

        Raises
        ------
        ProductoOpcionNotFoundError
            Si no se encuentra una opción de producto con el ID proporcionado.
        """
        # Buscar la opción de producto por su ID
        producto_opcion = await self.repository.get_by_id(producto_opcion_id)

        # Verificar si existe
        if not producto_opcion:
            raise ProductoOpcionNotFoundError(f"No se encontró la opción de producto con ID {producto_opcion_id}")

        # Convertir y retornar como esquema de respuesta
        return ProductoOpcionResponse.model_validate(producto_opcion)

    async def delete_producto_opcion(self, producto_opcion_id: str) -> bool:
        """
        Elimina una opción de producto por su ID.
        
        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a eliminar.

        Returns
        -------
        bool
            True si la opción de producto fue eliminada correctamente.

        Raises
        ------
        ProductoOpcionNotFoundError
            Si no se encuentra una opción de producto con el ID proporcionado.
        """
        # Verificar primero si la opción de producto existe
        producto_opcion = await self.repository.get_by_id(producto_opcion_id)
        if not producto_opcion:
            raise ProductoOpcionNotFoundError(f"No se encontró la opción de producto con ID {producto_opcion_id}")

        # Eliminar la opción de producto
        result = await self.repository.delete(producto_opcion_id)
        return result

    async def get_producto_opciones(
        self,
        skip: int = 0,
        limit: int = 100,
        id_mesa: Optional[str] = None,
        id_local: Optional[str] = None
    ) -> ProductoOpcionList:
        """
        Obtiene una lista paginada de opciones de productos.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_mesa : str, optional
            ID de mesa para filtrar por local (el backend resuelve local automáticamente).
        id_local : str, optional
            ID de local para filtrar directamente.

        Returns
        -------
        ProductoOpcionList
            Esquema con la lista de opciones de productos y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ProductoOpcionValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ProductoOpcionValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Resolver local desde mesa si es necesario
        local_id = None

        if id_mesa:
            # Resolver: mesa → zona → local
            local = await self.mesa_repository.get_local_by_mesa_id(id_mesa)
            if local:
                local_id = local.id
            else:
                raise ProductoOpcionValidationError(f"La mesa {id_mesa} no tiene un local asignado")
        elif id_local:
            local_id = id_local

        # Filtrar por local si tenemos uno
        if local_id:
            return await self._get_producto_opciones_con_local(local_id, skip, limit)
        else:
            # Sin filtro - retornar todas las opciones de productos (backward compatible)
            producto_opciones, total = await self.repository.get_all(skip, limit)

            # Convertir modelos a esquemas de resumen
            producto_opcion_summaries = [ProductoOpcionSummary.model_validate(po) for po in producto_opciones]

            # Retornar esquema de lista
            return ProductoOpcionList(items=producto_opcion_summaries, total=total)

    async def _get_producto_opciones_con_local(
        self,
        id_local: str,
        skip: int,
        limit: int
    ) -> ProductoOpcionList:
        """
        Obtiene opciones de productos filtradas por local con overrides aplicados.

        Parameters
        ----------
        id_local : str
            ID del local para filtrar.
        skip : int
            Número de registros a omitir.
        limit : int
            Número máximo de registros a retornar.

        Returns
        -------
        ProductoOpcionList
            Lista de opciones de productos con override de precio_adicional aplicado.
        """
        from decimal import Decimal

        # Obtener relaciones local-producto_opcion activas
        relaciones, total = await self.locales_productos_opciones_repository.get_productos_opciones_by_local(
            id_local, activo=True, skip=skip, limit=limit
        )

        # Cargar opciones de productos completas y aplicar overrides
        opciones_con_overrides = []
        for relacion in relaciones:
            opcion = await self.repository.get_by_id(relacion.id_producto_opcion)
            if opcion:
                # Aplicar override de precio_adicional (NULL = usar original, NOT NULL = usar custom)
                opcion_dict = opcion.to_dict()
                opcion_dict['precio_adicional'] = (
                    relacion.precio_adicional_override if relacion.precio_adicional_override is not None else opcion.precio_adicional
                )

                opciones_con_overrides.append(ProductoOpcionSummary.model_validate(opcion_dict))

        return ProductoOpcionList(items=opciones_con_overrides, total=total)

    async def update_producto_opcion(self, producto_opcion_id: str, producto_opcion_data: ProductoOpcionUpdate) -> ProductoOpcionResponse:
        """
        Actualiza una opción de producto existente.

        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a actualizar.
        producto_opcion_data : ProductoOpcionUpdate
            Datos para actualizar la opción de producto.

        Returns
        -------
        ProductoOpcionResponse
            Esquema de respuesta con los datos de la opción de producto actualizada.

        Raises
        ------
        ProductoOpcionNotFoundError
            Si no se encuentra una opción de producto con el ID proporcionado.
        ProductoOpcionConflictError
            Si ya existe otra opción de producto con el mismo nombre.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = producto_opcion_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la opción de producto actual
            return await self.get_producto_opcion_by_id(producto_opcion_id)

        try:
            # Actualizar la opción de producto
            updated_producto_opcion = await self.repository.update(producto_opcion_id, **update_data)

            # Verificar si la opción de producto fue encontrada
            if not updated_producto_opcion:
                raise ProductoOpcionNotFoundError(f"No se encontró la opción de producto con ID {producto_opcion_id}")

            # Convertir y retornar como esquema de respuesta
            return ProductoOpcionResponse.model_validate(updated_producto_opcion)
        except IntegrityError:
            # Capturar errores de integridad
            if "nombre" in update_data:
                raise ProductoOpcionConflictError(
                    f"Ya existe una opción de producto con el nombre '{update_data['nombre']}'"
                )
            # Si no es por nombre, reenviar la excepción original
            raise
