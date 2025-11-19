"""
Repositorio para la gestión de zonas en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import joinedload

from src.models.mesas.zona_model import ZonaModel


class ZonaRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de zonas.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las zonas en el sistema, siguiendo el patrón Repository.

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

    async def create(self, zona: ZonaModel) -> ZonaModel:
        """
        Crea una nueva zona en la base de datos.

        Parameters
        ----------
        zona : ZonaModel
            Instancia del modelo de zona a crear.

        Returns
        -------
        ZonaModel
            El modelo de zona creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(zona)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(zona)
            return zona
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, zona_id: str) -> Optional[ZonaModel]:
        """
        Obtiene una zona por su identificador único con eager loading del local.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a buscar (ULID).

        Returns
        -------
        Optional[ZonaModel]
            La zona encontrada o None si no existe.
        """
        query = (
            select(ZonaModel)
            .options(joinedload(ZonaModel.local))
            .where(ZonaModel.id == zona_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_local(
        self, local_id: str, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ZonaModel], int]:
        """
        Obtiene zonas por ID de local con paginación.

        Parameters
        ----------
        local_id : str
            ID del local para filtrar zonas.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[ZonaModel], int]
            Tupla con la lista de zonas y el número total de registros.
        """
        # Consulta para obtener las zonas paginadas
        query = (
            select(ZonaModel)
            .options(joinedload(ZonaModel.local))
            .where(ZonaModel.id_local == local_id)
            .offset(skip)
            .limit(limit)
        )

        # Consulta para obtener el total de registros
        count_query = select(func.count(ZonaModel.id)).where(
            ZonaModel.id_local == local_id
        )

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            zonas = result.scalars().all()
            total = count_result.scalar() or 0

            return list(zonas), total
        except SQLAlchemyError:
            raise

    async def get_by_nivel(
        self, nivel: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ZonaModel], int]:
        """
        Obtiene zonas por nivel jerárquico con paginación.

        Parameters
        ----------
        nivel : int
            Nivel jerárquico para filtrar zonas (0, 1, 2).
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[ZonaModel], int]
            Tupla con la lista de zonas y el número total de registros.
        """
        # Consulta para obtener las zonas paginadas
        query = (
            select(ZonaModel)
            .options(joinedload(ZonaModel.local))
            .where(ZonaModel.nivel == nivel)
            .offset(skip)
            .limit(limit)
        )

        # Consulta para obtener el total de registros
        count_query = select(func.count(ZonaModel.id)).where(ZonaModel.nivel == nivel)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            zonas = result.scalars().all()
            total = count_result.scalar() or 0

            return list(zonas), total
        except SQLAlchemyError:
            raise

    async def delete(self, zona_id: str) -> bool:
        """
        Elimina una zona de la base de datos por su ID.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a eliminar (ULID).

        Returns
        -------
        bool
            True si la zona fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(ZonaModel).where(ZonaModel.id == zona_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, zona_id: str, **kwargs) -> Optional[ZonaModel]:
        """
        Actualiza una zona existente con los valores proporcionados.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a actualizar (ULID).
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[ZonaModel]
            La zona actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(ZonaModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(zona_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(ZonaModel)
                .where(ZonaModel.id == zona_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar la zona actualizada
            updated_zona = await self.get_by_id(zona_id)

            # Si no se encontró la zona, retornar None
            if not updated_zona:
                return None

            return updated_zona
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ZonaModel], int]:
        """
        Obtiene una lista paginada de zonas y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[ZonaModel], int]
            Tupla con la lista de zonas y el número total de registros.
        """
        # Consulta para obtener las zonas paginadas
        query = (
            select(ZonaModel)
            .options(joinedload(ZonaModel.local))
            .offset(skip)
            .limit(limit)
        )

        # Consulta para obtener el total de registros
        count_query = select(func.count(ZonaModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            zonas = result.scalars().all()
            total = count_result.scalar() or 0

            return list(zonas), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise
