from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from src.models.auth.admin_model import AdminModel


class AdminRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de administradores.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con los administradores en el sistema, siguiendo el patrón Repository.

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

    async def create(self, admin: AdminModel) -> AdminModel:
        """
        Crea un nuevo administrador en la base de datos.

        Parameters
        ----------
        admin : AdminModel
            Instancia del modelo de administrador a crear.

        Returns
        -------
        AdminModel
            El modelo de administrador creado con su ID asignado.

        Raises
        ----
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(admin)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(admin)
            return admin
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, admin_id: str) -> Optional[AdminModel]:
        """
        Obtiene un administrador por su identificador único.

        Parameters
        ----------
        admin_id : str
            Identificador único del administrador a buscar.

        Returns
        -------
        Optional[AdminModel]
            El administrador encontrado o None si no existe.
        """
        query = select(AdminModel).where(AdminModel.id == admin_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        """
        Obtiene un administrador por su email.

        Parameters
        ----------
        email : str
            Email del administrador a buscar.

        Returns
        -------
        Optional[AdminModel]
            El administrador encontrado o None si no existe.
        """
        query = select(AdminModel).where(AdminModel.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete(self, admin_id: str) -> bool:
        """
        Elimina un administrador de la base de datos por su ID.

        Parameters
        ----------
        admin_id : str
            Identificador único del administrador a eliminar.

        Returns
        -------
        bool
            True si el administrador fue eliminado, False si no existía.

        Raises
        ----
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(AdminModel).where(AdminModel.id == admin_id)
            result = await self.session.execute(stmt)
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise


    async def update_ultimo_acceso(self, admin_id: str) -> Optional[AdminModel]:
        """
        Actualiza el campo ultimo_acceso de un administrador.

        Parameters
        ----------
        admin_id : str
            Identificador único del administrador.

        Returns
        -------
        Optional[AdminModel]
            El administrador actualizado o None si no existe.
        """
        try:
            stmt = (
                update(AdminModel)
                .where(AdminModel.id == admin_id)
                .values(ultimo_acceso=datetime.now(timezone.utc))
            )
            await self.session.execute(stmt)
            await self.session.flush()

            return await self.get_by_id(admin_id)
        except SQLAlchemyError:
            await self.session.rollback()
            raise
