"""
Repositorio para la gestión de alérgenos en el sistema.
"""

from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.menu.alergeno_model import AlergenoModel


class AlergenoRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de alérgenos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los alérgenos en el sistema, siguiendo el patrón Repository.

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

    async def get_all(
        self, skip: int = 0, limit: int = 100, producto_id: Optional[str] = None
    ) -> List[AlergenoModel]:
        """
        Obtiene una lista paginada de alérgenos y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        producto_id : Optional[str], optional
            ID del producto para filtrar alérgenos asociados, por defecto None.

        Returns
        -------
        List[AlergenoModel]
            Lista de instancias de AlergenoModel.
        """
        query = select(AlergenoModel)
        if producto_id:
            from src.models.menu.producto_alergeno_model import ProductoAlergenoModel

            query = query.join(AlergenoModel.productos_alergenos).where(
                ProductoAlergenoModel.id_producto == producto_id
            )

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            alergenos = result.scalars().all()

            return list(alergenos)
        except SQLAlchemyError:
            raise
