"""
Repositorio para la gestión de pedidos en el sistema.
"""

from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_, extract
from sqlalchemy.orm import selectinload

from src.models.pedidos.pedido_model import PedidoModel
from src.models.pedidos.pedido_producto_model import PedidoProductoModel
from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel
from src.core.enums.pedido_enums import EstadoPedido


class PedidoRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de pedidos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los pedidos en el sistema, siguiendo el patrón Repository.

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

    async def create(self, pedido: PedidoModel) -> PedidoModel:
        """
        Crea un nuevo pedido en la base de datos.

        Parameters
        ----------
        pedido : PedidoModel
            Instancia del modelo de pedido a crear.

        Returns
        -------
        PedidoModel
            El modelo de pedido creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(pedido)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(pedido)
            return pedido
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, pedido_id: str) -> Optional[PedidoModel]:
        """
        Obtiene un pedido por su identificador único.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a buscar (ULID).

        Returns
        -------
        Optional[PedidoModel]
            El pedido encontrado o None si no existe.
        """
        query = select(PedidoModel).where(PedidoModel.id == pedido_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_numero_pedido(self, numero_pedido: str) -> Optional[PedidoModel]:
        """
        Obtiene un pedido por su número único.

        Parameters
        ----------
        numero_pedido : str
            Número único del pedido a buscar.

        Returns
        -------
        Optional[PedidoModel]
            El pedido encontrado o None si no existe.
        """
        query = select(PedidoModel).where(PedidoModel.numero_pedido == numero_pedido)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, pedido_id: str) -> bool:
        """
        Elimina un pedido de la base de datos por su ID.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a eliminar (ULID).

        Returns
        -------
        bool
            True si el pedido fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(PedidoModel).where(PedidoModel.id == pedido_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, pedido_id: str, **kwargs) -> Optional[PedidoModel]:
        """
        Actualiza un pedido existente con los valores proporcionados.

        Parameters
        ----------
        pedido_id : str
            Identificador único del pedido a actualizar (ULID).
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[PedidoModel]
            El pedido actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(PedidoModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(pedido_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(PedidoModel)
                .where(PedidoModel.id == pedido_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el pedido actualizado
            updated_pedido = await self.get_by_id(pedido_id)

            # Si no se encontró el pedido, retornar None
            if not updated_pedido:
                return None

            return updated_pedido
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoPedido] = None,
        id_mesa: Optional[str] = None,
        id_usuario: Optional[str] = None,
        id_sesion_mesa: Optional[str] = None
    ) -> Tuple[List[PedidoModel], int]:
        """
        Obtiene una lista paginada de pedidos y el total de registros.

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
        Tuple[List[PedidoModel], int]
            Tupla con la lista de pedidos y el número total de registros.
        """
        # Construir la consulta base
        query = select(PedidoModel)
        count_query = select(func.count(PedidoModel.id))

        # Aplicar filtros si están presentes
        filters = []
        if estado is not None:
            filters.append(PedidoModel.estado == estado)
        if id_mesa is not None:
            filters.append(PedidoModel.id_mesa == id_mesa)
        if id_usuario is not None:
            filters.append(PedidoModel.id_usuario == id_usuario)
        if id_sesion_mesa is not None:
            filters.append(PedidoModel.id_sesion_mesa == id_sesion_mesa)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Aplicar paginación y ordenamiento
        query = query.order_by(PedidoModel.fecha_creacion.desc()).offset(skip).limit(limit)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            pedidos = result.scalars().all()
            total = count_result.scalar() or 0

            return list(pedidos), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def get_last_sequence_for_date_and_mesa(
        self, date: datetime, numero_mesa: str
    ) -> int:
        """
        Obtiene la última secuencia de pedido para una fecha y mesa específica.

        Parameters
        ----------
        date : datetime
            Fecha para la cual obtener la secuencia.
        numero_mesa : str
            Número de mesa.

        Returns
        -------
        int
            La última secuencia encontrada, o 0 si no hay pedidos.
        """
        try:
            # Construir el patrón para el numero_pedido
            # Formato: YYYYMMDD-M{numero_mesa}-{seq:03d}
            date_str = date.strftime("%Y%m%d")
            pattern = f"{date_str}-M{numero_mesa}-%"

            # Consultar los pedidos que coincidan con el patrón
            query = (
                select(PedidoModel.numero_pedido)
                .where(PedidoModel.numero_pedido.like(pattern))
                .order_by(PedidoModel.numero_pedido.desc())
                .limit(1)
            )

            result = await self.session.execute(query)
            last_numero = result.scalar()

            if last_numero:
                # Extraer la secuencia del numero_pedido
                # Formato: YYYYMMDD-M{numero_mesa}-{seq:03d}
                parts = last_numero.split("-")
                if len(parts) == 3:
                    try:
                        return int(parts[2])
                    except ValueError:
                        return 0

            return 0
        except SQLAlchemyError:
            raise

    async def get_all_detallado(
        self,
        skip: int = 0,
        limit: int = 100,
        estado: Optional[EstadoPedido] = None,
        id_mesa: Optional[str] = None,
        id_usuario: Optional[str] = None,
        id_sesion_mesa: Optional[str] = None
    ) -> Tuple[List[PedidoModel], int]:
        """
        Obtiene una lista paginada de pedidos con productos y opciones eager-loaded.

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
        Tuple[List[PedidoModel], int]
            Tupla con la lista de pedidos (con relaciones cargadas) y el número total de registros.
        """
        # Construir la consulta base con eager loading
        query = (
            select(PedidoModel)
            .outerjoin(PedidoModel.pedidos_productos)
            .outerjoin(PedidoProductoModel.pedidos_opciones)
            .options(
                selectinload(PedidoModel.pedidos_productos)
                .selectinload(PedidoProductoModel.producto),
                selectinload(PedidoModel.pedidos_productos)
                .selectinload(PedidoProductoModel.pedidos_opciones)
                .selectinload(PedidoOpcionModel.producto_opcion)
            )
        )
        count_query = select(func.count(PedidoModel.id.distinct()))

        # Aplicar filtros si están presentes
        filters = []
        if estado is not None:
            filters.append(PedidoModel.estado == estado)
        if id_mesa is not None:
            filters.append(PedidoModel.id_mesa == id_mesa)
        if id_usuario is not None:
            filters.append(PedidoModel.id_usuario == id_usuario)
        if id_sesion_mesa is not None:
            filters.append(PedidoModel.id_sesion_mesa == id_sesion_mesa)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Aplicar paginación y ordenamiento
        query = query.order_by(PedidoModel.fecha_creacion.desc()).offset(skip).limit(limit)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados con unique() para evitar duplicados por los joins
            pedidos = result.unique().scalars().all()
            total = count_result.scalar() or 0

            return list(pedidos), total
        except SQLAlchemyError:
            raise
