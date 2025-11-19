"""
Repositorio para la gestión de opciones de productos en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.pedidos.producto_opcion_model import ProductoOpcionModel


class ProductoOpcionRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de opciones de productos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las opciones de productos en el sistema, siguiendo el patrón Repository.

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

    async def create(self, producto_opcion: ProductoOpcionModel) -> ProductoOpcionModel:
        """
        Crea una nueva opción de producto en la base de datos.

        Parameters
        ----------
        producto_opcion : ProductoOpcionModel
            Instancia del modelo de opción de producto a crear.

        Returns
        -------
        ProductoOpcionModel
            El modelo de opción de producto creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(producto_opcion)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(producto_opcion)
            return producto_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, producto_opcion_id: str) -> Optional[ProductoOpcionModel]:

        """
        Obtiene una opción de producto por su identificador único.

        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a buscar.

        Returns
        -------
        Optional[ProductoOpcionModel]
            La opción de producto encontrada o None si no existe.
        """
        query = select(ProductoOpcionModel).where(ProductoOpcionModel.id == producto_opcion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, producto_opcion_id: str) -> bool:
        """
        Elimina una opción de producto de la base de datos por su ID.

        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a eliminar.

        Returns
        -------
        bool
            True si la opción de producto fue eliminada, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(ProductoOpcionModel).where(ProductoOpcionModel.id == producto_opcion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, producto_opcion_id: str, **kwargs) -> Optional[ProductoOpcionModel]:
        """
        Actualiza una opción de producto existente con los valores proporcionados.

        Parameters
        ----------
        producto_opcion_id : str
            Identificador único de la opción de producto a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[ProductoOpcionModel]
            La opción de producto actualizada o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(ProductoOpcionModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(producto_opcion_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(ProductoOpcionModel)
                .where(ProductoOpcionModel.id == producto_opcion_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar la opción de producto actualizada
            updated_producto_opcion = await self.get_by_id(producto_opcion_id)
            
            # Si no se encontró la opción de producto, retornar None
            if not updated_producto_opcion:
                return None

            return updated_producto_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[ProductoOpcionModel], int]:
        """
        Obtiene una lista paginada de opciones de productos y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[ProductoOpcionModel], int]
            Tupla con la lista de opciones de productos y el número total de registros.
        """
        # Consulta para obtener las opciones de productos paginadas
        query = select(ProductoOpcionModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(ProductoOpcionModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            producto_opciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(producto_opciones), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise
