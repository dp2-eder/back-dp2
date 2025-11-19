"""
Repositorio para la gestión de roles en el sistema.
"""

from typing import Optional, List, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.auth.rol_model import RolModel


class RolRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de roles.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los roles en el sistema, siguiendo el patrón Repository.

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

    async def create(self, rol: RolModel) -> RolModel:
        """
        Crea un nuevo rol en la base de datos.

        Parameters
        ----------
        rol : RolModel
            Instancia del modelo de rol a crear.

        Returns
        -------
        RolModel
            El modelo de rol creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(rol)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(rol)
            return rol
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, rol_id: str) -> Optional[RolModel]:
        """
        Obtiene un rol por su identificador único.

        Parameters
        ----------
        rol_id : str
            Identificador único del rol a buscar.

        Returns
        -------
        Optional[RolModel]
            El rol encontrado o None si no existe.
        """
        query = select(RolModel).where(RolModel.id == rol_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, rol_id: str) -> bool:
        """
        Elimina un rol de la base de datos por su ID.

        Parameters
        ----------
        rol_id : str
            Identificador único del rol a eliminar.

        Returns
        -------
        bool
            True si el rol fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(RolModel).where(RolModel.id == rol_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, rol_id: str, **kwargs) -> Optional[RolModel]:
        """
        Actualiza un rol existente con los valores proporcionados.

        Parameters
        ----------
        rol_id : str
            Identificador único del rol a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[RolModel]
            El rol actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(RolModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(rol_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(RolModel)
                .where(RolModel.id == rol_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.commit()

            # Consultar el rol actualizado
            updated_rol = await self.get_by_id(rol_id)
            
            # Si no se encontró el rol, retornar None
            if not updated_rol:
                return None

            return updated_rol
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[RolModel], int]:
        """
        Obtiene una lista paginada de roles y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[RolModel], int]
            Tupla con la lista de roles y el número total de registros.
        """
        # Consulta para obtener los roles paginados
        query = select(RolModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(RolModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            roles = result.scalars().all()
            total = count_result.scalar() or 0

            return list(roles), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise
