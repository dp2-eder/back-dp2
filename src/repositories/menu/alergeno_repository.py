"""
Repositorio para la gestión de alérgenos en el sistema.
"""

from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repositories.base_repository import BaseRepository
from src.models.menu.alergeno_model import AlergenoModel
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel

class AlergenoRepository(BaseRepository[AlergenoModel]):
    """Repositorio para gestionar operaciones CRUD del modelo de alérgenos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los alérgenos en el sistema, siguiendo el patrón Repository.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        super().__init__(session, AlergenoModel)

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[AlergenoModel], int]:
        """
        Obtiene una lista paginada de alérgenos y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[AlergenoModel], int]
            Tupla con la lista de alérgenos y el total de registros.
        """
        query = select(AlergenoModel).order_by(AlergenoModel.nombre)
        return await self._fetch_paginated(query, skip, limit)