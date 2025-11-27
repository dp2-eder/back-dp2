"""
Servicio para la gestión de pedidos en el sistema.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.pedidos.pedido_repository import PedidoRepository
from src.repositories.mesas.mesa_repository import MesaRepository
from src.repositories.pedidos.pedido_producto_repository import PedidoProductoRepository
from src.repositories.pedidos.pedido_opcion_repository import PedidoOpcionRepository
from src.repositories.menu.producto_repository import ProductoRepository
from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository
from src.models.pedidos.pedido_model import PedidoModel
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.api.schemas.pedido_schema import (
    PedidoCreate,
    PedidoUpdate,
    PedidoResponse,
    PedidoSummary,
    PedidoList,
    PedidoEstadoUpdate,
    PedidoCompletoCreate,
    PedidoCompletoResponse,
    PedidoItemResponse,
)
from src.api.schemas.pedido_producto_schema import PedidoProductoResponse
from src.api.schemas.pedido_opcion_schema import PedidoOpcionResponse
from src.api.schemas.pedido_schema import PedidoProductoWithOpcionesResponse
from src.api.schemas.pedido_detallado_schema import (
    PedidoDetalladoResponse,
    PedidoDetalladoList,
    PedidoProductoDetalladoResponse,
    ProductoDetalleResponse,
    OpcionDetalleResponse,
)
from src.api.schemas.pedido_sesion_schema import (
    PedidoEnviarRequest,
    PedidoEnviarResponse,
    PedidoHistorialResponse,
    PedidoHistorialDetalle,
    ProductoPedidoDetalle,
    ProductoOpcionDetalle,
)
from src.business_logic.exceptions.pedido_exceptions import (
    PedidoValidationError,
    PedidoNotFoundError,
    PedidoConflictError,
    PedidoStateTransitionError,
)
from src.core.enums.pedido_enums import EstadoPedido
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.business_logic.notifications.rabbitmq_service import get_rabbitmq_service
from src.repositories.menu.categoria_repository import CategoriaRepository
from src.api.schemas.scrapper_schemas import (
    PlatoInsertRequest,
    MesaDomotica,
    ProductoDomotica,
    ComprobanteElectronico,
    TipoDocumentoEnum,
    TipoComprobanteEnum,
    MesaEstadoEnum
)

logger = logging.getLogger(__name__)



class PedidoService:
    """Servicio para la gestión de pedidos en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con pedidos, incluyendo validaciones, generación de número de pedido,
    gestión de estados y manejo de excepciones.

    Attributes
    ----------
    repository : PedidoRepository
        Repositorio para acceso a datos de pedidos.
    mesa_repository : MesaRepository
        Repositorio para validar mesas.
    """

    # Transiciones de estado válidas
    VALID_TRANSITIONS = {
        EstadoPedido.PENDIENTE: [EstadoPedido.CONFIRMADO, EstadoPedido.CANCELADO],
        EstadoPedido.CONFIRMADO: [EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO],
        EstadoPedido.EN_PREPARACION: [EstadoPedido.LISTO, EstadoPedido.CANCELADO],
        EstadoPedido.LISTO: [EstadoPedido.ENTREGADO],
        EstadoPedido.ENTREGADO: [],
        EstadoPedido.CANCELADO: [],
    }

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = PedidoRepository(session)
        self.mesa_repository = MesaRepository(session)
        self.pedido_producto_repository = PedidoProductoRepository(session)
        self.pedido_opcion_repository = PedidoOpcionRepository(session)
        self.producto_repository = ProductoRepository(session)
        self.producto_opcion_repository = ProductoOpcionRepository(session)
        self.categoria_repository = CategoriaRepository(session)
        self.sesion_mesa_repository = SesionMesaRepository(session)
        self.session = session

    async def _generate_numero_pedido(self, id_mesa: str) -> str:
        """
        Genera un número de pedido único con formato YYYYMMDD-M{numero_mesa}-{seq:03d}.

        Parameters
        ----------
        id_mesa : str
            ID de la mesa (ULID).

        Returns
        -------
        str
            Número de pedido generado.

        Raises
        ------
        PedidoValidationError
            Si la mesa no existe.
        """
        # Obtener la mesa para extraer el número
        mesa = await self.mesa_repository.get_by_id(id_mesa)
        if not mesa:
            raise PedidoValidationError(f"No se encontró la mesa con ID {id_mesa}")

        # Obtener la fecha actual
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # Obtener la última secuencia para esta fecha y mesa
        last_seq = await self.repository.get_last_sequence_for_date_and_mesa(
            now, mesa.numero
        )
        new_seq = last_seq + 1

        # Generar el número de pedido
        numero_pedido = f"{date_str}-M{mesa.numero}-{new_seq:03d}"

        return numero_pedido

    async def create_pedido(self, pedido_data: PedidoCreate) -> PedidoResponse:
        """
        Crea un nuevo pedido en el sistema.

        Parameters
        ----------
        pedido_data : PedidoCreate
            Datos para crear el nuevo pedido.

        Returns
        -------
        PedidoResponse
            Esquema de respuesta con los datos del pedido creado.

        Raises
        ------
        PedidoConflictError
            Si ya existe un pedido con el mismo número.
        PedidoValidationError
            Si los datos son inválidos o la mesa no existe.
        """
        try:
            # Generar número de pedido automáticamente
            numero_pedido = await self._generate_numero_pedido(pedido_data.id_mesa)

            # Crear modelo de pedido desde los datos
            pedido = PedidoModel(
                id_mesa=pedido_data.id_mesa,
                id_usuario=pedido_data.id_usuario,
                numero_pedido=numero_pedido,
                estado=EstadoPedido.PENDIENTE,
                subtotal=pedido_data.subtotal or Decimal("0.00"),
                impuestos=pedido_data.impuestos or Decimal("0.00"),
                descuentos=pedido_data.descuentos or Decimal("0.00"),
                total=pedido_data.total or Decimal("0.00"),
                notas_cliente=pedido_data.notas_cliente,
                notas_cocina=pedido_data.notas_cocina,
            )

            # Persistir en la base de datos
            created_pedido = await self.repository.create(pedido)

            # Convertir y retornar como esquema de respuesta
            return PedidoResponse.model_validate(created_pedido)
        except IntegrityError:
            # Capturar errores de integridad (numero_pedido duplicado, FK inválida)
            raise PedidoConflictError(
                f"Error al crear el pedido. Posible conflicto con numero_pedido o FK inválida"
            )

    async def get_pedido_by_id(self, pedido_id: str) -> PedidoResponse:
        """
        Obtiene un pedido por su ID incluyendo los detalles de cada item.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a buscar (ULID).

        Returns
        -------
        PedidoResponse
            Esquema de respuesta con los datos del pedido e items.

        Raises
        ------
        PedidoNotFoundError
            Si no se encuentra un pedido con el ID proporcionado.
        """
        # Buscar el pedido por su ID
        pedido = await self.repository.get_by_id(pedido_id)

        # Verificar si existe
        if not pedido:
            raise PedidoNotFoundError(f"No se encontró el pedido con ID {pedido_id}")

        # Obtener items del pedido
        items = await self.pedido_producto_repository.get_by_pedido_id(pedido_id)

        # Construir la lista de items con sus opciones
        items_response = []
        for item in items:
            opciones = await self.pedido_opcion_repository.get_by_pedido_producto_id(
                item.id
            )
            opciones_ids = [opcion.id_producto_opcion for opcion in opciones]

            items_response.append(
                PedidoItemResponse(
                    id_producto=item.id_producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    opciones=opciones_ids,
                    notas_personalizacion=item.notas_personalizacion,
                )
            )

        # Convertir el pedido a esquema de respuesta y adjuntar items
        pedido_response = PedidoResponse.model_validate(pedido)
        pedido_response.items = items_response

        return pedido_response

    async def get_pedido_by_numero(self, numero_pedido: str) -> PedidoResponse:
        """
        Obtiene un pedido por su número único incluyendo los detalles de cada item.

        Parameters
        ----------
        numero_pedido : str
            Número único del pedido a buscar.

        Returns
        -------
        PedidoResponse
            Esquema de respuesta con los datos del pedido e items.

        Raises
        ------
        PedidoNotFoundError
            Si no se encuentra un pedido con el número proporcionado.
        """
        # Buscar el pedido por su número
        pedido = await self.repository.get_by_numero_pedido(numero_pedido)

        # Verificar si existe
        if not pedido:
            raise PedidoNotFoundError(
                f"No se encontró el pedido con número {numero_pedido}"
            )

        # Obtener items del pedido
        items = await self.pedido_producto_repository.get_by_pedido_id(pedido.id)

        items_response = []
        for item in items:
            opciones = await self.pedido_opcion_repository.get_by_pedido_producto_id(
                item.id
            )
            opciones_ids = [opcion.id_producto_opcion for opcion in opciones]

            items_response.append(
                PedidoItemResponse(
                    id_producto=item.id_producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    opciones=opciones_ids,
                    notas_personalizacion=item.notas_personalizacion,
                )
            )

        pedido_response = PedidoResponse.model_validate(pedido)
        pedido_response.items = items_response

        return pedido_response

    async def delete_pedido(self, pedido_id: str) -> bool:
        """
        Elimina un pedido por su ID.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si el pedido fue eliminado correctamente.

        Raises
        ------
        PedidoNotFoundError
            Si no se encuentra un pedido con el ID proporcionado.
        """
        # Verificar primero si el pedido existe
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise PedidoNotFoundError(f"No se encontró el pedido con ID {pedido_id}")

        # Eliminar el pedido
        result = await self.repository.delete(pedido_id)
        return result

    async def get_pedidos(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoPedido] = None,
        id_mesa: Optional[str] = None,
        id_usuario: Optional[str] = None,
        id_sesion_mesa: Optional[str] = None,
    ) -> PedidoList:
        """
        Obtiene una lista paginada de pedidos.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        estado : EstadoPedido, optional
            Filtrar por estado del pedido.
        id_mesa : str, optional
            Filtrar por ID de mesa.
        id_usuario : str, optional
            Filtrar por ID de usuario.
        id_sesion_mesa : str, optional
            Filtrar por ID de sesión de mesa.

        Returns
        -------
        PedidoList
            Esquema con la lista de pedidos y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise PedidoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise PedidoValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener pedidos desde el repositorio
        pedidos, total = await self.repository.get_all(skip, limit, estado, id_mesa, id_usuario, id_sesion_mesa)

        # Convertir modelos a esquemas de resumen
        pedido_summaries = [PedidoSummary.model_validate(pedido) for pedido in pedidos]

        # Retornar esquema de lista
        return PedidoList(items=pedido_summaries, total=total)

    async def get_pedidos_detallado(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoPedido] = None,
        id_mesa: Optional[str] = None,
        id_usuario: Optional[str] = None,
        id_sesion_mesa: Optional[str] = None,
    ) -> PedidoDetalladoList:
        """
        Obtiene una lista paginada de pedidos con información detallada de productos y opciones.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        estado : EstadoPedido, optional
            Filtrar por estado del pedido.
        id_mesa : str, optional
            Filtrar por ID de mesa.
        id_usuario : str, optional
            Filtrar por ID de usuario.
        id_sesion_mesa : str, optional
            Filtrar por ID de sesión de mesa.

        Returns
        -------
        PedidoDetalladoList
            Esquema con la lista de pedidos detallados y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise PedidoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise PedidoValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener pedidos con relaciones eager-loaded desde el repositorio
        pedidos, total = await self.repository.get_all_detallado(skip, limit, estado, id_mesa, id_usuario, id_sesion_mesa)

        # Convertir modelos a esquemas detallados
        pedidos_detallados = []
        for pedido in pedidos:
            # Construir datos básicos del pedido
            pedido_dict = pedido.to_dict()

            # Procesar productos del pedido con sus opciones
            productos_detallados = []
            for pedido_producto in pedido.pedidos_productos:
                # Datos del producto
                producto_data = None
                if pedido_producto.producto:
                    producto_data = ProductoDetalleResponse(
                        id=pedido_producto.producto.id,
                        nombre=pedido_producto.producto.nombre,
                        descripcion=pedido_producto.producto.descripcion,
                        precio_base=pedido_producto.producto.precio_base,
                        disponible=pedido_producto.producto.disponible,
                        id_categoria=pedido_producto.producto.id_categoria
                    )

                # Procesar opciones del producto
                opciones_detalladas = []
                for pedido_opcion in pedido_producto.pedidos_opciones:
                    opcion_data = OpcionDetalleResponse(
                        id=pedido_opcion.id,
                        id_pedido_producto=pedido_opcion.id_pedido_producto,
                        id_producto_opcion=pedido_opcion.id_producto_opcion,
                        precio_adicional=pedido_opcion.precio_adicional,
                        nombre_opcion=pedido_opcion.producto_opcion.nombre if pedido_opcion.producto_opcion else None,
                        descripcion_opcion=None  # ProductoOpcion no tiene descripción
                    )
                    opciones_detalladas.append(opcion_data)

                # Construir el producto detallado con sus opciones
                producto_detallado = PedidoProductoDetalladoResponse(
                    id=pedido_producto.id,
                    id_pedido=pedido_producto.id_pedido,
                    id_producto=pedido_producto.id_producto,
                    cantidad=pedido_producto.cantidad,
                    precio_unitario=pedido_producto.precio_unitario,
                    precio_opciones=pedido_producto.precio_opciones,
                    subtotal=pedido_producto.subtotal,
                    notas_personalizacion=pedido_producto.notas_personalizacion,
                    producto=producto_data,
                    opciones=opciones_detalladas
                )
                productos_detallados.append(producto_detallado)

            # Construir el pedido detallado completo
            pedido_detallado = PedidoDetalladoResponse(
                id=pedido.id,
                id_mesa=pedido.id_mesa,
                id_usuario=pedido.id_usuario,
                numero_pedido=pedido.numero_pedido,
                estado=pedido.estado,
                subtotal=pedido.subtotal,
                impuestos=pedido.impuestos,
                descuentos=pedido.descuentos,
                total=pedido.total,
                notas_cliente=pedido.notas_cliente,
                notas_cocina=pedido.notas_cocina,
                fecha_creacion=pedido.fecha_creacion,
                fecha_modificacion=pedido.fecha_modificacion,
                fecha_confirmado=pedido.fecha_confirmado,
                fecha_en_preparacion=pedido.fecha_en_preparacion,
                fecha_listo=pedido.fecha_listo,
                fecha_entregado=pedido.fecha_entregado,
                fecha_cancelado=pedido.fecha_cancelado,
                productos=productos_detallados
            )
            pedidos_detallados.append(pedido_detallado)

        # Retornar esquema de lista
        return PedidoDetalladoList(items=pedidos_detallados, total=total)

    async def update_pedido(
        self, pedido_id: str, pedido_data: PedidoUpdate
    ) -> PedidoResponse:
        """
        Actualiza un pedido existente.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a actualizar (ULID).
        pedido_data : PedidoUpdate
            Datos para actualizar el pedido.

        Returns
        -------
        PedidoResponse
            Esquema de respuesta con los datos del pedido actualizado.

        Raises
        ------
        PedidoNotFoundError
            Si no se encuentra un pedido con el ID proporcionado.
        PedidoValidationError
            Si los datos de actualización son inválidos.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = pedido_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el pedido actual
            return await self.get_pedido_by_id(pedido_id)

        # Validar que los valores monetarios sean positivos
        for field in ["subtotal", "impuestos", "descuentos", "total"]:
            if field in update_data and update_data[field] < 0:
                raise PedidoValidationError(
                    f"El campo '{field}' debe ser mayor o igual a cero"
                )

        try:
            # Actualizar el pedido
            updated_pedido = await self.repository.update(pedido_id, **update_data)

            # Verificar si el pedido fue encontrado
            if not updated_pedido:
                raise PedidoNotFoundError(f"No se encontró el pedido con ID {pedido_id}")

            # Convertir y retornar como esquema de respuesta
            return PedidoResponse.model_validate(updated_pedido)
        except IntegrityError:
            # Capturar errores de integridad (FK inválida)
            raise PedidoValidationError(
                "Error al actualizar el pedido. Verifique los datos proporcionados"
            )

    async def cambiar_estado(
        self, pedido_id: str, estado_data: PedidoEstadoUpdate
    ) -> PedidoResponse:
        """
        Cambia el estado de un pedido y actualiza el timestamp correspondiente.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido.
        estado_data : PedidoEstadoUpdate
            Nuevo estado del pedido.

        Returns
        -------
        PedidoResponse
            Esquema de respuesta con los datos del pedido actualizado.

        Raises
        ------
        PedidoNotFoundError
            Si no se encuentra el pedido.
        PedidoStateTransitionError
            Si la transición de estado no es válida.
        """
        # Obtener el pedido actual
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise PedidoNotFoundError(f"No se encontró el pedido con ID {pedido_id}")

        # Validar la transición de estado
        nuevo_estado = estado_data.estado
        if nuevo_estado not in self.VALID_TRANSITIONS.get(pedido.estado, []):
            raise PedidoStateTransitionError(
                f"Transición de estado inválida: {pedido.estado.value} -> {nuevo_estado.value}"
            )

        # Preparar los datos de actualización
        update_fields = {}
        update_fields["estado"] = nuevo_estado

        # Actualizar el timestamp correspondiente al nuevo estado
        now = datetime.now()
        if nuevo_estado == EstadoPedido.CONFIRMADO:
            update_fields["fecha_confirmado"] = now
        elif nuevo_estado == EstadoPedido.EN_PREPARACION:
            update_fields["fecha_en_preparacion"] = now
        elif nuevo_estado == EstadoPedido.LISTO:
            update_fields["fecha_listo"] = now
        elif nuevo_estado == EstadoPedido.ENTREGADO:
            update_fields["fecha_entregado"] = now
        elif nuevo_estado == EstadoPedido.CANCELADO:
            update_fields["fecha_cancelado"] = now

        # Actualizar el pedido
        updated_pedido = await self.repository.update(pedido_id, **update_fields)

        # Convertir y retornar como esquema de respuesta
        return PedidoResponse.model_validate(updated_pedido)

    async def create_pedido_completo(
        self, pedido_data: PedidoCompletoCreate
    ) -> PedidoCompletoResponse:
        """
        Crea un pedido completo con sus items en una sola transacción.

        Este método crea un pedido y todos sus items de forma atómica, calculando
        automáticamente los totales basándose en los items proporcionados.

        Parameters
        ----------
        pedido_data : PedidoCompletoCreate
            Datos del pedido completo con su lista de items.

        Returns
        -------
        PedidoCompletoResponse
            Esquema de respuesta con el pedido y sus items creados.

        Raises
        ------
        PedidoValidationError
            Si los datos son inválidos, la mesa no existe, o algún producto
            no existe o no está disponible.
        PedidoConflictError
            Si hay un conflicto de integridad en la base de datos.
        """
        try:
            # Validar que la mesa existe
            mesa = await self.mesa_repository.get_by_id(pedido_data.id_mesa)
            if not mesa:
                raise PedidoValidationError(
                    f"No se encontró la mesa con ID {pedido_data.id_mesa}"
                )

            # Validar que todos los productos existen y están disponibles
            for item in pedido_data.items:
                producto = await self.producto_repository.get_by_id(item.id_producto)
                if not producto:
                    raise PedidoValidationError(
                        f"No se encontró el producto con ID {item.id_producto}"
                    )
                if not producto.disponible:
                    raise PedidoValidationError(
                        f"El producto '{producto.nombre}' no está disponible actualmente"
                    )

                # Validar que todas las opciones existen
                for opcion in item.opciones:
                    producto_opcion = await self.producto_opcion_repository.get_by_id(opcion.id_producto_opcion)
                    if not producto_opcion:
                        raise PedidoValidationError(
                            f"No se encontró la opción de producto con ID {opcion.id_producto_opcion}"
                        )

            # Generar número de pedido
            numero_pedido = await self._generate_numero_pedido(pedido_data.id_mesa)

            # Calcular subtotal sumando todos los items
            subtotal = Decimal("0.00")
            for item in pedido_data.items:
                # Calcular precio_opciones sumando todas las opciones
                precio_opciones = sum(opcion.precio_adicional for opcion in item.opciones)
                precio_total_unitario = item.precio_unitario + precio_opciones
                item_subtotal = Decimal(str(item.cantidad)) * precio_total_unitario
                subtotal += item_subtotal

            # Por ahora no calculamos impuestos ni descuentos, solo el total = subtotal
            total = subtotal

            # Crear el pedido
            pedido = PedidoModel(
                id_mesa=pedido_data.id_mesa,
                id_usuario=pedido_data.id_usuario,
                numero_pedido=numero_pedido,
                estado=EstadoPedido.PENDIENTE,
                subtotal=subtotal,
                impuestos=Decimal("0.00"),
                descuentos=Decimal("0.00"),
                total=total,
                notas_cliente=pedido_data.notas_cliente,
                notas_cocina=pedido_data.notas_cocina,
            )

            # Persistir el pedido
            created_pedido = await self.repository.create(pedido)

            # Crear todos los items del pedido con sus opciones
            created_items_with_opciones = []
            for item_data in pedido_data.items:
                # Calcular precio_opciones sumando todas las opciones
                precio_opciones = sum(opcion.precio_adicional for opcion in item_data.opciones)
                precio_total_unitario = item_data.precio_unitario + precio_opciones
                item_subtotal = Decimal(str(item_data.cantidad)) * precio_total_unitario

                # Crear el item
                item = PedidoProductoModel(
                    id_pedido=created_pedido.id,
                    id_producto=item_data.id_producto,
                    cantidad=item_data.cantidad,
                    precio_unitario=item_data.precio_unitario,
                    precio_opciones=precio_opciones,
                    subtotal=item_subtotal,
                    notas_personalizacion=item_data.notas_personalizacion,
                )

                # Persistir el item
                created_item = await self.pedido_producto_repository.create(item)

                # Crear las opciones para este item
                created_opciones = []
                for opcion_data in item_data.opciones:
                    opcion = PedidoOpcionModel(
                        id_pedido_producto=created_item.id,
                        id_producto_opcion=opcion_data.id_producto_opcion,
                        precio_adicional=opcion_data.precio_adicional,
                    )
                    created_opcion = await self.pedido_opcion_repository.create(opcion)
                    created_opciones.append(created_opcion)

                # Guardar item con sus opciones
                created_items_with_opciones.append((created_item, created_opciones))

            # Commit de la transacción (si usamos flush automáticamente)
            await self.session.flush()

            # Construir la respuesta completa con items y opciones
            pedido_response = PedidoResponse.model_validate(created_pedido)

            # Construir items con opciones
            items_with_opciones_response = []
            for item, opciones in created_items_with_opciones:
                # Convertir el item
                item_dict = {
                    "id": item.id,
                    "id_pedido": item.id_pedido,
                    "id_producto": item.id_producto,
                    "cantidad": item.cantidad,
                    "precio_unitario": item.precio_unitario,
                    "precio_opciones": item.precio_opciones,
                    "subtotal": item.subtotal,
                    "notas_personalizacion": item.notas_personalizacion,
                    "fecha_creacion": item.fecha_creacion,
                    "fecha_modificacion": item.fecha_modificacion,
                    "opciones": [PedidoOpcionResponse.model_validate(opcion) for opcion in opciones]
                }
                items_with_opciones_response.append(PedidoProductoWithOpcionesResponse(**item_dict))

            # Crear el objeto de respuesta completo
            response_dict = pedido_response.model_dump()
            response_dict["items"] = items_with_opciones_response

            # --- Integración RabbitMQ ---
            try:
                rabbitmq_service = await get_rabbitmq_service()
                if rabbitmq_service.is_connected:
                    # 1. Construir MesaDomotica
                    zona_nombre = mesa.zona.nombre if mesa.zona else "SIN ZONA"
                    mesa_domotica = MesaDomotica(
                        nombre=mesa.numero,
                        zona=zona_nombre,
                        nota=mesa.nota,
                        estado=MesaEstadoEnum.OCUPADA
                    )

                    # 2. Construir lista de ProductoDomotica
                    platos_domotica = []
                    categoria_cache = {}

                    for item_data in pedido_data.items:
                        producto = await self.producto_repository.get_by_id(item_data.id_producto)
                        
                        if producto:
                            # Obtener nombre de categoría
                            cat_nombre = "GENERAL"
                            if producto.id_categoria in categoria_cache:
                                cat_nombre = categoria_cache[producto.id_categoria]
                            else:
                                categoria = await self.categoria_repository.get_by_id(producto.id_categoria)
                                if categoria:
                                    cat_nombre = categoria.nombre
                                    categoria_cache[producto.id_categoria] = cat_nombre
                            
                            plato = ProductoDomotica(
                                categoria=cat_nombre,
                                nombre=producto.nombre,
                                stock=str(item_data.cantidad), # Usamos la cantidad del pedido como "stock" a insertar
                                precio=str(producto.precio_base)
                            )
                            platos_domotica.append(plato)

                    # 3. Construir ComprobanteElectronico (Datos dummy/por defecto por ahora)
                    comprobante = ComprobanteElectronico(
                        tipo_documento=TipoDocumentoEnum.DNI,
                        numero_documento="00000000",
                        nombres_completos="CLIENTE GENERICO",
                        direccion="LIMA",
                        observacion=pedido_data.notas_cliente or "Sin observaciones",
                        tipo_comprobante=TipoComprobanteEnum.BOLETA
                    )

                    # 4. Construir PlatoInsertRequest
                    plato_request = PlatoInsertRequest(
                        mesa=mesa_domotica,
                        platos=platos_domotica,
                        comprobante=comprobante
                    )

                    # 5. Publicar
                    await rabbitmq_service.publish_pedido_creado(plato_request.model_dump(mode='json'))
                else:
                    logger.warning("RabbitMQ no está conectado. No se envió la notificación de pedido creado.")
            except Exception as e:
                logger.error(f"Error al enviar notificación a RabbitMQ: {str(e)}")
            # ----------------------------

            return PedidoCompletoResponse(**response_dict)

        except IntegrityError as e:
            # Rollback implícito por SQLAlchemy
            raise PedidoConflictError(
                f"Error al crear el pedido completo. Conflicto de integridad: {str(e)}"
            )

    async def enviar_pedido_por_token(
        self, pedido_data: PedidoEnviarRequest
    ) -> PedidoEnviarResponse:
        """
        Crea un pedido usando el token de sesión de mesa compartido.

        Este método obtiene los precios automáticamente desde la base de datos,
        sin necesidad de que el frontend los envíe. Valida la sesión de mesa
        y crea el pedido asociándolo a la sesión.

        Parameters
        ----------
        pedido_data : PedidoEnviarRequest
            Datos del pedido con token de sesión e items (sin precios).

        Returns
        -------
        PedidoEnviarResponse
            Respuesta con el pedido creado y todos los cálculos.

        Raises
        ------
        PedidoValidationError
            Si el token no existe, la sesión no está activa, o algún producto
            no existe o no está disponible.
        PedidoConflictError
            Si hay un conflicto de integridad en la base de datos.
        """
        try:
            # 1. Validar que la sesión existe y está activa
            sesion = await self.sesion_mesa_repository.get_by_token(
                pedido_data.token_sesion
            )
            if not sesion:
                raise PedidoValidationError(
                    f"No se encontró una sesión con el token {pedido_data.token_sesion}"
                )

            # Validar que el estado sea ACTIVA
            if sesion.estado != EstadoSesionMesa.ACTIVA:
                raise PedidoValidationError(
                    "La sesión de mesa no está activa. No se pueden crear pedidos."
                )

            # Validar que no esté expirada por tiempo
            if sesion.esta_expirada():
                raise PedidoValidationError(
                    "La sesión ha expirado. Por favor, solicite una nueva sesión en el login."
                )

            # 2. Validar que la mesa existe (aunque debería existir si hay sesión)
            mesa = await self.mesa_repository.get_by_id(sesion.id_mesa)
            if not mesa:
                raise PedidoValidationError(
                    f"No se encontró la mesa con ID {sesion.id_mesa}"
                )

            # 3. Validar productos y calcular precios
            subtotal = Decimal("0.00")
            items_validados = []

            for item in pedido_data.items:
                # Obtener producto desde BD
                producto = await self.producto_repository.get_by_id(item.id_producto)
                if not producto:
                    raise PedidoValidationError(
                        f"No se encontró el producto con ID {item.id_producto}"
                    )
                if not producto.disponible:
                    raise PedidoValidationError(
                        f"El producto '{producto.nombre}' no está disponible actualmente"
                    )

                # Calcular precio de opciones
                precio_opciones = Decimal("0.00")
                opciones_validadas = []
                for opcion in item.opciones:
                    producto_opcion = await self.producto_opcion_repository.get_by_id(
                        opcion.id_producto_opcion
                    )
                    if not producto_opcion:
                        raise PedidoValidationError(
                            f"No se encontró la opción con ID {opcion.id_producto_opcion}"
                        )
                    precio_opciones += producto_opcion.precio_adicional
                    opciones_validadas.append(producto_opcion)

                # Calcular subtotal del item
                precio_total_unitario = producto.precio_base + precio_opciones
                item_subtotal = Decimal(str(item.cantidad)) * precio_total_unitario
                subtotal += item_subtotal

                # Guardar datos validados
                items_validados.append({
                    "item": item,
                    "producto": producto,
                    "opciones": opciones_validadas,
                    "precio_opciones": precio_opciones,
                    "item_subtotal": item_subtotal
                })

            # 4. Calcular totales (por ahora sin impuestos ni descuentos)
            impuestos = Decimal("0.00")
            descuentos = Decimal("0.00")
            total = subtotal

            # 5. Generar número de pedido
            numero_pedido = await self._generate_numero_pedido(sesion.id_mesa)

            # 6. Crear el pedido con id_sesion_mesa
            pedido = PedidoModel(
                id_mesa=sesion.id_mesa,
                id_usuario=sesion.id_usuario_creador,  # Usuario que creó la sesión
                id_sesion_mesa=sesion.id,  # ✅ Asociar a la sesión
                numero_pedido=numero_pedido,
                estado=EstadoPedido.PENDIENTE,
                subtotal=subtotal,
                impuestos=impuestos,
                descuentos=descuentos,
                total=total,
                notas_cliente=pedido_data.notas_cliente,
                notas_cocina=pedido_data.notas_cocina,
            )

            # Persistir el pedido
            created_pedido = await self.repository.create(pedido)

            # 7. Crear todos los items con sus opciones
            productos_detalle = []
            for item_data in items_validados:
                item = item_data["item"]
                producto = item_data["producto"]
                opciones = item_data["opciones"]
                precio_opciones = item_data["precio_opciones"]
                item_subtotal = item_data["item_subtotal"]

                # Crear el item
                pedido_producto = PedidoProductoModel(
                    id_pedido=created_pedido.id,
                    id_producto=producto.id,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio_base,
                    precio_opciones=precio_opciones,
                    subtotal=item_subtotal,
                    notas_personalizacion=item.notas_personalizacion,
                )
                created_item = await self.pedido_producto_repository.create(pedido_producto)

                # Crear opciones del item
                opciones_detalle = []
                for idx, opcion in enumerate(opciones):
                    pedido_opcion = PedidoOpcionModel(
                        id_pedido_producto=created_item.id,
                        id_producto_opcion=opcion.id,
                        precio_adicional=opcion.precio_adicional,
                    )
                    created_opcion = await self.pedido_opcion_repository.create(pedido_opcion)

                    # Construir detalle de opción
                    opciones_detalle.append(
                        ProductoOpcionDetalle(
                            id=created_opcion.id,
                            id_producto_opcion=opcion.id,
                            nombre_opcion=opcion.nombre,
                            precio_adicional=opcion.precio_adicional,
                        )
                    )

                # Construir detalle de producto
                productos_detalle.append(
                    ProductoPedidoDetalle(
                        id=created_item.id,
                        id_producto=producto.id,
                        nombre_producto=producto.nombre,
                        precio_base=producto.precio_base,
                        imagen_path=producto.imagen_path,
                        imagen_alt_text=producto.imagen_alt_text,
                        cantidad=item.cantidad,
                        precio_unitario=producto.precio_base,
                        precio_opciones=precio_opciones,
                        subtotal=item_subtotal,
                        notas_personalizacion=item.notas_personalizacion,
                        opciones=opciones_detalle,
                    )
                )

            # 8. Commit de la transacción
            await self.session.flush()
            impuestos = created_pedido.impuestos or Decimal("0.00")
            descuentos = created_pedido.descuentos or Decimal("0.00")
            total = created_pedido.total or Decimal("0.00")
            # 9. Construir respuesta completa
            pedido_detalle = PedidoHistorialDetalle(
                id=created_pedido.id,
                numero_pedido=created_pedido.numero_pedido,
                estado=created_pedido.estado,
                subtotal=created_pedido.subtotal,
                impuestos=impuestos,
                descuentos=descuentos,
                total=total,
                notas_cliente=created_pedido.notas_cliente,
                notas_cocina=created_pedido.notas_cocina,
                fecha_creacion=created_pedido.fecha_creacion,
                fecha_confirmado=created_pedido.fecha_confirmado,
                fecha_en_preparacion=created_pedido.fecha_en_preparacion,
                fecha_listo=created_pedido.fecha_listo,
                fecha_entregado=created_pedido.fecha_entregado,
                productos=productos_detalle,
            )

            # --- Integración RabbitMQ ---
            try:
                rabbitmq_service = await get_rabbitmq_service()
                if rabbitmq_service.is_connected:
                    # 1. Construir MesaDomotica
                    # mesa ya fue validada y cargada en paso 2
                    zona_nombre = mesa.zona.nombre if mesa.zona else "SIN ZONA"
                    mesa_domotica = MesaDomotica(
                        nombre=mesa.numero,
                        zona=zona_nombre,
                        nota=mesa.nota,
                        estado=MesaEstadoEnum.OCUPADA
                    )

                    # 2. Construir lista de ProductoDomotica
                    platos_domotica = []
                    categoria_cache = {}

                    for item_data in items_validados:
                        producto = item_data["producto"]
                        item = item_data["item"]
                        
                        # Obtener nombre de categoría
                        cat_nombre = "GENERAL"
                        if producto.id_categoria in categoria_cache:
                            cat_nombre = categoria_cache[producto.id_categoria]
                        else:
                            categoria = await self.categoria_repository.get_by_id(producto.id_categoria)
                            if categoria:
                                cat_nombre = categoria.nombre
                                categoria_cache[producto.id_categoria] = cat_nombre
                        
                        plato = ProductoDomotica(
                            categoria=cat_nombre,
                            nombre=producto.nombre,
                            stock=str(item.cantidad),
                            precio=str(producto.precio_base)
                        )
                        platos_domotica.append(plato)

                    # 3. Construir ComprobanteElectronico
                    comprobante = ComprobanteElectronico(
                        tipo_documento=TipoDocumentoEnum.DNI,
                        numero_documento="00000000",
                        nombres_completos="CLIENTE GENERICO",
                        direccion="LIMA",
                        observacion=pedido_data.notas_cliente or "Sin observaciones",
                        tipo_comprobante=TipoComprobanteEnum.BOLETA
                    )

                    # 4. Construir PlatoInsertRequest
                    plato_request = PlatoInsertRequest(
                        mesa=mesa_domotica,
                        platos=platos_domotica,
                        comprobante=comprobante
                    )

                    # 5. Publicar
                    await rabbitmq_service.publish_pedido_creado(plato_request.model_dump(mode='json'))
                else:
                    logger.warning("RabbitMQ no está conectado. No se envió la notificación de pedido creado.")
            except Exception as e:
                logger.error(f"Error al enviar notificación a RabbitMQ: {str(e)}")
            # ----------------------------

            return PedidoEnviarResponse(
                status=201,
                message="Pedido creado exitosamente",
                pedido=pedido_detalle,
            )

        except IntegrityError as e:
            # Rollback implícito por SQLAlchemy
            raise PedidoConflictError(
                f"Error al crear el pedido con token de sesión. Conflicto de integridad: {str(e)}"
            )

    async def obtener_historial_por_token(
        self, token_sesion: str
    ) -> PedidoHistorialResponse:
        """
        Obtiene el historial completo de pedidos para un token de sesión.

        Lista todos los pedidos realizados en una sesión de mesa compartida,
        con información detallada de productos y opciones.

        Parameters
        ----------
        token_sesion : str
            Token de sesión de mesa (ULID de 26 caracteres).

        Returns
        -------
        PedidoHistorialResponse
            Respuesta con metadatos de la sesión y lista completa de pedidos.

        Raises
        ------
        PedidoValidationError
            Si el token no existe.
        """
        # 1. Validar que la sesión existe
        sesion = await self.sesion_mesa_repository.get_by_token(token_sesion)
        if not sesion:
            raise PedidoValidationError(
                f"No se encontró una sesión con el token {token_sesion}"
            )

        # Validar si la sesión está cerrada o expirada
        sesion_cerrada = (
            sesion.estado != EstadoSesionMesa.ACTIVA or sesion.esta_expirada()
        )

        if sesion_cerrada:
            # Retornar respuesta con lista vacía y mensaje
            return PedidoHistorialResponse(
                token_sesion=token_sesion,
                id_mesa=sesion.id_mesa,
                estado_sesion=sesion.estado.value,
                mensaje="Esta sesión ha sido cerrada o ha expirado. No hay pedidos disponibles.",
                total_pedidos=0,
                pedidos=[]
            )

        # 2. Obtener todos los pedidos de esta sesión (detallado)
        pedidos, total = await self.repository.get_all_detallado(
            skip=0,
            limit=1000,  # Límite alto para obtener todos los pedidos de la sesión
            id_sesion_mesa=sesion.id
        )

        # 3. Construir lista de pedidos detallados
        pedidos_detalle = []
        for pedido in pedidos:
            # Procesar productos del pedido con sus opciones
            productos_detalle = []
            for pedido_producto in pedido.pedidos_productos:
                producto_rel = pedido_producto.producto
                nombre_producto = producto_rel.nombre if producto_rel else "Producto"
                precio_base = (
                    producto_rel.precio_base
                    if producto_rel and producto_rel.precio_base is not None
                    else pedido_producto.precio_unitario
                )
                imagen_path = producto_rel.imagen_path if producto_rel else None
                imagen_alt_text = (
                    producto_rel.imagen_alt_text if producto_rel else None
                )
                # Procesar opciones del producto
                opciones_detalle = []
                for pedido_opcion in pedido_producto.pedidos_opciones:
                    opciones_detalle.append(
                        ProductoOpcionDetalle(
                            id=pedido_opcion.id,
                            id_producto_opcion=pedido_opcion.id_producto_opcion,
                            nombre_opcion=(
                                pedido_opcion.producto_opcion.nombre
                                if pedido_opcion.producto_opcion
                                else "Opción"
                            ),
                            precio_adicional=pedido_opcion.precio_adicional,
                        )
                    )

                # Construir el producto detallado
                productos_detalle.append(
                    ProductoPedidoDetalle(
                        id=pedido_producto.id,
                        id_producto=pedido_producto.id_producto,
                        nombre_producto=nombre_producto,
                        precio_base=precio_base,
                        imagen_path=imagen_path,
                        imagen_alt_text=imagen_alt_text,
                        cantidad=pedido_producto.cantidad,
                        precio_unitario=pedido_producto.precio_unitario,
                        precio_opciones=pedido_producto.precio_opciones,
                        subtotal=pedido_producto.subtotal,
                        notas_personalizacion=pedido_producto.notas_personalizacion,
                        opciones=opciones_detalle,
                    )
                )
            impuestos = pedido.impuestos or Decimal("0.00")
            descuentos = pedido.descuentos or Decimal("0.00")
            # Construir el pedido detallado
            pedidos_detalle.append(
                PedidoHistorialDetalle(
                    id=pedido.id,
                    numero_pedido=pedido.numero_pedido,
                    estado=pedido.estado,
                    subtotal=pedido.subtotal,
                    impuestos=impuestos,
                    descuentos=descuentos,
                    total=pedido.total,
                    notas_cliente=pedido.notas_cliente,
                    notas_cocina=pedido.notas_cocina,
                    fecha_creacion=pedido.fecha_creacion,
                    fecha_confirmado=pedido.fecha_confirmado,
                    fecha_en_preparacion=pedido.fecha_en_preparacion,
                    fecha_listo=pedido.fecha_listo,
                    fecha_entregado=pedido.fecha_entregado,
                    productos=productos_detalle,
                )
            )

        # 4. Construir respuesta completa
        return PedidoHistorialResponse(
            token_sesion=token_sesion,
            id_mesa=sesion.id_mesa,
            estado_sesion=sesion.estado.value,
            mensaje=None,  # None si la sesión está activa
            total_pedidos=total,
            pedidos=pedidos_detalle,
        )
