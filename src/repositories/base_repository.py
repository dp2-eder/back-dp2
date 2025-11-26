from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from src.business_logic.exceptions.base_exceptions import ValidationError
from src.models.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


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

    async def get_by_id(self, obj_id: str) -> Optional[T]:
        """
        Obtiene una instancia del modelo por su ID.

        Parameters
        ----------
        obj_id : Any
            ID de la instancia a buscar.

        Returns
        -------
        Optional[T]
            La instancia encontrada o None si no existe.
        """
        try:
            query = select(self.model).where(self.model.id == obj_id)
            result = await self.session.execute(query)
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise e

    async def update(self, obj: T) -> T:
        """
        Actualiza una instancia del modelo en la base de datos.

        Parameters
        ----------
        obj : T
            Instancia del modelo a actualizar.

        Returns
        -------
        T
            La instancia actualizada y refrescada.
        """
        try:
            await self.session.merge(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    async def delete(self, obj_id: str) -> bool:
        """
        Elimina una instancia del modelo por su ID.

        Parameters
        ----------
        obj_id : Any
            ID de la instancia a eliminar.
        """
        try:
            query = delete(self.model).where(self.model.id == obj_id)
            await self.session.execute(query)
            await self.session.flush()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise e

    def _validate_pagination(self, skip: int, limit: int) -> None:
        """Valida parámetros de paginación.

        Args:
            skip: Offset de paginación
            limit: Límite de registros

        Raises:
            AlergenoValidationError: Si los parámetros son inválidos
        """
        if skip < 0:
            raise ValidationError("El parámetro 'skip' debe ser mayor o igual a cero")
        if limit <= 0:
            raise ValidationError("El parámetro 'limit' debe ser mayor a cero")

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
            self._validate_pagination(skip, limit)
            count_query = select(func.count()).select_from(query.subquery())
            paginated_query = query.offset(skip).limit(limit)

            total_result = await self.session.execute(count_query)
            total = total_result.scalar() or 0
            if total == 0:
                return [], 0

            result = await self.session.execute(paginated_query)
            items = list(result.scalars().all())

            return items, total
        except ValidationError as ve:
            raise ve
        except SQLAlchemyError as e:
            raise e
