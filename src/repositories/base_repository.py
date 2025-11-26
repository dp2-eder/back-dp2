from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Repositorio base con funcionalidades comunes para todos los repositorios.
    Implementa operaciones CRUD genéricas y utilidades de paginación.
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Inicializa el repositorio con una sesión de base de datos y el modelo.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy.
        model : Type[T]
            Clase del modelo SQLAlchemy asociado a este repositorio.
        """
        self.session = session
        self.model = model

    async def create(self, obj: T) -> T:
        """
        Crea una nueva instancia del modelo en la base de datos.

        Parameters
        ----------
        obj : T
            Instancia del modelo a crear.

        Returns
        -------
        T
            La instancia creada y refrescada.
        """
        try:
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def _fetch_paginated(
        self, query: Select, skip: int, limit: int
    ) -> Tuple[List[T], int]:
        """
        Método centralizado para ejecutar queries con paginación y conteo.
        
        Parameters
        ----------
        query : Select
            La consulta base de SQLAlchemy.
        skip : int
            Número de registros a saltar.
        limit : int
            Número máximo de registros a retornar.

        Returns
        -------
        Tuple[List[T], int]
            Una tupla conteniendo la lista de resultados y el conteo total.
        """
        try:
            count_query = select(func.count()).select_from(query.subquery())
            paginated_query = query.offset(skip).limit(limit)

            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            if total == 0:
                return [], 0

            result = await self.session.execute(paginated_query)
            items = list(result.scalars().all())

            return items, total
        except SQLAlchemyError as e:
            raise e
