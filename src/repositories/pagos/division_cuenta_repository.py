"""
Repositorio para la gestión de divisiones de cuenta en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload

from src.models.pagos.division_cuenta_model import DivisionCuentaModel


class DivisionCuentaRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de divisiones de cuenta.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las divisiones de cuenta en el sistema.

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

    async def create(self, division: DivisionCuentaModel) -> DivisionCuentaModel:
        """
        Crea una nueva división de cuenta en la base de datos.

        Parameters
        ----------
        division : DivisionCuentaModel
            Instancia del modelo de división a crear.

        Returns
        -------
        DivisionCuentaModel
            El modelo de división creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de creación.
        """
        try:
            self.session.add(division)
            await self.session.flush()
            await self.session.refresh(division)
            return division
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, division_id: str) -> Optional[DivisionCuentaModel]:
        """
        Obtiene una división de cuenta por su ID.

        Parameters
        ----------
        division_id : str
            Identificador único de la división (ULID).

        Returns
        -------
        Optional[DivisionCuentaModel]
            El modelo de división si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = select(DivisionCuentaModel).where(DivisionCuentaModel.id == division_id)
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise e

    async def get_with_detalles(self, division_id: str) -> Optional[DivisionCuentaModel]:
        """
        Obtiene una división con sus detalles cargados.

        Parameters
        ----------
        division_id : str
            Identificador único de la división (ULID).

        Returns
        -------
        Optional[DivisionCuentaModel]
            El modelo de división con detalles cargados, None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaModel)
                .options(selectinload(DivisionCuentaModel.detalles))
                .where(DivisionCuentaModel.id == division_id)
            )
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise e

    async def get_by_pedido(self, pedido_id: str) -> List[DivisionCuentaModel]:
        """
        Obtiene divisiones de cuenta por pedido.

        Parameters
        ----------
        pedido_id : str
            ID del pedido para filtrar divisiones.

        Returns
        -------
        List[DivisionCuentaModel]
            Lista de divisiones del pedido.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaModel)
                .where(DivisionCuentaModel.id_pedido == pedido_id)
                .order_by(DivisionCuentaModel.created_at.desc())
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise e

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[DivisionCuentaModel], int]:
        """
        Obtiene todas las divisiones con paginación.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[DivisionCuentaModel], int]
            Tupla con la lista de divisiones y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaModel)
                .order_by(DivisionCuentaModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            count_query = select(func.count(DivisionCuentaModel.id))

            result = await self.session.execute(query)
            divisiones = list(result.scalars().all())

            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0

            return divisiones, total
        except SQLAlchemyError as e:
            raise e

    async def update(self, division_id: str, **kwargs) -> Optional[DivisionCuentaModel]:
        """
        Actualiza una división existente.

        Parameters
        ----------
        division_id : str
            Identificador único de la división a actualizar (ULID).
        **kwargs
            Campos a actualizar con sus nuevos valores.

        Returns
        -------
        Optional[DivisionCuentaModel]
            El modelo de división actualizado si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de actualización.
        """
        try:
            division = await self.get_by_id(division_id)
            if not division:
                return None

            for key, value in kwargs.items():
                if hasattr(division, key):
                    setattr(division, key, value)

            await self.session.flush()
            await self.session.refresh(division)
            return division
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def delete(self, division_id: str) -> bool:
        """
        Elimina una división de la base de datos.

        Parameters
        ----------
        division_id : str
            Identificador único de la división a eliminar (ULID).

        Returns
        -------
        bool
            True si la división fue eliminada, False si no se encontró.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de eliminación.
        """
        try:
            query = delete(DivisionCuentaModel).where(DivisionCuentaModel.id == division_id)
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
