"""
Repositorio para la gestión de sesiones de mesa en el sistema.
"""

from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa


class SesionMesaRepository:
    """Repositorio para gestionar operaciones CRUD del modelo de sesiones de mesa.

    Proporciona acceso a la capa de persistencia para las operaciones
    relacionadas con las sesiones de mesa en el sistema, siguiendo el patrón Repository.

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

    async def create(self, sesion_mesa: SesionMesaModel) -> SesionMesaModel:
        """
        Crea una nueva sesión de mesa en la base de datos.

        Parameters
        ----------
        sesion_mesa : SesionMesaModel
            Instancia del modelo de sesión de mesa a crear.

        Returns
        -------
        SesionMesaModel
            El modelo de sesión de mesa creado con su ID asignado.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            self.session.add(sesion_mesa)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(sesion_mesa)
            return sesion_mesa
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_by_id(self, sesion_id: str) -> Optional[SesionMesaModel]:
        """
        Obtiene una sesión de mesa por su ID.

        Parameters
        ----------
        sesion_id : str
            El ID de la sesión de mesa a buscar.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión de mesa encontrada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = select(SesionMesaModel).where(SesionMesaModel.id == sesion_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def get_by_token(self, token_sesion: str) -> Optional[SesionMesaModel]:
        """
        Obtiene una sesión de mesa por su token único.

        Parameters
        ----------
        token_sesion : str
            El token de la sesión a buscar.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión de mesa encontrada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = select(SesionMesaModel).where(
                SesionMesaModel.token_sesion == token_sesion
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def get_active_by_mesa(
        self, id_mesa: str
    ) -> Optional[SesionMesaModel]:
        """
        Obtiene una sesión activa para una mesa específica.

        Si existen múltiples sesiones activas (situación anómala),
        retorna la más reciente por fecha_inicio.

        Parameters
        ----------
        id_mesa : str
            El ID de la mesa.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión activa encontrada (la más reciente si hay múltiples), o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = (
                select(SesionMesaModel)
                .where(
                    SesionMesaModel.id_mesa == id_mesa,
                    SesionMesaModel.estado == EstadoSesionMesa.ACTIVA,
                )
                .order_by(SesionMesaModel.fecha_inicio.desc())
            )
            result = await self.session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError:
            raise

    async def get_active_by_usuario_and_mesa(
        self, id_usuario: str, id_mesa: str
    ) -> Optional[SesionMesaModel]:
        """
        Obtiene una sesión activa para un usuario específico en una mesa.

        Parameters
        ----------
        id_usuario : str
            El ID del usuario.
        id_mesa : str
            El ID de la mesa.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión activa encontrada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = (
                select(SesionMesaModel)
                .join(
                    UsuarioSesionMesaModel,
                    SesionMesaModel.id == UsuarioSesionMesaModel.id_sesion_mesa,
                )
                .where(
                    UsuarioSesionMesaModel.id_usuario == id_usuario,
                    SesionMesaModel.id_mesa == id_mesa,
                    SesionMesaModel.estado == EstadoSesionMesa.ACTIVA,
                )
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    async def add_usuario_to_sesion(
        self, id_sesion_mesa: str, id_usuario: str
    ) -> UsuarioSesionMesaModel:
        """
        Agrega un usuario a una sesión de mesa existente.

        Parameters
        ----------
        id_sesion_mesa : str
            El ID de la sesión de mesa.
        id_usuario : str
            El ID del usuario a agregar.

        Returns
        -------
        UsuarioSesionMesaModel
            La asociación creada.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            asociacion = UsuarioSesionMesaModel(
                id_usuario=id_usuario,
                id_sesion_mesa=id_sesion_mesa,
                fecha_ingreso=datetime.now()
            )
            self.session.add(asociacion)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(asociacion)
            return asociacion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def remove_usuario_from_sesion(
        self, id_sesion_mesa: str, id_usuario: str
    ) -> bool:
        """
        Elimina un usuario de una sesión de mesa.

        Parameters
        ----------
        id_sesion_mesa : str
            El ID de la sesión de mesa.
        id_usuario : str
            El ID del usuario a eliminar.

        Returns
        -------
        bool
            True si se eliminó el usuario, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            from sqlalchemy import delete
            stmt = delete(UsuarioSesionMesaModel).where(
                UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa,
                UsuarioSesionMesaModel.id_usuario == id_usuario,
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def usuario_in_sesion(
        self, id_sesion_mesa: str, id_usuario: str
    ) -> bool:
        """
        Verifica si un usuario ya está en una sesión de mesa.

        Parameters
        ----------
        id_sesion_mesa : str
            El ID de la sesión de mesa.
        id_usuario : str
            El ID del usuario.

        Returns
        -------
        bool
            True si el usuario está en la sesión, False en caso contrario.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            stmt = select(UsuarioSesionMesaModel).where(
                UsuarioSesionMesaModel.id_sesion_mesa == id_sesion_mesa,
                UsuarioSesionMesaModel.id_usuario == id_usuario,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError:
            raise

    async def update(
        self, sesion_id: str, data: dict
    ) -> Optional[SesionMesaModel]:
        """
        Actualiza una sesión de mesa existente.

        Parameters
        ----------
        sesion_id : str
            El ID de la sesión de mesa a actualizar.
        data : dict
            Diccionario con los campos a actualizar.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión de mesa actualizada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Obtener la sesión actual
            sesion = await self.get_by_id(sesion_id)
            if not sesion:
                return None

            # Actualizar campos
            for key, value in data.items():
                if hasattr(sesion, key):
                    setattr(sesion, key, value)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(sesion)
            return sesion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def finalizar_sesion(self, sesion_id: str) -> Optional[SesionMesaModel]:
        """
        Finaliza una sesión de mesa marcándola como finalizada.

        Parameters
        ----------
        sesion_id : str
            El ID de la sesión de mesa a finalizar.

        Returns
        -------
        Optional[SesionMesaModel]
            La sesión de mesa finalizada, o None si no existe.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Obtener la sesión actual
            sesion = await self.get_by_id(sesion_id)
            if not sesion:
                return None

            # Actualizar estado y fecha de fin
            sesion.estado = EstadoSesionMesa.FINALIZADA
            sesion.fecha_fin = datetime.now()

            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(sesion)
            return sesion
        except SQLAlchemyError:
            await self.session.rollback()
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        id_mesa: Optional[str] = None,
        id_usuario: Optional[str] = None,
        estado: Optional[EstadoSesionMesa] = None,
    ) -> Tuple[List[SesionMesaModel], int]:
        """
        Obtiene una lista paginada de sesiones de mesa con filtros opcionales.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_mesa : Optional[str], optional
            Filtrar por ID de mesa.
        id_usuario : Optional[str], optional
            Filtrar por ID de usuario (a través de la tabla intermedia).
        estado : Optional[EstadoSesionMesa], optional
            Filtrar por estado de la sesión.

        Returns
        -------
        Tuple[List[SesionMesaModel], int]
            Tupla con la lista de sesiones de mesa y el total de registros.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            # Construir query base
            stmt = select(SesionMesaModel)

            # Si se filtra por usuario, hacer join con la tabla intermedia
            if id_usuario:
                stmt = stmt.join(
                    UsuarioSesionMesaModel,
                    SesionMesaModel.id == UsuarioSesionMesaModel.id_sesion_mesa,
                ).where(UsuarioSesionMesaModel.id_usuario == id_usuario)

            # Aplicar filtros opcionales
            if id_mesa:
                stmt = stmt.where(SesionMesaModel.id_mesa == id_mesa)
            if estado:
                stmt = stmt.where(SesionMesaModel.estado == estado)

            # Contar total antes de aplicar paginación
            count_stmt = select(func.count()).select_from(stmt.alias())
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar() or 0

            # Aplicar ordenamiento y paginación
            stmt = (
                stmt.order_by(SesionMesaModel.fecha_inicio.desc())
                .offset(skip)
                .limit(limit)
            )

            # Ejecutar query
            result = await self.session.execute(stmt)
            sesiones = list(result.scalars().all())

            return sesiones, total
        except SQLAlchemyError:
            raise

    async def delete(self, sesion_id: str) -> bool:
        """
        Elimina una sesión de mesa de la base de datos.

        Parameters
        ----------
        sesion_id : str
            El ID de la sesión de mesa a eliminar.

        Returns
        -------
        bool
            True si se eliminó la sesión, False si no existía.

        Raises
        ------
        SQLAlchemyError
            Si ocurre un error durante la operación en la base de datos.
        """
        try:
            from sqlalchemy import delete
            stmt = delete(SesionMesaModel).where(SesionMesaModel.id == sesion_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError:
            await self.session.rollback()
            raise