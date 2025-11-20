"""
Servicio para la gestión de items de pedidos (pedido_producto) en el sistema.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.pedidos.pedido_producto_repository import PedidoProductoRepository
from src.repositories.pedidos.pedido_repository import PedidoRepository
from src.repositories.pedidos.pedido_opcion_repository import PedidoOpcionRepository
from src.repositories.menu.producto_repository import ProductoRepository
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.api.schemas.pedido_producto_schema import (
    PedidoProductoCreate,
    PedidoProductoUpdate,
    PedidoProductoResponse,
    PedidoProductoSummary,
    PedidoProductoList,
    PedidoItemList,
)
from src.api.schemas.pedido_schema import PedidoItemResponse
from src.business_logic.exceptions.pedido_producto_exceptions import (
    PedidoProductoValidationError,
    PedidoProductoNotFoundError,
    PedidoProductoConflictError,
)


class PedidoProductoService:
    """Servicio para la gestión de items de pedidos en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con items de pedidos, incluyendo validaciones, cálculo de subtotal,
    y manejo de excepciones.

    Attributes
    ----------
    repository : PedidoProductoRepository
        Repositorio para acceso a datos de items de pedidos.
    pedido_repository : PedidoRepository
        Repositorio para validar pedidos.
    producto_repository : ProductoRepository
        Repositorio para validar productos.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = PedidoProductoRepository(session)
        self.pedido_repository = PedidoRepository(session)
        self.pedido_opcion_repository = PedidoOpcionRepository(session)
        self.producto_repository = ProductoRepository(session)

    async def create_pedido_producto(
        self, item_data: PedidoProductoCreate
    ) -> PedidoProductoResponse:
        """
        Crea un nuevo item de pedido en el sistema.

        Parameters
        ----------
        item_data : PedidoProductoCreate
            Datos para crear el nuevo item de pedido.

        Returns
        -------
        PedidoProductoResponse
            Esquema de respuesta con los datos del item creado.

        Raises
        ------
        PedidoProductoValidationError
            Si el pedido o producto no existen, o el producto no está disponible.
        PedidoProductoConflictError
            Si hay un conflicto de integridad.
        """
        # Validar que el pedido existe
        pedido = await self.pedido_repository.get_by_id(item_data.id_pedido)
        if not pedido:
            raise PedidoProductoValidationError(
                f"No se encontró el pedido con ID {item_data.id_pedido}"
            )

        # Validar que el producto existe y está disponible
        producto = await self.producto_repository.get_by_id(item_data.id_producto)
        if not producto:
            raise PedidoProductoValidationError(
                f"No se encontró el producto con ID {item_data.id_producto}"
            )
        if not producto.disponible:
            raise PedidoProductoValidationError(
                f"El producto '{producto.nombre}' no está disponible actualmente"
            )

        # Calcular subtotal
        precio_total_unitario = item_data.precio_unitario + (item_data.precio_opciones or Decimal("0.00"))
        subtotal = Decimal(str(item_data.cantidad)) * precio_total_unitario

        try:
            # Crear modelo de item de pedido
            item = PedidoProductoModel(
                id_pedido=item_data.id_pedido,
                id_producto=item_data.id_producto,
                cantidad=item_data.cantidad,
                precio_unitario=item_data.precio_unitario,
                precio_opciones=item_data.precio_opciones or Decimal("0.00"),
                subtotal=subtotal,
                notas_personalizacion=item_data.notas_personalizacion,
            )

            # Persistir en la base de datos
            created_item = await self.repository.create(item)

            # Convertir y retornar como esquema de respuesta
            return PedidoProductoResponse.model_validate(created_item)
        except IntegrityError:
            # Capturar errores de integridad (FK inválida)
            raise PedidoProductoConflictError(
                "Error al crear el item de pedido. Posible conflicto de integridad"
            )

    async def get_pedido_producto_by_id(
        self, item_id: str
    ) -> PedidoProductoResponse:
        """
        Obtiene un item de pedido por su ID.

        Parameters
        ----------
        item_id : str
            Identificador único del item de pedido a buscar (ULID).

        Returns
        -------
        PedidoProductoResponse
            Esquema de respuesta con los datos del item.

        Raises
        ------
        PedidoProductoNotFoundError
            Si no se encuentra un item con el ID proporcionado.
        """
        # Buscar el item por su ID
        item = await self.repository.get_by_id(item_id)

        # Verificar si existe
        if not item:
            raise PedidoProductoNotFoundError(
                f"No se encontró el item de pedido con ID {item_id}"
            )

        # Convertir y retornar como esquema de respuesta
        return PedidoProductoResponse.model_validate(item)

    async def get_productos_by_pedido(self, pedido_id: str) -> PedidoItemList:
        """
        Obtiene todos los items de un pedido específico con sus opciones.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido (ULID).

        Returns
        -------
        PedidoItemList
            Esquema con la lista de items del pedido incluyendo opciones.

        Raises
        ------
        PedidoProductoValidationError
            Si el pedido no existe.
        """
        # Validar que el pedido existe
        pedido = await self.pedido_repository.get_by_id(pedido_id)
        if not pedido:
            raise PedidoProductoValidationError(
                f"No se encontró el pedido con ID {pedido_id}"
            )

        # Obtener items del pedido
        items = await self.repository.get_by_pedido_id(pedido_id)

        # Construir la lista de items con sus opciones
        items_response = []
        for item in items:
            # Obtener opciones del item
            opciones = await self.pedido_opcion_repository.get_by_pedido_producto_id(item.id)
            # Extraer los IDs de las opciones
            opciones_ids = [opcion.id_producto_opcion for opcion in opciones]
            
            # Crear el item response
            item_response = PedidoItemResponse(
                id_producto=item.id_producto,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
                opciones=opciones_ids,
                notas_personalizacion=item.notas_personalizacion
            )
            items_response.append(item_response)

        # Retornar esquema de lista
        return PedidoItemList(items=items_response, total=len(items_response))

    async def delete_pedido_producto(self, item_id: str) -> bool:
        """
        Elimina un item de pedido por su ID.

        Parameters
        ----------
        item_id : str
            Identificador único del item de pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si el item fue eliminado correctamente.

        Raises
        ------
        PedidoProductoNotFoundError
            Si no se encuentra un item con el ID proporcionado.
        """
        # Verificar primero si el item existe
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise PedidoProductoNotFoundError(
                f"No se encontró el item de pedido con ID {item_id}"
            )

        # Eliminar el item
        result = await self.repository.delete(item_id)
        return result

    async def get_pedidos_productos(
        self,
        skip: int = 0,
        limit: int = 100,
        id_pedido: Optional[str] = None,
        id_producto: Optional[str] = None,
    ) -> PedidoProductoList:
        """
        Obtiene una lista paginada de items de pedidos.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_pedido : str, optional
            Filtrar por ID de pedido.
        id_producto : str, optional
            Filtrar por ID de producto.

        Returns
        -------
        PedidoProductoList
            Esquema con la lista de items y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise PedidoProductoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise PedidoProductoValidationError(
                "El parámetro 'limit' debe ser mayor a cero"
            )

        # Obtener items desde el repositorio
        items, total = await self.repository.get_all(skip, limit, id_pedido, id_producto)

        # Convertir modelos a esquemas de resumen
        item_summaries = [PedidoProductoSummary.model_validate(item) for item in items]

        # Retornar esquema de lista
        return PedidoProductoList(items=item_summaries, total=total)

    async def update_pedido_producto(
        self, item_id: str, item_data: PedidoProductoUpdate
    ) -> PedidoProductoResponse:
        """
        Actualiza un item de pedido existente.

        Parameters
        ----------
        item_id : str
            Identificador único del item de pedido a actualizar (ULID).
        item_data : PedidoProductoUpdate
            Datos para actualizar el item.

        Returns
        -------
        PedidoProductoResponse
            Esquema de respuesta con los datos del item actualizado.

        Raises
        ------
        PedidoProductoNotFoundError
            Si no se encuentra un item con el ID proporcionado.
        PedidoProductoValidationError
            Si los datos de actualización son inválidos.
        """
        # Obtener el item actual
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise PedidoProductoNotFoundError(
                f"No se encontró el item de pedido con ID {item_id}"
            )

        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = item_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el item actual
            return await self.get_pedido_producto_by_id(item_id)

        # Si se actualizan cantidad o precios, recalcular subtotal
        if any(field in update_data for field in ["cantidad", "precio_unitario", "precio_opciones"]):
            cantidad = update_data.get("cantidad", item.cantidad)
            precio_unitario = update_data.get("precio_unitario", item.precio_unitario)
            precio_opciones = update_data.get("precio_opciones", item.precio_opciones)

            # Calcular nuevo subtotal
            precio_total_unitario = precio_unitario + precio_opciones
            subtotal = Decimal(str(cantidad)) * precio_total_unitario
            update_data["subtotal"] = subtotal

        try:
            # Actualizar el item
            updated_item = await self.repository.update(item_id, **update_data)

            # Verificar si el item fue encontrado
            if not updated_item:
                raise PedidoProductoNotFoundError(
                    f"No se encontró el item de pedido con ID {item_id}"
                )

            # Convertir y retornar como esquema de respuesta
            return PedidoProductoResponse.model_validate(updated_item)
        except IntegrityError:
            # Capturar errores de integridad
            raise PedidoProductoValidationError(
                "Error al actualizar el item. Verifique los datos proporcionados"
            )
