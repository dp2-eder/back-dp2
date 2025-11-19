"""
Repositorio para la gestión de detalles de división de cuenta en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel


class DivisionCuentaDetalleRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de detalles de división.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los detalles de división de cuenta en el sistema.

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

    async def create(self, detalle: DivisionCuentaDetalleModel) -> DivisionCuentaDetalleModel:
        """
        Crea un nuevo detalle de división en la base de datos.

        Parameters
        ----------
        detalle : DivisionCuentaDetalleModel
            Instancia del modelo de detalle a crear.

        Returns
        -------
        DivisionCuentaDetalleModel
            El modelo de detalle creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de creación.
        """
        try:
            self.session.add(detalle)
            await self.session.flush()
            await self.session.refresh(detalle)
            return detalle
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, detalle_id: str) -> Optional[DivisionCuentaDetalleModel]:
        """
        Obtiene un detalle por su ID.

        Parameters
        ----------
        detalle_id : str
            Identificador único del detalle (ULID).

        Returns
        -------
        Optional[DivisionCuentaDetalleModel]
            El modelo de detalle si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = select(DivisionCuentaDetalleModel).where(DivisionCuentaDetalleModel.id == detalle_id)
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise e

    async def get_by_division(self, division_id: str) -> List[DivisionCuentaDetalleModel]:
        """
        Obtiene detalles por división de cuenta.

        Parameters
        ----------
        division_id : str
            ID de la división para filtrar detalles.

        Returns
        -------
        List[DivisionCuentaDetalleModel]
            Lista de detalles de la división.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaDetalleModel)
                .where(DivisionCuentaDetalleModel.id_division_cuenta == division_id)
                .order_by(DivisionCuentaDetalleModel.persona_numero)
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise e

    async def get_by_persona(
        self, division_id: str, persona_numero: int
    ) -> List[DivisionCuentaDetalleModel]:
        """
        Obtiene items asignados a una persona específica.

        Parameters
        ----------
        division_id : str
            ID de la división de cuenta.
        persona_numero : int
            Número identificador de la persona.

        Returns
        -------
        List[DivisionCuentaDetalleModel]
            Lista de items asignados a esa persona.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaDetalleModel)
                .where(
                    DivisionCuentaDetalleModel.id_division_cuenta == division_id,
                    DivisionCuentaDetalleModel.persona_numero == persona_numero
                )
            )
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise e

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[DivisionCuentaDetalleModel], int]:
        """
        Obtiene todos los detalles con paginación.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[DivisionCuentaDetalleModel], int]
            Tupla con la lista de detalles y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = (
                select(DivisionCuentaDetalleModel)
                .order_by(DivisionCuentaDetalleModel.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            count_query = select(func.count(DivisionCuentaDetalleModel.id))

            result = await self.session.execute(query)
            detalles = list(result.scalars().all())

            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0

            return detalles, total
        except SQLAlchemyError as e:
            raise e

    async def update(self, detalle_id: str, **kwargs) -> Optional[DivisionCuentaDetalleModel]:
        """
        Actualiza un detalle existente.

        Parameters
        ----------
        detalle_id : str
            Identificador único del detalle a actualizar (ULID).
        **kwargs
            Campos a actualizar con sus nuevos valores.

        Returns
        -------
        Optional[DivisionCuentaDetalleModel]
            El modelo de detalle actualizado si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de actualización.
        """
        try:
            detalle = await self.get_by_id(detalle_id)
            if not detalle:
                return None

            for key, value in kwargs.items():
                if hasattr(detalle, key):
                    setattr(detalle, key, value)

            await self.session.flush()
            await self.session.refresh(detalle)
            return detalle
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def delete(self, detalle_id: str) -> bool:
        """
        Elimina un detalle de la base de datos.

        Parameters
        ----------
        detalle_id : str
            Identificador único del detalle a eliminar (ULID).

        Returns
        -------
        bool
            True si el detalle fue eliminado, False si no se encontró.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de eliminación.
        """
        try:
            query = delete(DivisionCuentaDetalleModel).where(DivisionCuentaDetalleModel.id == detalle_id)
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e
