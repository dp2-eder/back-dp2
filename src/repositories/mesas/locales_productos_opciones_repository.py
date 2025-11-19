"""
Repositorio para la gestión de relaciones Local-ProductoOpcion.
"""

from typing import Optional, List, Tuple
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_

from src.models.mesas.locales_productos_opciones_model import LocalesProductosOpcionesModel


class LocalesProductosOpcionesRepository:
    """Repositorio para gestionar operaciones CRUD de LocalesProductosOpciones.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la activación de opciones de producto por local y
    sus overrides de precio adicional.

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

    async def create(self, relacion: LocalesProductosOpcionesModel) -> LocalesProductosOpcionesModel:
        """
        Crea una nueva relación local-producto_opcion.

        Parameters
        ----------
        relacion : LocalesProductosOpcionesModel
            Instancia del modelo a crear.

        Returns
        -------
        LocalesProductosOpcionesModel
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

    async def get_by_id(self, relacion_id: str) -> Optional[LocalesProductosOpcionesModel]:
        """
        Obtiene una relación por su ID único.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        Optional[LocalesProductosOpcionesModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesProductosOpcionesModel).where(LocalesProductosOpcionesModel.id == relacion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_local_and_producto_opcion(
        self, id_local: str, id_producto_opcion: str
    ) -> Optional[LocalesProductosOpcionesModel]:
        """
        Obtiene una relación por local y producto_opcion.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.

        Returns
        -------
        Optional[LocalesProductosOpcionesModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesProductosOpcionesModel).where(
            and_(
                LocalesProductosOpcionesModel.id_local == id_local,
                LocalesProductosOpcionesModel.id_producto_opcion == id_producto_opcion
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_productos_opciones_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesProductosOpcionesModel], int]:
        """
        Obtiene todas las relaciones de opciones de producto para un local específico.

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
        Tuple[List[LocalesProductosOpcionesModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesProductosOpcionesModel).where(
            LocalesProductosOpcionesModel.id_local == id_local
        )
        count_query = select(func.count(LocalesProductosOpcionesModel.id)).where(
            LocalesProductosOpcionesModel.id_local == id_local
        )

        if activo is not None:
            query = query.where(LocalesProductosOpcionesModel.activo == activo)
            count_query = count_query.where(LocalesProductosOpcionesModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def get_locales_by_producto_opcion(
        self,
        id_producto_opcion: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesProductosOpcionesModel], int]:
        """
        Obtiene todas las relaciones de locales para una opción de producto específica.

        Parameters
        ----------
        id_producto_opcion : str
            Identificador de la opción de producto.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalesProductosOpcionesModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesProductosOpcionesModel).where(
            LocalesProductosOpcionesModel.id_producto_opcion == id_producto_opcion
        )
        count_query = select(func.count(LocalesProductosOpcionesModel.id)).where(
            LocalesProductosOpcionesModel.id_producto_opcion == id_producto_opcion
        )

        if activo is not None:
            query = query.where(LocalesProductosOpcionesModel.activo == activo)
            count_query = count_query.where(LocalesProductosOpcionesModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def update(self, relacion_id: str, **kwargs) -> Optional[LocalesProductosOpcionesModel]:
        """
        Actualiza una relación local-producto_opcion existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[LocalesProductosOpcionesModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(LocalesProductosOpcionesModel, k) and k != "id"
            }

            if not valid_fields:
                return await self.get_by_id(relacion_id)

            stmt = (
                update(LocalesProductosOpcionesModel)
                .where(LocalesProductosOpcionesModel.id == relacion_id)
                .values(**valid_fields)
                .returning(LocalesProductosOpcionesModel)
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
        Elimina una relación local-producto_opcion por su ID.

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
            stmt = delete(LocalesProductosOpcionesModel).where(
                LocalesProductosOpcionesModel.id == relacion_id
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_by_local_and_producto_opcion(
        self, id_local: str, id_producto_opcion: str
    ) -> bool:
        """
        Elimina una relación por local y producto_opcion.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.

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
            stmt = delete(LocalesProductosOpcionesModel).where(
                and_(
                    LocalesProductosOpcionesModel.id_local == id_local,
                    LocalesProductosOpcionesModel.id_producto_opcion == id_producto_opcion
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def batch_insert(
        self, relaciones: List[LocalesProductosOpcionesModel]
    ) -> List[LocalesProductosOpcionesModel]:
        """
        Crea múltiples relaciones en una sola operación.

        Parameters
        ----------
        relaciones : List[LocalesProductosOpcionesModel]
            Lista de modelos a crear.

        Returns
        -------
        List[LocalesProductosOpcionesModel]
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

    async def activate_producto_opcion_for_local(
        self,
        id_local: str,
        id_producto_opcion: str,
        precio_adicional_override: Optional[Decimal] = None
    ) -> LocalesProductosOpcionesModel:
        """
        Activa una opción de producto para un local (crea o actualiza la relación).

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.
        precio_adicional_override : Optional[Decimal], optional
            Precio adicional personalizado.

        Returns
        -------
        LocalesProductosOpcionesModel
            La relación creada o actualizada.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto_opcion(id_local, id_producto_opcion)

        if existing:
            return await self.update(
                existing.id,
                activo=True,
                precio_adicional_override=precio_adicional_override
            )
        else:
            nueva_relacion = LocalesProductosOpcionesModel(
                id_local=id_local,
                id_producto_opcion=id_producto_opcion,
                activo=True,
                precio_adicional_override=precio_adicional_override
            )
            return await self.create(nueva_relacion)

    async def deactivate_producto_opcion_for_local(
        self, id_local: str, id_producto_opcion: str
    ) -> Optional[LocalesProductosOpcionesModel]:
        """
        Desactiva una opción de producto para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.

        Returns
        -------
        Optional[LocalesProductosOpcionesModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto_opcion(id_local, id_producto_opcion)

        if existing:
            return await self.update(existing.id, activo=False)

        return None

    async def update_precio_adicional_override(
        self,
        id_local: str,
        id_producto_opcion: str,
        precio_adicional_override: Optional[Decimal]
    ) -> Optional[LocalesProductosOpcionesModel]:
        """
        Actualiza el precio adicional override para una opción en un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto_opcion : str
            Identificador de la opción de producto.
        precio_adicional_override : Optional[Decimal]
            Precio adicional personalizado (None = usar original).

        Returns
        -------
        Optional[LocalesProductosOpcionesModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto_opcion(id_local, id_producto_opcion)

        if not existing:
            return None

        return await self.update(
            existing.id,
            precio_adicional_override=precio_adicional_override
        )
