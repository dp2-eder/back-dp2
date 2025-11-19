"""
Repositorio para la gestión de items de pedidos (pedido_producto) en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_

from src.models.pedidos.pedido_producto_model import PedidoProductoModel


class PedidoProductoRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de items de pedidos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los items/productos de pedidos en el sistema.

    Attributes
    ----------
    session : AsyncSession
        Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.session = session

    async def create(self, pedido_producto: PedidoProductoModel) -> PedidoProductoModel:
        """
        Crea un nuevo item de pedido en la base de datos.

        Parameters
        ----------
        pedido_producto : PedidoProductoModel
            Instancia del modelo de item de pedido a crear.

        Returns
        -------
        PedidoProductoModel
            El modelo de item de pedido creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(pedido_producto)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(pedido_producto)
            return pedido_producto
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, pedido_producto_id: str) -> Optional[PedidoProductoModel]:
        """
        Obtiene un item de pedido por su identificador único.

        Parameters
        ----------
        pedido_producto_id : str
            Identificador único del item de pedido a buscar (ULID).

        Returns
        -------
        Optional[PedidoProductoModel]
            El item de pedido encontrado o None si no existe.
        """
        query = select(PedidoProductoModel).where(PedidoProductoModel.id == pedido_producto_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_pedido_id(self, pedido_id: str) -> List[PedidoProductoModel]:
        """
        Obtiene todos los items de un pedido específico.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido (ULID).

        Returns
        -------
        List[PedidoProductoModel]
            Lista de items del pedido.
        """
        query = select(PedidoProductoModel).where(
            PedidoProductoModel.id_pedido == pedido_id
        ).order_by(PedidoProductoModel.fecha_creacion)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, pedido_producto_id: str) -> bool:
        """
        Elimina un item de pedido de la base de datos por su ID.

        Parameters
        ----------
        pedido_producto_id : str
            Identificador único del item de pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si el item fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(PedidoProductoModel).where(PedidoProductoModel.id == pedido_producto_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, pedido_producto_id: str, **kwargs) -> Optional[PedidoProductoModel]:
        """
        Actualiza un item de pedido existente con los valores proporcionados.

        Parameters
        ----------
        pedido_producto_id : str
            Identificador único del item de pedido a actualizar (ULID).
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[PedidoProductoModel]
            El item de pedido actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(PedidoProductoModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(pedido_producto_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(PedidoProductoModel)
                .where(PedidoProductoModel.id == pedido_producto_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el item actualizado
            updated_item = await self.get_by_id(pedido_producto_id)

            # Si no se encontró el item, retornar None
            if not updated_item:
                return None

            return updated_item
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        id_pedido: Optional[str] = None,
        id_producto: Optional[str] = None
    ) -> Tuple[List[PedidoProductoModel], int]:
        """
        Obtiene una lista paginada de items de pedidos y el total de registros.

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
        Tuple[List[PedidoProductoModel], int]
            Tupla con la lista de items y el número total de registros.
        """
        # Construir la consulta base
        query = select(PedidoProductoModel)
        count_query = select(func.count(PedidoProductoModel.id))

        # Aplicar filtros si están presentes
        filters = []
        if id_pedido is not None:
            filters.append(PedidoProductoModel.id_pedido == id_pedido)
        if id_producto is not None:
            filters.append(PedidoProductoModel.id_producto == id_producto)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Aplicar paginación y ordenamiento
        query = query.order_by(PedidoProductoModel.fecha_creacion.desc()).offset(skip).limit(limit)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            items = result.scalars().all()
            total = count_result.scalar() or 0

            return list(items), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise
