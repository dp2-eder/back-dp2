"""
Repositorio para la gestión de relaciones Local-Producto.
"""

from typing import Optional, List, Tuple
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_

from src.models.mesas.locales_productos_model import LocalesProductosModel


class LocalesProductosRepository:
    """Repositorio para gestionar operaciones CRUD de LocalesProductos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la activación de productos por local y sus overrides.

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

    async def create(self, relacion: LocalesProductosModel) -> LocalesProductosModel:
        """
        Crea una nueva relación local-producto.

        Parameters
        ----------
        relacion : LocalesProductosModel
            Instancia del modelo a crear.

        Returns
        -------
        LocalesProductosModel
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

    async def get_by_id(self, relacion_id: str) -> Optional[LocalesProductosModel]:
        """
        Obtiene una relación por su ID único.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        Optional[LocalesProductosModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesProductosModel).where(LocalesProductosModel.id == relacion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_local_and_producto(
        self, id_local: str, id_producto: str
    ) -> Optional[LocalesProductosModel]:
        """
        Obtiene una relación por local y producto.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.

        Returns
        -------
        Optional[LocalesProductosModel]
            La relación encontrada o None si no existe.
        """
        query = select(LocalesProductosModel).where(
            and_(
                LocalesProductosModel.id_local == id_local,
                LocalesProductosModel.id_producto == id_producto
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_productos_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesProductosModel], int]:
        """
        Obtiene todas las relaciones de productos para un local específico.

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
        Tuple[List[LocalesProductosModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesProductosModel).where(LocalesProductosModel.id_local == id_local)
        count_query = select(func.count(LocalesProductosModel.id)).where(
            LocalesProductosModel.id_local == id_local
        )

        if activo is not None:
            query = query.where(LocalesProductosModel.activo == activo)
            count_query = count_query.where(LocalesProductosModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def get_locales_by_producto(
        self,
        id_producto: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[LocalesProductosModel], int]:
        """
        Obtiene todas las relaciones de locales para un producto específico.

        Parameters
        ----------
        id_producto : str
            Identificador del producto.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[LocalesProductosModel], int]
            Tupla con la lista de relaciones y el total de registros.
        """
        query = select(LocalesProductosModel).where(
            LocalesProductosModel.id_producto == id_producto
        )
        count_query = select(func.count(LocalesProductosModel.id)).where(
            LocalesProductosModel.id_producto == id_producto
        )

        if activo is not None:
            query = query.where(LocalesProductosModel.activo == activo)
            count_query = count_query.where(LocalesProductosModel.activo == activo)

        query = query.offset(skip).limit(limit)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            relaciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(relaciones), total
        except SQLAlchemyError:
            raise

    async def update(self, relacion_id: str, **kwargs) -> Optional[LocalesProductosModel]:
        """
        Actualiza una relación local-producto existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[LocalesProductosModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        try:
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(LocalesProductosModel, k) and k != "id"
            }

            if not valid_fields:
                return await self.get_by_id(relacion_id)

            stmt = (
                update(LocalesProductosModel)
                .where(LocalesProductosModel.id == relacion_id)
                .values(**valid_fields)
                .returning(LocalesProductosModel)
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
        Elimina una relación local-producto por su ID.

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
            stmt = delete(LocalesProductosModel).where(LocalesProductosModel.id == relacion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_by_local_and_producto(
        self, id_local: str, id_producto: str
    ) -> bool:
        """
        Elimina una relación por local y producto.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.

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
            stmt = delete(LocalesProductosModel).where(
                and_(
                    LocalesProductosModel.id_local == id_local,
                    LocalesProductosModel.id_producto == id_producto
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def batch_insert(
        self, relaciones: List[LocalesProductosModel]
    ) -> List[LocalesProductosModel]:
        """
        Crea múltiples relaciones en una sola operación.

        Parameters
        ----------
        relaciones : List[LocalesProductosModel]
            Lista de modelos a crear.

        Returns
        -------
        List[LocalesProductosModel]
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

    async def activate_producto_for_local(
        self,
        id_local: str,
        id_producto: str,
        precio_override: Optional[Decimal] = None,
        disponible_override: Optional[bool] = None,
        nombre_override: Optional[str] = None,
        descripcion_override: Optional[str] = None
    ) -> LocalesProductosModel:
        """
        Activa un producto para un local (crea o actualiza la relación con overrides).

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.
        precio_override : Optional[Decimal], optional
            Precio personalizado.
        disponible_override : Optional[bool], optional
            Disponibilidad personalizada.
        nombre_override : Optional[str], optional
            Nombre personalizado.
        descripcion_override : Optional[str], optional
            Descripción personalizada.

        Returns
        -------
        LocalesProductosModel
            La relación creada o actualizada.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto(id_local, id_producto)

        if existing:
            return await self.update(
                existing.id,
                activo=True,
                precio_override=precio_override,
                disponible_override=disponible_override,
                nombre_override=nombre_override,
                descripcion_override=descripcion_override
            )
        else:
            nueva_relacion = LocalesProductosModel(
                id_local=id_local,
                id_producto=id_producto,
                activo=True,
                precio_override=precio_override,
                disponible_override=disponible_override,
                nombre_override=nombre_override,
                descripcion_override=descripcion_override
            )
            return await self.create(nueva_relacion)

    async def deactivate_producto_for_local(
        self, id_local: str, id_producto: str
    ) -> Optional[LocalesProductosModel]:
        """
        Desactiva un producto para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.

        Returns
        -------
        Optional[LocalesProductosModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto(id_local, id_producto)

        if existing:
            return await self.update(existing.id, activo=False)

        return None

    async def update_overrides(
        self,
        id_local: str,
        id_producto: str,
        precio_override: Optional[Decimal] = None,
        disponible_override: Optional[bool] = None,
        nombre_override: Optional[str] = None,
        descripcion_override: Optional[str] = None
    ) -> Optional[LocalesProductosModel]:
        """
        Actualiza los valores de override para un producto en un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_producto : str
            Identificador del producto.
        precio_override : Optional[Decimal], optional
            Precio personalizado (None = usar original).
        disponible_override : Optional[bool], optional
            Disponibilidad personalizada (None = usar original).
        nombre_override : Optional[str], optional
            Nombre personalizado (None = usar original).
        descripcion_override : Optional[str], optional
            Descripción personalizada (None = usar original).

        Returns
        -------
        Optional[LocalesProductosModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación.
        """
        existing = await self.get_by_local_and_producto(id_local, id_producto)

        if not existing:
            return None

        return await self.update(
            existing.id,
            precio_override=precio_override,
            disponible_override=disponible_override,
            nombre_override=nombre_override,
            descripcion_override=descripcion_override
        )
