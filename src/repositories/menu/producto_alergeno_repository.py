"""
Repositorio para la gestión de relaciones producto-alérgeno en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
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
        Obtiene una relación producto-alérgeno por su ID simple (ULID).

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación encontrada o None si no existe.
        """
        query = select(ProductoAlergenoModel).where(
            ProductoAlergenoModel.id == id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_producto_alergeno(
        self, id_producto: str, id_alergeno: str
    ) -> Optional[ProductoAlergenoModel]:
        """
        Obtiene una relación producto-alérgeno por su combinación (backward compatibility).

        LEGACY METHOD: Usar get_by_id() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        id_alergeno : str
            Identificador único del alérgeno.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación encontrada o None si no existe.
        """
        query = select(ProductoAlergenoModel).where(
            ProductoAlergenoModel.id_producto == id_producto,
            ProductoAlergenoModel.id_alergeno == id_alergeno
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

    async def delete_by_producto_alergeno(
        self, id_producto: str, id_alergeno: str
    ) -> bool:
        """
        Elimina una relación por combinación producto-alérgeno (backward compatibility).

        LEGACY METHOD: Usar delete() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        id_alergeno : str
            Identificador único del alérgeno.

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
                ProductoAlergenoModel.id_producto == id_producto,
                ProductoAlergenoModel.id_alergeno == id_alergeno
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
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
            Campos y valores a actualizar.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            # Excluir las claves primarias (id, id_producto, id_alergeno)
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(ProductoAlergenoModel, k) and k not in ("id", "id_producto", "id_alergeno")
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(ProductoAlergenoModel)
                .where(ProductoAlergenoModel.id == id)
                .values(**valid_fields)
                .returning(ProductoAlergenoModel)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Obtener el resultado actualizado
            updated_producto_alergeno = result.scalars().first()

            # Si no se encontró la relación, retornar None
            if not updated_producto_alergeno:
                return None

            # Refrescar el objeto desde la base de datos
            await self.session.refresh(updated_producto_alergeno)

            return updated_producto_alergeno
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update_by_producto_alergeno(
        self, id_producto: str, id_alergeno: str, **kwargs
    ) -> Optional[ProductoAlergenoModel]:
        """
        Actualiza una relación por combinación producto-alérgeno (backward compatibility).

        LEGACY METHOD: Usar update() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        id_alergeno : str
            Identificador único del alérgeno.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[ProductoAlergenoModel]
            La relación actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            # Excluir las claves primarias
            valid_fields = {
                k: v for k, v in kwargs.items()
                if hasattr(ProductoAlergenoModel, k) and k not in ("id", "id_producto", "id_alergeno")
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_producto_alergeno(id_producto, id_alergeno)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(ProductoAlergenoModel)
                .where(
                    ProductoAlergenoModel.id_producto == id_producto,
                    ProductoAlergenoModel.id_alergeno == id_alergeno
                )
                .values(**valid_fields)
                .returning(ProductoAlergenoModel)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Obtener el resultado actualizado
            updated_producto_alergeno = result.scalars().first()

            # Si no se encontró la relación, retornar None
            if not updated_producto_alergeno:
                return None

            # Refrescar el objeto desde la base de datos
            await self.session.refresh(updated_producto_alergeno)

            return updated_producto_alergeno
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ProductoAlergenoModel], int]:
        """
        Obtiene una lista paginada de relaciones producto-alérgeno y el total de registros.

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
        # Consulta para obtener las relaciones paginadas
        query = select(ProductoAlergenoModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count()).select_from(ProductoAlergenoModel)

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            producto_alergenos = result.scalars().all()
            total = count_result.scalar() or 0

            return list(producto_alergenos), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def get_by_producto(
        self,
        id_producto: str,
        solo_activos: bool = True
    ) -> List[ProductoAlergenoModel]:
        """
        Obtiene todos los alérgenos asociados a un producto específico.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto.
        solo_activos : bool, optional
            Si True, solo retorna relaciones activas. Por defecto True.

        Returns
        -------
        List[ProductoAlergenoModel]
            Lista de relaciones producto-alérgeno para el producto especificado.
        """
        query = select(ProductoAlergenoModel).where(
            ProductoAlergenoModel.id_producto == id_producto
        )

        if solo_activos:
            query = query.where(ProductoAlergenoModel.activo == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_alergenos_by_producto(
        self,
        id_producto: str,
        solo_activos: bool = True
    ) -> List:
        """
        Obtiene todos los alérgenos asociados a un producto específico con JOIN.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto (ULID).
        solo_activos : bool, optional
            Si True, solo retorna alérgenos activos. Por defecto True.

        Returns
        -------
        List[AlergenoModel]
            Lista directa de alérgenos asociados al producto.
        """
        from src.models.menu.alergeno_model import AlergenoModel

        query = (
            select(AlergenoModel)
            .join(ProductoAlergenoModel, AlergenoModel.id == ProductoAlergenoModel.id_alergeno)
            .where(ProductoAlergenoModel.id_producto == id_producto)
        )

        if solo_activos:
            query = query.where(ProductoAlergenoModel.activo == True)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_alergeno(self, id_alergeno: str) -> List[ProductoAlergenoModel]:
        """
        Obtiene todos los productos que contienen un alérgeno específico.

        Parameters
        ----------
        id_alergeno : str
            Identificador único del alérgeno.

        Returns
        -------
        List[ProductoAlergenoModel]
            Lista de relaciones producto-alérgeno para el alérgeno especificado.
        """
        query = select(ProductoAlergenoModel).where(
            ProductoAlergenoModel.id_alergeno == id_alergeno
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
