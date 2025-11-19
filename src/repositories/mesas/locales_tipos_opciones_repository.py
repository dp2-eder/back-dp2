"""
Repositorio para la gestión de relaciones Local-TipoOpcion.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_

from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel


class LocalesTiposOpcionesRepository:
    """Repositorio para gestionar operaciones CRUD de LocalesTiposOpciones.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la activación de tipos de opciones por local.

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

    async def create(self, relacion: LocalesTiposOpcionesModel) -> LocalesTiposOpcionesModel:
        """
        Crea una nueva relación local-tipo_opcion.

        Parameters
        ----------
        relacion : LocalesTiposOpcionesModel
            Instancia del modelo a crear.

        Returns
        -------
        LocalesTiposOpcionesModel
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

    async def get_by_id(self, relacion_id: str) -> Optional[LocalesTiposOpcionesModel]:
        """
        Obtiene una relación por su ID único.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        Optional[LocalesTiposOpcionesModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesTiposOpcionesModel).where(LocalesTiposOpcionesModel.id == relacion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_local_and_tipo_opcion(
        self, id_local: str, id_tipo_opcion: str
    ) -> Optional[LocalesTiposOpcionesModel]:
        """
        Obtiene una relación por local y tipo de opción.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_tipo_opcion : str
            Identificador del tipo de opción.

        Returns
        -------
        Optional[LocalesTiposOpcionesModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesTiposOpcionesModel).where(
            and_(
                LocalesTiposOpcionesModel.id_local == id_local,
                LocalesTiposOpcionesModel.id_tipo_opcion == id_tipo_opcion
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_tipos_opciones_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesTiposOpcionesModel], int]:
        """
        Obtiene todas las relaciones de tipos de opciones para un local específico.

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
        Tuple[List[LocalesTiposOpcionesModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesTiposOpcionesModel).where(LocalesTiposOpcionesModel.id_local == id_local)
        count_query = select(func.count(LocalesTiposOpcionesModel.id)).where(
            LocalesTiposOpcionesModel.id_local == id_local
        )

        if activo is not None:
            query = query.where(LocalesTiposOpcionesModel.activo == activo)
            count_query = count_query.where(LocalesTiposOpcionesModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def get_locales_by_tipo_opcion(
        self,
        id_tipo_opcion: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesTiposOpcionesModel], int]:
        """
        Obtiene todas las relaciones de locales para un tipo de opción específico.

        Parameters
        ----------
        id_tipo_opcion : str
            Identificador del tipo de opción.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalesTiposOpcionesModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesTiposOpcionesModel).where(
            LocalesTiposOpcionesModel.id_tipo_opcion == id_tipo_opcion
        )
        count_query = select(func.count(LocalesTiposOpcionesModel.id)).where(
            LocalesTiposOpcionesModel.id_tipo_opcion == id_tipo_opcion
        )

        if activo is not None:
            query = query.where(LocalesTiposOpcionesModel.activo == activo)
            count_query = count_query.where(LocalesTiposOpcionesModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def update(self, relacion_id: str, **kwargs) -> Optional[LocalesTiposOpcionesModel]:
        """
        Actualiza una relación local-tipo_opcion existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[LocalesTiposOpcionesModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(LocalesTiposOpcionesModel, k) and k != "id"
            }

            if not valid_fields:
                return await self.get_by_id(relacion_id)

            stmt = (
                update(LocalesTiposOpcionesModel)
                .where(LocalesTiposOpcionesModel.id == relacion_id)
                .values(**valid_fields)
                .returning(LocalesTiposOpcionesModel)
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
        Elimina una relación local-tipo_opcion por su ID.

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
            stmt = delete(LocalesTiposOpcionesModel).where(LocalesTiposOpcionesModel.id == relacion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_by_local_and_tipo_opcion(
        self, id_local: str, id_tipo_opcion: str
    ) -> bool:
        """
        Elimina una relación por local y tipo de opción.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_tipo_opcion : str
            Identificador del tipo de opción.

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
            stmt = delete(LocalesTiposOpcionesModel).where(
                and_(
                    LocalesTiposOpcionesModel.id_local == id_local,
                    LocalesTiposOpcionesModel.id_tipo_opcion == id_tipo_opcion
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def batch_insert(
        self, relaciones: List[LocalesTiposOpcionesModel]
    ) -> List[LocalesTiposOpcionesModel]:
        """
        Crea múltiples relaciones en una sola operación.

        Parameters
        ----------
        relaciones : List[LocalesTiposOpcionesModel]
            Lista de modelos a crear.

        Returns
        -------
        List[LocalesTiposOpcionesModel]
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

    async def activate_tipo_opcion_for_local(
        self, id_local: str, id_tipo_opcion: str
    ) -> LocalesTiposOpcionesModel:
        """
        Activa un tipo de opción para un local (crea o actualiza la relación).

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_tipo_opcion : str
            Identificador del tipo de opción.

        Returns
        -------
        LocalesTiposOpcionesModel
            La relación creada o actualizada.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_tipo_opcion(id_local, id_tipo_opcion)

        if existing:
            return await self.update(existing.id, activo=True)
        else:
            nueva_relacion = LocalesTiposOpcionesModel(
                id_local=id_local,
                id_tipo_opcion=id_tipo_opcion,
                activo=True
            )
            return await self.create(nueva_relacion)

    async def deactivate_tipo_opcion_for_local(
        self, id_local: str, id_tipo_opcion: str
    ) -> Optional[LocalesTiposOpcionesModel]:
        """
        Desactiva un tipo de opción para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_tipo_opcion : str
            Identificador del tipo de opción.

        Returns
        -------
        Optional[LocalesTiposOpcionesModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_tipo_opcion(id_local, id_tipo_opcion)

        if existing:
            return await self.update(existing.id, activo=False)

        return None
