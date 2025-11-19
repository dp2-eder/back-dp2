"""
Repositorio para la gestión de relaciones Local-Categoría.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_

from src.models.mesas.locales_categorias_model import LocalesCategoriasModel


class LocalesCategoriasRepository:
    """Repositorio para gestionar operaciones CRUD de LocalesCategorias.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la activación de categorías por local.

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
            Sesión asíncrona de SQLAlchemy.
        """
        self.session = session

    async def create(self, relacion: LocalesCategoriasModel) -> LocalesCategoriasModel:
        """
        Crea una nueva relación local-categoría.

        Parameters
        ----------
        relacion : LocalesCategoriasModel
            Instancia del modelo a crear.

        Returns
        -------
        LocalesCategoriasModel
            El modelo creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            self.session.add(relacion)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(relacion)
            return relacion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, relacion_id: str) -> Optional[LocalesCategoriasModel]:
        """
        Obtiene una relación por su ID único.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        Optional[LocalesCategoriasModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesCategoriasModel).where(LocalesCategoriasModel.id == relacion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_local_and_categoria(
        self, id_local: str, id_categoria: str
    ) -> Optional[LocalesCategoriasModel]:
        """
        Obtiene una relación por local y categoría.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_categoria : str
            Identificador de la categoría.

        Returns
        -------
        Optional[LocalesCategoriasModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesCategoriasModel).where(
            and_(
                LocalesCategoriasModel.id_local == id_local,
                LocalesCategoriasModel.id_categoria == id_categoria
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_categorias_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesCategoriasModel], int]:
        """
        Obtiene todas las relaciones de categorías para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalesCategoriasModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesCategoriasModel).where(LocalesCategoriasModel.id_local == id_local)
        count_query = select(func.count(LocalesCategoriasModel.id)).where(
            LocalesCategoriasModel.id_local == id_local
        )

        if activo is not None:
            query = query.where(LocalesCategoriasModel.activo == activo)
            count_query = count_query.where(LocalesCategoriasModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def get_locales_by_categoria(
        self,
        id_categoria: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesCategoriasModel], int]:
        """
        Obtiene todas las relaciones de locales para una categoría específica.

        Parameters
        ----------
        id_categoria : str
            Identificador de la categoría.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalesCategoriasModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesCategoriasModel).where(
            LocalesCategoriasModel.id_categoria == id_categoria
        )
        count_query = select(func.count(LocalesCategoriasModel.id)).where(
            LocalesCategoriasModel.id_categoria == id_categoria
        )

        if activo is not None:
            query = query.where(LocalesCategoriasModel.activo == activo)
            count_query = count_query.where(LocalesCategoriasModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def update(self, relacion_id: str, **kwargs) -> Optional[LocalesCategoriasModel]:
        """
        Actualiza una relación local-categoría existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[LocalesCategoriasModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(LocalesCategoriasModel, k) and k != "id"
            }

            if not valid_fields:
                return await self.get_by_id(relacion_id)

            stmt = (
                update(LocalesCategoriasModel)
                .where(LocalesCategoriasModel.id == relacion_id)
                .values(**valid_fields)
                .returning(LocalesCategoriasModel)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            updated_relacion = result.scalars().first()

            if not updated_relacion:
                return None

            await self.session.refresh(updated_relacion)

            return updated_relacion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete(self, relacion_id: str) -> bool:
        """
        Elimina una relación local-categoría por su ID.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        bool
            True si fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            stmt = delete(LocalesCategoriasModel).where(LocalesCategoriasModel.id == relacion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_by_local_and_categoria(
        self, id_local: str, id_categoria: str
    ) -> bool:
        """
        Elimina una relación por local y categoría.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_categoria : str
            Identificador de la categoría.

        Returns
        -------
        bool
            True si fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            stmt = delete(LocalesCategoriasModel).where(
                and_(
                    LocalesCategoriasModel.id_local == id_local,
                    LocalesCategoriasModel.id_categoria == id_categoria
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def batch_insert(
        self, relaciones: List[LocalesCategoriasModel]
    ) -> List[LocalesCategoriasModel]:
        """
        Crea múltiples relaciones en una sola operación.

        Parameters
        ----------
        relaciones : List[LocalesCategoriasModel]
            Lista de modelos a crear.

        Returns
        -------
        List[LocalesCategoriasModel]
            Lista de relaciones creadas con sus IDs asignados.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        if not relaciones:
            return []

        try:
            self.session.add_all(relaciones)
            await self.session.flush()
            await self.session.commit()

            for relacion in relaciones:
                await self.session.refresh(relacion)

            return relaciones
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def activate_categoria_for_local(
        self, id_local: str, id_categoria: str, orden_override: Optional[int] = None
    ) -> LocalesCategoriasModel:
        """
        Activa una categoría para un local (crea o actualiza la relación).

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_categoria : str
            Identificador de la categoría.
        orden_override : Optional[int], optional
            Orden personalizado para este local.

        Returns
        -------
        LocalesCategoriasModel
            La relación creada o actualizada.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_categoria(id_local, id_categoria)

        if existing:
            return await self.update(
                existing.id,
                activo=True,
                orden_override=orden_override
            )
        else:
            nueva_relacion = LocalesCategoriasModel(
                id_local=id_local,
                id_categoria=id_categoria,
                activo=True,
                orden_override=orden_override
            )
            return await self.create(nueva_relacion)

    async def deactivate_categoria_for_local(
        self, id_local: str, id_categoria: str
    ) -> Optional[LocalesCategoriasModel]:
        """
        Desactiva una categoría para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_categoria : str
            Identificador de la categoría.

        Returns
        -------
        Optional[LocalesCategoriasModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_categoria(id_local, id_categoria)

        if existing:
            return await self.update(existing.id, activo=False)

        return None
