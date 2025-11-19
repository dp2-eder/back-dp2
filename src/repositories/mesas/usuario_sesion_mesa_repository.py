"""
Repositorio para la gestión de asociaciones usuario-sesión de mesa.
"""

from typing import Optional, List
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel
from src.models.auth.usuario_model import UsuarioModel


class UsuarioSesionMesaRepository:
    """Repositorio para gestionar operaciones CRUD de asociaciones usuario-sesión.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con la tabla intermedia usuarios_sesiones_mesas.

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

    async def create(
        self, usuario_sesion_mesa: UsuarioSesionMesaModel
    ) -> UsuarioSesionMesaModel:
        """
        Crea una nueva asociación usuario-sesión en la base de datos.

        Parameters
        ----------
        usuario_sesion_mesa : UsuarioSesionMesaModel
            Instancia del modelo de asociación a crear.

        Returns
        -------
        UsuarioSesionMesaModel
            El modelo de asociación creado con su ID asignado.

        Raises
        ------
        IntegrityError
            Si ya existe una asociación con el mismo usuario y sesión.
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(usuario_sesion_mesa)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(usuario_sesion_mesa)
            return usuario_sesion_mesa
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, asociacion_id: str) -> Optional[UsuarioSesionMesaModel]:
        """
        Obtiene una asociación por su ID.

        Parameters
        ----------
        asociacion_id : str
            El ID de la asociación a buscar.

        Returns
        -------
        Optional[UsuarioSesionMesaModel]
            La asociación encontrada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = select(UsuarioSesionMesaModel).where(
                UsuarioSesionMesaModel.id == asociacion_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def get_by_usuario_and_sesion(
        self, id_usuario: str, id_sesion_mesa: str
    ) -> Optional[UsuarioSesionMesaModel]:
        """
        Obtiene una asociación específica de usuario y sesión.

        Parameters
        ----------
        id_usuario : str
            El ID del usuario.
        id_sesion_mesa : str
            El ID de la sesión de mesa.

        Returns
        -------
        Optional[UsuarioSesionMesaModel]
            La asociación encontrada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = select(UsuarioSesionMesaModel).where(
                UsuarioSesionMesaModel.id_usuario == id_usuario,
                UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def get_usuarios_by_sesion(self, id_sesion_mesa: str) -> List[UsuarioModel]:
        """
        Obtiene todos los usuarios asociados a una sesión de mesa.

        Parameters
        ----------
        id_sesion_mesa : str
            El ID de la sesión de mesa.

        Returns
        -------
        List[UsuarioModel]
            Lista de usuarios en la sesión.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = (
                select(UsuarioModel)
                .join(
                    UsuarioSesionMesaModel,
                    UsuarioModel.id == UsuarioSesionMesaModel.id_usuario,
                )
                .where(UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa)
                .order_by(UsuarioSesionMesaModel.fecha_ingreso)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError:
            raise

    async def get_sesiones_by_usuario(
        self, id_usuario: str
    ) -> List[UsuarioSesionMesaModel]:
        """
        Obtiene todas las asociaciones de sesiones para un usuario.

        Parameters
        ----------
        id_usuario : str
            El ID del usuario.

        Returns
        -------
        List[UsuarioSesionMesaModel]
            Lista de asociaciones de sesiones del usuario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = (
                select(UsuarioSesionMesaModel)
                .where(UsuarioSesionMesaModel.id_usuario == id_usuario)
                .order_by(UsuarioSesionMesaModel.fecha_ingreso.desc())
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError:
            raise

    async def delete(
        self, id_usuario: str, id_sesion_mesa: str
    ) -> bool:
        """
        Elimina una asociación usuario-sesión.

        Parameters
        ----------
        id_usuario : str
            El ID del usuario.
        id_sesion_mesa : str
            El ID de la sesión de mesa.

        Returns
        -------
        bool
            True si se eliminó la asociación, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = delete(UsuarioSesionMesaModel).where(
                UsuarioSesionMesaModel.id_usuario == id_usuario,
                UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa,
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all_by_sesion(
        self, id_sesion_mesa: str
    ) -> List[UsuarioSesionMesaModel]:
        """
        Obtiene todas las asociaciones para una sesión específica.

        Parameters
        ----------
        id_sesion_mesa : str
            El ID de la sesión de mesa.

        Returns
        -------
        List[UsuarioSesionMesaModel]
            Lista de todas las asociaciones de la sesión.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = (
                select(UsuarioSesionMesaModel)
                .where(UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa)
                .order_by(UsuarioSesionMesaModel.fecha_ingreso)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError:
            raise
