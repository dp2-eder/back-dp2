"""
Servicio para la gestión de opciones de pedidos en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.pedidos.pedido_opcion_repository import PedidoOpcionRepository
from src.repositories.pedidos.pedido_producto_repository import PedidoProductoRepository
from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.api.schemas.pedido_opcion_schema import (
    PedidoOpcionCreate,
    PedidoOpcionUpdate,
    PedidoOpcionResponse,
    PedidoOpcionSummary,
    PedidoOpcionList,
)
from src.business_logic.exceptions.pedido_opcion_exceptions import (
    PedidoOpcionValidationError,
    PedidoOpcionNotFoundError,
    PedidoOpcionConflictError,
)


class PedidoOpcionService:
    """Servicio para la gestión de opciones de pedidos en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con opciones de pedidos, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : PedidoOpcionRepository
        Repositorio para acceso a datos de opciones de pedidos.
    pedido_producto_repository : PedidoProductoRepository
        Repositorio para validar la existencia de items de pedidos.
    producto_opcion_repository : ProductoOpcionRepository
        Repositorio para validar la existencia de opciones de productos.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = PedidoOpcionRepository(session)
        self.pedido_producto_repository = PedidoProductoRepository(session)
        self.producto_opcion_repository = ProductoOpcionRepository(session)

    async def create_pedido_opcion(self, pedido_opcion_data: PedidoOpcionCreate) -> PedidoOpcionResponse:
        """
        Crea una nueva opción de pedido en el sistema.

        Parameters
        ----------
        pedido_opcion_data : PedidoOpcionCreate
            Datos para crear la nueva opción de pedido.

        Returns
        -------
        PedidoOpcionResponse
            Esquema de respuesta con los datos de la opción de pedido creada.

        Raises
        ------
        PedidoOpcionValidationError
            Si no existe el pedido_producto o el producto_opcion.
        PedidoOpcionConflictError
            Si ya existe la opción de pedido.
        """
        # Validar que existe el pedido_producto
        pedido_producto = await self.pedido_producto_repository.get_by_id(
            pedido_opcion_data.id_pedido_producto
        )
        if not pedido_producto:
            raise PedidoOpcionValidationError(
                f"No existe el item de pedido con ID {pedido_opcion_data.id_pedido_producto}"
            )

        # Validar que existe el producto_opcion
        producto_opcion = await self.producto_opcion_repository.get_by_id(
            pedido_opcion_data.id_producto_opcion
        )
        if not producto_opcion:
            raise PedidoOpcionValidationError(
                f"No existe la opción de producto con ID {pedido_opcion_data.id_producto_opcion}"
            )

        try:
            # Crear modelo de pedido_opcion desde los datos
            pedido_opcion = PedidoOpcionModel(
                id_pedido_producto=pedido_opcion_data.id_pedido_producto,
                id_producto_opcion=pedido_opcion_data.id_producto_opcion,
                precio_adicional=pedido_opcion_data.precio_adicional,
            )

            # Persistir en la base de datos
            created_pedido_opcion = await self.repository.create(pedido_opcion)

            # Convertir y retornar como esquema de respuesta
            return PedidoOpcionResponse.model_validate(created_pedido_opcion)
        except IntegrityError:
            # Capturar errores de integridad
            raise PedidoOpcionConflictError(
                f"Error al crear la opción de pedido"
            )

    async def get_pedido_opcion_by_id(self, pedido_opcion_id: str) -> PedidoOpcionResponse:
        """
        Obtiene una opción de pedido por su ID.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a buscar (ULID).

        Returns
        -------
        PedidoOpcionResponse
            Esquema de respuesta con los datos de la opción de pedido.

        Raises
        ------
        PedidoOpcionNotFoundError
            Si no se encuentra una opción de pedido con el ID proporcionado.
        """
        # Buscar la opción de pedido por su ID
        pedido_opcion = await self.repository.get_by_id(pedido_opcion_id)

        # Verificar si existe
        if not pedido_opcion:
            raise PedidoOpcionNotFoundError(f"No se encontró la opción de pedido con ID {pedido_opcion_id}")

        # Convertir y retornar como esquema de respuesta
        return PedidoOpcionResponse.model_validate(pedido_opcion)

    async def get_opciones_by_pedido_producto(self, pedido_producto_id: str) -> PedidoOpcionList:
        """
        Obtiene todas las opciones de un item de pedido específico.

        Parameters
        ----------
        pedido_producto_id : str
            Identificador único del item de pedido (ULID).

        Returns
        -------
        PedidoOpcionList
            Esquema con la lista de opciones y el total.

        Raises
        ------
        PedidoOpcionValidationError
            Si no existe el pedido_producto.
        """
        # Validar que existe el pedido_producto
        pedido_producto = await self.pedido_producto_repository.get_by_id(pedido_producto_id)
        if not pedido_producto:
            raise PedidoOpcionValidationError(
                f"No existe el item de pedido con ID {pedido_producto_id}"
            )

        # Obtener opciones desde el repositorio
        opciones = await self.repository.get_by_pedido_producto_id(pedido_producto_id)

        # Convertir modelos a esquemas de resumen
        opcion_summaries = [PedidoOpcionSummary.model_validate(opcion) for opcion in opciones]

        # Retornar esquema de lista
        return PedidoOpcionList(items=opcion_summaries, total=len(opcion_summaries))

    async def delete_pedido_opcion(self, pedido_opcion_id: str) -> bool:
        """
        Elimina una opción de pedido por su ID.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si la opción de pedido fue eliminada correctamente.

        Raises
        ------
        PedidoOpcionNotFoundError
            Si no se encuentra una opción de pedido con el ID proporcionado.
        """
        # Verificar primero si la opción de pedido existe
        pedido_opcion = await self.repository.get_by_id(pedido_opcion_id)
        if not pedido_opcion:
            raise PedidoOpcionNotFoundError(f"No se encontró la opción de pedido con ID {pedido_opcion_id}")

        # Eliminar la opción de pedido
        result = await self.repository.delete(pedido_opcion_id)
        return result

    async def get_pedido_opciones(self, skip: int = 0, limit: int = 100) -> PedidoOpcionList:
        """
        Obtiene una lista paginada de opciones de pedidos.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        PedidoOpcionList
            Esquema con la lista de opciones de pedidos y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise PedidoOpcionValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise PedidoOpcionValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener opciones de pedidos desde el repositorio
        pedido_opciones, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        pedido_opcion_summaries = [PedidoOpcionSummary.model_validate(opcion) for opcion in pedido_opciones]

        # Retornar esquema de lista
        return PedidoOpcionList(items=pedido_opcion_summaries, total=total)

    async def update_pedido_opcion(self, pedido_opcion_id: str, pedido_opcion_data: PedidoOpcionUpdate) -> PedidoOpcionResponse:
        """
        Actualiza una opción de pedido existente.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a actualizar (ULID).
        pedido_opcion_data : PedidoOpcionUpdate
            Datos para actualizar la opción de pedido.

        Returns
        -------
        PedidoOpcionResponse
            Esquema de respuesta con los datos de la opción de pedido actualizada.

        Raises
        ------
        PedidoOpcionNotFoundError
            Si no se encuentra una opción de pedido con el ID proporcionado.
        PedidoOpcionConflictError
            Si hay un conflicto con los datos.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = pedido_opcion_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la opción actual
            return await self.get_pedido_opcion_by_id(pedido_opcion_id)

        try:
            # Actualizar la opción de pedido
            updated_pedido_opcion = await self.repository.update(pedido_opcion_id, **update_data)

            # Verificar si la opción fue encontrada
            if not updated_pedido_opcion:
                raise PedidoOpcionNotFoundError(f"No se encontró la opción de pedido con ID {pedido_opcion_id}")

            # Convertir y retornar como esquema de respuesta
            return PedidoOpcionResponse.model_validate(updated_pedido_opcion)
        except IntegrityError:
            # Capturar errores de integridad
            raise PedidoOpcionConflictError(
                f"Error al actualizar la opción de pedido"
            )
