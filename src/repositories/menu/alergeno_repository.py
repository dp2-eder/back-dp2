"""
Repositorio para la gestión de alérgenos en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.menu.alergeno_model import AlergenoModel


class AlergenoRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de alérgenos.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los alérgenos en el sistema, siguiendo el patrón Repository.

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

    async def create(self, alergeno: AlergenoModel) -> AlergenoModel:
        """
        Crea un nuevo alérgeno en la base de datos.

        Parameters
        ----------
        alergeno : AlergenoModel
            Instancia del modelo de alérgeno a crear.

        Returns
        -------
        AlergenoModel
            El modelo de alérgeno creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(alergeno)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(alergeno)
            return alergeno
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, alergeno_id: str) -> Optional[AlergenoModel]:
        """
        Obtiene un alérgeno por su identificador único.

        Parameters
        ----------
        alergeno_id : str
            Identificador único del alérgeno a buscar.

        Returns
        -------
        Optional[AlergenoModel]
            El alérgeno encontrado o None si no existe.
        """
        query = select(AlergenoModel).where(AlergenoModel.id == alergeno_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, alergeno_id: str) -> bool:
        """
        Elimina un alérgeno de la base de datos por su ID.

        Parameters
        ----------
        alergeno_id : str
            Identificador único del alérgeno a eliminar.

        Returns
        -------
        bool
            True si el alérgeno fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(AlergenoModel).where(AlergenoModel.id == alergeno_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, alergeno_id: str, **kwargs) -> Optional[AlergenoModel]:
        """
        Actualiza un alérgeno existente con los valores proporcionados.

        Parameters
        ----------
        alergeno_id : str
            Identificador único del alérgeno a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[AlergenoModel]
            El alérgeno actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(AlergenoModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(alergeno_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(AlergenoModel)
                .where(AlergenoModel.id == alergeno_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el alérgeno actualizado
            updated_alergeno = await self.get_by_id(alergeno_id)
            
            # Si no se encontró el alérgeno, retornar None
            if not updated_alergeno:
                return None

            return updated_alergeno
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[AlergenoModel], int]:
        """
        Obtiene una lista paginada de alérgenos y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[AlergenoModel], int]
            Tupla con la lista de alérgenos y el número total de registros.
        """
        # Consulta para obtener los alérgenos paginados
        query = select(AlergenoModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(AlergenoModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            alergenos = result.scalars().all()
            total = count_result.scalar() or 0

            return list(alergenos), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def get_by_nombre(self, nombre: str) -> Optional[AlergenoModel]:
        """
        Obtiene un alérgeno por su nombre.

        Parameters
        ----------
        nombre : str
            Nombre del alérgeno a buscar.

        Returns
        -------
        Optional[AlergenoModel]
            El alérgeno encontrado o None si no existe.
        """
        query = select(AlergenoModel).where(AlergenoModel.nombre == nombre)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_activos(self) -> List[AlergenoModel]:
        """
        Obtiene todos los alérgenos activos.

        Returns
        -------
        List[AlergenoModel]
            Lista de alérgenos activos.
        """
        query = select(AlergenoModel).where(AlergenoModel.activo == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())
