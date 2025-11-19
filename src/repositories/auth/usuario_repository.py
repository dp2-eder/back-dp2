"""
Repositorio para la gestión de usuarios en el sistema.
"""

from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload

from src.models.auth.usuario_model import UsuarioModel


class UsuarioRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de usuarios.

    
    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los usuarios en el sistema, siguiendo el patrón Repository.

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

    async def create(self, usuario: UsuarioModel) -> UsuarioModel:
        """
        Crea un nuevo usuario en la base de datos.

        Parameters
        ----------
        usuario : UsuarioModel
            Instancia del modelo de usuario a crear.

        Returns
        -------
        UsuarioModel
            El modelo de usuario creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(usuario)
            await self.session.flush()
            await self.session.refresh(usuario)
            return usuario
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, usuario_id: str) -> Optional[UsuarioModel]:
        """
        Obtiene un usuario por su identificador único.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a buscar.

        Returns
        -------
        Optional[UsuarioModel]
            El usuario encontrado o None si no existe.
        """
        query = select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[UsuarioModel]:
        """
        Obtiene un usuario por su email.

        Parameters
        ----------
        email : str
            Email del usuario a buscar.

        Returns
        -------
        Optional[UsuarioModel]
            El usuario encontrado o None si no existe.
        """
        query = select(UsuarioModel).where(UsuarioModel.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, usuario_id: str) -> bool:
        """
        Elimina un usuario de la base de datos por su ID.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a eliminar.

        Returns
        -------
        bool
            True si el usuario fue eliminado, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(UsuarioModel).where(UsuarioModel.id == usuario_id)
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def update(self, usuario_id: str, **kwargs) -> Optional[UsuarioModel]:
        """
        Actualiza un usuario existente con los valores proporcionados.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario a actualizar.
        **kwargs
            Campos y valores a actualizar.

        Returns
        -------
        Optional[UsuarioModel]
            El usuario actualizado o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Filtrar solo los campos que pertenecen al modelo
            valid_fields = {
                k: v for k, v in kwargs.items() if hasattr(UsuarioModel, k) and k != "id"
            }

            if not valid_fields:
                # No hay campos válidos para actualizar
                return await self.get_by_id(usuario_id)

            # Construir y ejecutar la sentencia de actualización
            stmt = (
                update(UsuarioModel)
                .where(UsuarioModel.id == usuario_id)
                .values(**valid_fields)
            )

            result = await self.session.execute(stmt)
            await self.session.flush()

            # Consultar el usuario actualizado
            updated_usuario = await self.get_by_id(usuario_id)
            
            # Si no se encontró el usuario, retornar None
            if not updated_usuario:
                return None

            return updated_usuario
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> Tuple[List[UsuarioModel], int]:
        """
        Obtiene una lista paginada de usuarios y el total de registros.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        Tuple[List[UsuarioModel], int]
            Tupla con la lista de usuarios y el número total de registros.
        """
        # Consulta para obtener los usuarios paginados
        query = select(UsuarioModel).offset(skip).limit(limit)

        # Consulta para obtener el total de registros
        count_query = select(func.count(UsuarioModel.id))

        try:
            # Ejecutar ambas consultas
            result = await self.session.execute(query)
            count_result = await self.session.execute(count_query)

            # Obtener los resultados
            usuarios = result.scalars().all()
            total = count_result.scalar() or 0

            return list(usuarios), total
        except SQLAlchemyError:
            # En caso de error, no es necesario hacer rollback aquí
            # porque no estamos modificando datos
            raise

    async def update_ultimo_acceso(self, usuario_id: str) -> Optional[UsuarioModel]:
        """
        Actualiza el campo ultimo_acceso de un usuario.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario.

        Returns
        -------
        Optional[UsuarioModel]
            El usuario actualizado o None si no existe.
        """
        try:
            stmt = (
                update(UsuarioModel)
                .where(UsuarioModel.id == usuario_id)
                .values(ultimo_acceso=datetime.now(timezone.utc))
            )
            await self.session.execute(stmt)
            await self.session.flush()
            
            return await self.get_by_id(usuario_id)
        except SQLAlchemyError:
            await self.session.rollback()
            raise

