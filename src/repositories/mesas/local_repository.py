"""
Repositorio para la gestión de locales en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.mesas.local_model import LocalModel


class LocalRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de locales.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los locales en el sistema, siguiendo el patrón Repository.

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

    async def create(self, local: LocalModel) -> LocalModel:
        """
        Crea un nuevo local en la base de datos.

        Parameters
        ----------
        local : LocalModel
            Instancia del modelo de local a crear.

        Returns
        -------
        LocalModel
            El modelo de local creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(local)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(local)
            return local
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, local_id: str) -> Optional[LocalModel]:
        """
        Obtiene un local por su identificador único.

        Parameters
        ----------
        local_id : str
            Identificador único del local a buscar (ULID).

        Returns
        -------
        Optional[LocalModel]
            El local encontrado o None si no existe.
        """
        query = select(LocalModel).where(LocalModel.id == local_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_codigo(self, codigo: str) -> Optional[LocalModel]:
        """
        Obtiene un local por su código único.

        Parameters
        ----------
        codigo : str
            Código único del local a buscar (ej: CEV-001).

        Returns
        -------
        Optional[LocalModel]
            El local encontrado o None si no existe.
        """
        query = select(LocalModel).where(LocalModel.codigo == codigo)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, local_id: str) -> bool:
        """
        Elimina un local de la base de datos por su ID.

        Parameters
        ----------
        local_id : str
            Identificador único del local a eliminar (ULID).

        Returns
        -------
        bool
            True si el local fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(LocalModel).where(LocalModel.id == local_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, local_id: str, **kwargs) -> Optional[LocalModel]:
        """
        Actualiza un local existente con los valores proporcionados.

        Parameters
        ----------
        local_id : str
            Identificador único del local a actualizar (ULID).
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[LocalModel]
            El local actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(LocalModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(local_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(LocalModel)
                .where(LocalModel.id == local_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el local actualizado
            updated_local = await self.get_by_id(local_id)

            # Si no se encontró el local, retornar None
            if not updated_local:
                return None

            return updated_local
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[LocalModel], int]:
        """
        Obtiene una lista paginada de locales y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalModel], int]
            Tupla con la lista de locales y el número total de registros.
        """
        # Consulta para obtener los locales paginados
        query = select(LocalModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(LocalModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            locales = result.scalars().all()
            total = count_result.scalar() or 0

            return list(locales), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise
