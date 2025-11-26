"""
Repositorio para la gestión de categorías en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from src.repositories.base_repository import BaseRepository
from src.models.menu.categoria_model import CategoriaModel


class CategoriaRepository(BaseRepository[CategoriaModel]):
    """Repositorio para gestionar operaciones CRUD del modelo de categorías.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las categorías en el sistema, siguiendo el patrón Repository.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        super().__init__(session, CategoriaModel)

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        activo: Optional[bool] = None
    ) -> Tuple[List[CategoriaModel], int]:
        """
        Obtiene una lista paginada de categorías y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        activo : Optional[bool], optional
            Si se especifica, filtra por estado activo/inactivo.

        Returns
        -------
        Tuple[List[CategoriaModel], int]
            Tupla con la lista de categorías y el número total de registros.
        """
        # Consulta base para obtener las categorías paginadas
        query = select(CategoriaModel)

        # Aplicar filtro de activo si se especifica
        if activo is not None:
            query = query.where(CategoriaModel.activo == activo)

        return await self._fetch_paginated(query, skip, limit)

    async def get_all_with_productos(
        self,
        skip: int = 0,
        limit: int = 100,
        activo: Optional[bool] = None
    ) -> Tuple[List[CategoriaModel], int]:
        """
        Obtiene una lista paginada de categorías con sus productos eager-loaded.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        activo : Optional[bool], optional
            Si se especifica, filtra por estado activo/inactivo.

        Returns
        -------
        Tuple[List[CategoriaModel], int]
            Tupla con la lista de categorías (con productos) y el número total de registros.
        """
        # Consulta base con eager loading de productos
        query = select(CategoriaModel).options(selectinload(CategoriaModel.productos))

        # Aplicar filtro de activo si se especifica
        if activo is not None:
            query = query.where(CategoriaModel.activo == activo)

        return await self._fetch_paginated(query, skip, limit)

    async def batch_insert(
        self, categorias: List[CategoriaModel]
    ) -> List[CategoriaModel]:
        """
        Crea múltiples categorías en una sola operación.

        Parameters
        ----------
        categorias : List[CategoriaModel]
            Lista de modelos de categorías a crear.

        Returns
        -------
        List[CategoriaModel]
            Lista de categorías creadas con sus IDs asignados.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        if not categorias:
            return []

        try:
            self.session.add_all(categorias)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(categorias)
            
            return categorias
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def batch_update(
        self, ids: List[str], activo: bool
    ) -> int:
        """
        Actualiza múltiples categorías en una sola operación.

        Parameters
        ----------
        ids : List[str]
            Lista de IDs de las categorías a actualizar.
        activo : bool
            Nuevo valor para el campo activo de las categorías.
        Returns
        -------
        List[CategoriaModel]
            Lista de categorías actualizadas.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        if not ids:
            return 0

        query = (
            update(CategoriaModel)
            .where(CategoriaModel.id.in_(ids))
            .values(activo=activo)
            .execution_options(synchronize_session="fetch")
        )

        try:
            result = await self.session.execute(query)
            await self.session.commit()
            return result.rowcount
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def exist_all_by_ids(self, ids: List[str]) -> bool:
        """
        Verifica si todas las categorías con los IDs proporcionados existen.

        Parameters
        ----------
        ids : List[str]
            Lista de IDs de las categorías a verificar.

        Returns
        -------
        bool
            True si todas las categorías existen, False en caso contrario.
        """
        if not ids:
            return True

        unique_ids = set(ids)
        query = select(func.count()).where(CategoriaModel.id.in_(unique_ids))
        result = await self.session.execute(query)
        count = result.scalar() or 0

        return count == len(unique_ids)