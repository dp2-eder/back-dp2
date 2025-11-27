"""
Repositorio para la gestión de sesiones en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base_repository import BaseRepository
from src.models.auth.sesion_model import SesionModel
from src.core.enums.sesion_enums import EstadoSesion


class SesionRepository(BaseRepository[SesionModel]):
    """Repositorio para gestionar operaciones CRUD del modelo de sesiones.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las sesiones en el sistema, siguiendo el patrón Repository.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        super().__init__(session, SesionModel)

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
        query = (
            select(SesionModel)
            .where(SesionModel.id_local == local_id)
            .order_by(SesionModel.fecha_creacion.desc())
        )
        return await self._fetch_paginated(query, skip, limit)

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
        query = (
            select(SesionModel)
            .where(SesionModel.estado == estado)
            .order_by(SesionModel.fecha_creacion.desc())
        )
        return await self._fetch_paginated(query, skip, limit)

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
        query = select(SesionModel).order_by(SesionModel.fecha_creacion.desc())

        if estado is not None:
            query = query.where(SesionModel.estado == estado)

        return await self._fetch_paginated(query, skip, limit)

    async def get_by_local_ordered(self, local_id: str) -> List[SesionModel]:
        query = (
            select(SesionModel)
            .where(SesionModel.id_local == local_id)
            .order_by(SesionModel.orden.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
