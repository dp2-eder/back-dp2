"""
Repositorio para la gestión de tipos de opciones en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.pedidos.tipo_opciones_model import TipoOpcionModel


class TipoOpcionRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de tipos de opciones.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los tipos de opciones en el sistema, siguiendo el patrón Repository.

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

    async def create(self, tipo_opcion: TipoOpcionModel) -> TipoOpcionModel:
        """
        Crea un nuevo tipo de opción en la base de datos.

        Parameters
        ----------
        tipo_opcion : TipoOpcionModel
            Instancia del modelo de tipo de opción a crear.

        Returns
        -------
        TipoOpcionModel
            El modelo de tipo de opción creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(tipo_opcion)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(tipo_opcion)
            return tipo_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, tipo_opcion_id: str) -> Optional[TipoOpcionModel]:
        """
        Obtiene un tipo de opción por su identificador único.

        Parameters
        ----------
        tipo_opcion_id : str
            Identificador único del tipo de opción a buscar.

        Returns
        -------
        Optional[TipoOpcionModel]
            El tipo de opción encontrado o None si no existe.
        """
        query = select(TipoOpcionModel).where(TipoOpcionModel.id == tipo_opcion_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, tipo_opcion_id: str) -> bool:
        """
        Elimina un tipo de opción de la base de datos por su ID.

        Parameters
        ----------
        tipo_opcion_id : str
            Identificador único del tipo de opción a eliminar.

        Returns
        -------
        bool
            True si el tipo de opción fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(TipoOpcionModel).where(TipoOpcionModel.id == tipo_opcion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, tipo_opcion_id: str, **kwargs) -> Optional[TipoOpcionModel]:
        """
        Actualiza un tipo de opción existente con los valores proporcionados.

        Parameters
        ----------
        tipo_opcion_id : str
            Identificador único del tipo de opción a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[TipoOpcionModel]
            El tipo de opción actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(TipoOpcionModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(tipo_opcion_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(TipoOpcionModel)
                .where(TipoOpcionModel.id == tipo_opcion_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el tipo de opción actualizado
            updated_tipo_opcion = await self.get_by_id(tipo_opcion_id)
            
            # Si no se encontró el tipo de opción, retornar None
            if not updated_tipo_opcion:
                return None

            return updated_tipo_opcion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[TipoOpcionModel], int]:
        """
        Obtiene una lista paginada de tipos de opciones y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[TipoOpcionModel], int]
            Tupla con la lista de tipos de opciones y el número total de registros.
        """
        # Consulta para obtener los tipos de opciones paginados
        query = select(TipoOpcionModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(TipoOpcionModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            tipos_opciones = result.scalars().all()
            total = count_result.scalar() or 0

            return list(tipos_opciones), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def get_by_codigo(self, codigo: str) -> Optional[TipoOpcionModel]:
        """
        Obtiene un tipo de opción por su código.

        Parameters
        ----------
        codigo : str
            Código del tipo de opción a buscar.

        Returns
        -------
        Optional[TipoOpcionModel]
            El tipo de opción encontrado o None si no existe.
        """
        query = select(TipoOpcionModel).where(TipoOpcionModel.codigo == codigo)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_activos(self) -> List[TipoOpcionModel]:
        """
        Obtiene todos los tipos de opciones activos.

        Returns
        -------
        List[TipoOpcionModel]
            Lista de tipos de opciones activos.
        """
        query = select(TipoOpcionModel).where(TipoOpcionModel.activo == True).order_by(TipoOpcionModel.orden)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_batch(self, tipos_opciones: List[TipoOpcionModel]) -> List[TipoOpcionModel]:
        """
        Crea múltiples tipos de opciones en la base de datos en una sola operación.

        Parameters
        ----------
        tipos_opciones : List[TipoOpcionModel]
            Lista de instancias del modelo de tipo de opción a crear.

        Returns
        -------
        List[TipoOpcionModel]
            Lista de modelos de tipo de opción creados con sus IDs asignados.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add_all(tipos_opciones)
            await self.session.flush()
            await self.session.commit()
            for tipo_opcion in tipos_opciones:
                await self.session.refresh(tipo_opcion)
            return tipos_opciones
        except SQLAlchemyError:
            await self.session.rollback()
            raise