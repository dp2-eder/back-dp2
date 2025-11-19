"""
Repositorio para la gestión de opciones de pedidos en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel


class PedidoOpcionRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de opciones de pedidos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las opciones de pedidos en el sistema, siguiendo el patrón Repository.

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

    async def create(self, pedido_opcion: PedidoOpcionModel) -> PedidoOpcionModel:
        """
        Crea una nueva opción de pedido en la base de datos.

        Parameters
        ----------
        pedido_opcion : PedidoOpcionModel
            Instancia del modelo de opción de pedido a crear.

        Returns
        -------
        PedidoOpcionModel
            El modelo de opción de pedido creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(pedido_opcion)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(pedido_opcion)
            return pedido_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, pedido_opcion_id: str) -> Optional[PedidoOpcionModel]:
        """
        Obtiene una opción de pedido por su identificador único.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a buscar (ULID).

        Returns
        -------
        Optional[PedidoOpcionModel]
            La opción de pedido encontrada o None si no existe.
        """
        query = select(PedidoOpcionModel).where(PedidoOpcionModel.id == pedido_opcion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_pedido_producto_id(self, pedido_producto_id: str) -> List[PedidoOpcionModel]:
        """
        Obtiene todas las opciones de un item de pedido específico.

        Parameters
        ----------
        pedido_producto_id : str
            Identificador único del item de pedido (ULID).

        Returns
        -------
        List[PedidoOpcionModel]
            Lista de opciones del item de pedido.
        """
        query = select(PedidoOpcionModel).where(
            PedidoOpcionModel.id_pedido_producto == pedido_producto_id
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, pedido_opcion_id: str) -> bool:
        """
        Elimina una opción de pedido de la base de datos por su ID.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si la opción fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(PedidoOpcionModel).where(PedidoOpcionModel.id == pedido_opcion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, pedido_opcion_id: str, **kwargs) -> Optional[PedidoOpcionModel]:
        """
        Actualiza una opción de pedido existente con los valores proporcionados.

        Parameters
        ----------
        pedido_opcion_id : str
            Identificador único de la opción de pedido a actualizar (ULID).
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[PedidoOpcionModel]
            La opción de pedido actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(PedidoOpcionModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(pedido_opcion_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(PedidoOpcionModel)
                .where(PedidoOpcionModel.id == pedido_opcion_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar la opción de pedido actualizada
            updated_opcion = await self.get_by_id(pedido_opcion_id)

            # Si no se encontró, retornar None
            if not updated_opcion:
                return None

            return updated_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100, id_pedido_producto: Optional[str] = None
    ) -> Tuple[List[PedidoOpcionModel], int]:
        """
        Obtiene una lista paginada de opciones de pedidos y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_pedido_producto : str, optional
            Filtrar por ID de item de pedido.

        Returns
        -------
        Tuple[List[PedidoOpcionModel], int]
            Tupla con la lista de opciones de pedidos y el número total de registros.
        """
        # Consulta base
        query = select(PedidoOpcionModel)
        count_query = select(func.count(PedidoOpcionModel.id))

        # Aplicar filtros
        if id_pedido_producto:
            query = query.where(PedidoOpcionModel.id_pedido_producto == id_pedido_producto)
            count_query = count_query.where(PedidoOpcionModel.id_pedido_producto == id_pedido_producto)

        # Aplicar paginación
        query = query.offset(skip).limit(limit)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            opciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(opciones), total
        except SQLAlchemyError:
            raise
