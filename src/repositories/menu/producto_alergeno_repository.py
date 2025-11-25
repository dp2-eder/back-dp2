"""
Repositorio para la gestión de relaciones producto-alérgeno en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete, update, func

from src.models.menu.producto_alergeno_model import ProductoAlergenoModel


class ProductoAlergenoRepository:
    """Repositorio para gestionar operaciones CRUD de relaciones producto-alérgeno.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la asignación de alérgenos a productos del menú,
    siguiendo el patrón Repository.

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

    async def create(self, producto_alergeno: ProductoAlergenoModel) -> ProductoAlergenoModel:
        """
        Crea una nueva relación producto-alérgeno en la base de datos.

        Parameters
        ----------
        producto_alergeno : ProductoAlergenoModel
            Instancia del modelo de relación a crear.

        Returns
        -------
        ProductoAlergenoModel
            El modelo de relación creado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(producto_alergeno)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(producto_alergeno)
            return producto_alergeno
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, id: str) -> Optional[ProductoAlergenoModel]:
        """
        Obtiene una relación producto-alérgeno por su ID con relaciones cargadas.

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación encontrada con producto y alérgeno cargados, o None si no existe.
        """
        query = (
            select(ProductoAlergenoModel)
            .where(ProductoAlergenoModel.id == id)
            .options(
                selectinload(ProductoAlergenoModel.producto),
                selectinload(ProductoAlergenoModel.alergeno)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_producto_alergeno(
        self, id_producto: str, id_alergeno: str
    ) -> Optional[ProductoAlergenoModel]:
        """
        Obtiene una relación por combinación producto-alérgeno con relaciones cargadas.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        id_alergeno : str
            Identificador único del alérgeno.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación encontrada con producto y alérgeno cargados, o None si no existe.
        """
        query = (
            select(ProductoAlergenoModel)
            .where(
                ProductoAlergenoModel.id_producto == id_producto,
                ProductoAlergenoModel.id_alergeno == id_alergeno
            )
            .options(
                selectinload(ProductoAlergenoModel.producto),
                selectinload(ProductoAlergenoModel.alergeno)
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, id: str) -> bool:
        """
        Elimina una relación producto-alérgeno de la base de datos por su ID.

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.

        Returns
        -------
        bool
            True si la relación fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(ProductoAlergenoModel).where(
                ProductoAlergenoModel.id == id
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def delete_by_producto(self, id_producto: str) -> int:
        """
        Elimina todas las relaciones de alérgenos de un producto.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.

        Returns
        -------
        int
            Número de relaciones eliminadas.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(ProductoAlergenoModel).where(
                ProductoAlergenoModel.id_producto == id_producto
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, id: str, **kwargs) -> Optional[ProductoAlergenoModel]:
        """
        Actualiza una relación producto-alérgeno existente por su ID.

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.
        **kwargs
            Campos y valores a actualizar (nivel_presencia, notas, activo).

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación actualizada con relaciones cargadas, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos editables
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(ProductoAlergenoModel, k) and k not in ("id", "id_producto", "id_alergeno")
            }

            if not valid_fields:
                return await self.get_by_id(id)

            stmt = (
                update(ProductoAlergenoModel)
                .where(ProductoAlergenoModel.id == id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            if result.rowcount == 0:
                return None

            return await self.get_by_id(id)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ProductoAlergenoModel], int]:
        """
        Obtiene una lista paginada de relaciones producto-alérgeno con relaciones cargadas.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[ProductoAlergenoModel], int]
            Tupla con la lista de relaciones y el número total de registros.
        """
        query = (
            select(ProductoAlergenoModel)
            .options(
                selectinload(ProductoAlergenoModel.producto),
                selectinload(ProductoAlergenoModel.alergeno)
            )
            .offset(skip)
            .limit(limit)
        )

        count_query = select(func.count()).select_from(ProductoAlergenoModel)

        try:
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            producto_alergenos = result.scalars().all()
            total = count_result.scalar() or 0

            return list(producto_alergenos), total
        except SQLAlchemyError:
            raise

    async def get_by_producto(
        self,
        id_producto: str,
        solo_activos: bool = True
    ) -> List[ProductoAlergenoModel]:
        """
        Obtiene todas las relaciones producto-alérgeno de un producto con alérgenos cargados.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        solo_activos : bool, optional
            Si True, solo retorna relaciones activas. Por defecto True.

        Returns
        -------
        List[ProductoAlergenoModel]
            Lista de relaciones producto-alérgeno con alérgenos cargados.
        """
        query = (
            select(ProductoAlergenoModel)
            .where(ProductoAlergenoModel.id_producto == id_producto)
            .options(selectinload(ProductoAlergenoModel.alergeno))
        )

        if solo_activos:
            query = query.where(ProductoAlergenoModel.activo == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_alergeno(
        self,
        id_alergeno: str,
        solo_activos: bool = True
    ) -> List[ProductoAlergenoModel]:
        """
        Obtiene todas las relaciones de productos que contienen un alérgeno específico.

        Parameters
        ----------
        id_alergeno : str
            Identificador único del alérgeno.
        solo_activos : bool, optional
            Si True, solo retorna relaciones activas. Por defecto True.

        Returns
        -------
        List[ProductoAlergenoModel]
            Lista de relaciones producto-alérgeno con productos cargados.
        """
        query = (
            select(ProductoAlergenoModel)
            .where(ProductoAlergenoModel.id_alergeno == id_alergeno)
            .options(selectinload(ProductoAlergenoModel.producto))
        )

        if solo_activos:
            query = query.where(ProductoAlergenoModel.activo == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def batch_create(
        self,
        relaciones: List[ProductoAlergenoModel]
    ) -> List[ProductoAlergenoModel]:
        """
        Crea múltiples relaciones producto-alérgeno en una sola operación batch.

        Parameters
        ----------
        relaciones : List[ProductoAlergenoModel]
            Lista de relaciones producto-alérgeno a crear.

        Returns
        -------
        List[ProductoAlergenoModel]
            Lista de relaciones creadas con sus IDs generados.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación (ej: violación de unique constraint).
        """
        if not relaciones:
            return []

        try:
            self.session.add_all(relaciones)
            await self.session.flush()
            await self.session.commit()
            
            # Refrescar para obtener IDs y relaciones
            for relacion in relaciones:
                await self.session.refresh(relacion)
            
            return relaciones
        except SQLAlchemyError:
            await self.session.rollback()
            raise