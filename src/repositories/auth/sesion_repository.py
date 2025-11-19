"""
Repositorio para la gestión de sesiones en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.auth.sesion_model import SesionModel
from src.core.enums.sesion_enums import EstadoSesion


class SesionRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de sesiones.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las sesiones en el sistema, siguiendo el patrón Repository.

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

    async def create(self, sesion: SesionModel) -> SesionModel:
        """
        Crea una nueva sesión en la base de datos.

        Parameters
        ----------
        sesion : SesionModel
            Instancia del modelo de sesión a crear.

        Returns
        -------
        SesionModel
            El modelo de sesión creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de creación.
        """
        try:
            self.session.add(sesion)
            await self.session.flush()
            await self.session.refresh(sesion)
            return sesion
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, sesion_id: str) -> Optional[SesionModel]:
        """
        Obtiene una sesión por su ID.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión (ULID).

        Returns
        -------
        Optional[SesionModel]
            El modelo de sesión si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            query = select(SesionModel).where(SesionModel.id == sesion_id)
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise e

    async def get_by_local(
        self, local_id: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[SesionModel], int]:
        """
        Obtiene sesiones filtradas por local con paginación.

        Parameters
        ----------
        local_id : str
            ID del local para filtrar sesiones.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[SesionModel], int]
            Tupla con la lista de sesiones y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            # Construir query con filtro de local
            query = (
                select(SesionModel)
                .where(SesionModel.id_local == local_id)
                .order_by(SesionModel.fecha_creacion.desc())
                .offset(skip)
                .limit(limit)
            )

            # Obtener total de registros con el mismo filtro
            count_query = select(func.count(SesionModel.id)).where(
                SesionModel.id_local == local_id
            )

            result = await self.session.execute(query)
            sesiones = list(result.scalars().all())

            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0

            return sesiones, total
        except SQLAlchemyError as e:
            raise e

    async def get_by_estado(
        self, estado: EstadoSesion, skip: int = 0, limit: int = 100
    ) -> Tuple[List[SesionModel], int]:
        """
        Obtiene sesiones filtradas por estado con paginación.

        Parameters
        ----------
        estado : EstadoSesion
            Estado para filtrar sesiones.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[SesionModel], int]
            Tupla con la lista de sesiones y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            # Construir query con filtro de estado
            query = (
                select(SesionModel)
                .where(SesionModel.estado == estado)
                .order_by(SesionModel.fecha_creacion.desc())
                .offset(skip)
                .limit(limit)
            )

            # Obtener total de registros con el mismo filtro
            count_query = select(func.count(SesionModel.id)).where(
                SesionModel.estado == estado
            )

            result = await self.session.execute(query)
            sesiones = list(result.scalars().all())

            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0

            return sesiones, total
        except SQLAlchemyError as e:
            raise e

    async def get_all(
        self, skip: int = 0, limit: int = 100, estado: Optional[EstadoSesion] = None
    ) -> Tuple[List[SesionModel], int]:
        """
        Obtiene todas las sesiones con paginación y filtro opcional por estado.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        estado : Optional[EstadoSesion], optional
            Estado para filtrar sesiones, por defecto None (sin filtro).

        Returns
        -------
        Tuple[List[SesionModel], int]
            Tupla con la lista de sesiones y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la consulta.
        """
        try:
            # Construir query con paginación
            query = select(SesionModel)
            
            # Aplicar filtro de estado si se proporciona
            if estado is not None:
                query = query.where(SesionModel.estado == estado)
            
            query = query.order_by(SesionModel.fecha_creacion.desc()).offset(skip).limit(limit)

            # Obtener total de registros con el mismo filtro
            count_query = select(func.count(SesionModel.id))
            if estado is not None:
                count_query = count_query.where(SesionModel.estado == estado)

            result = await self.session.execute(query)
            sesiones = list(result.scalars().all())

            count_result = await self.session.execute(count_query)
            total = count_result.scalar() or 0

            return sesiones, total
        except SQLAlchemyError as e:
            raise e

    async def update(self, sesion_id: str, **kwargs) -> Optional[SesionModel]:
        """
        Actualiza una sesión existente.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión a actualizar (ULID).
        **kwargs
            Campos a actualizar con sus nuevos valores.

        Returns
        -------
        Optional[SesionModel]
            El modelo de sesión actualizado si se encuentra, None en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de actualización.
        """
        try:
            # Buscar la sesión
            sesion = await self.get_by_id(sesion_id)
            if not sesion:
                return None

            # Actualizar los campos proporcionados
            for key, value in kwargs.items():
                if hasattr(sesion, key):
                    setattr(sesion, key, value)

            await self.session.flush()
            await self.session.refresh(sesion)
            return sesion
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def delete(self, sesion_id: str) -> bool:
        """
        Elimina una sesión de la base de datos.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión a eliminar (ULID).

        Returns
        -------
        bool
            True si la sesión fue eliminada, False si no se encontró.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación de eliminación.
        """
        try:
            query = delete(SesionModel).where(SesionModel.id == sesion_id)
            result = await self.session.execute(query)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def get_by_local_ordered(self, local_id: str) -> List[SesionModel]:
        query = (
            select(SesionModel)
            .where(SesionModel.id_local == local_id)
            .order_by(SesionModel.orden.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())