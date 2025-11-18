"""
Servicio para la gestión de sesiones de mesa en el sistema.
"""

from typing import List, Optional
from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository
from src.repositories.auth.usuario_repository import UsuarioRepository
from src.repositories.mesas.mesa_repository import MesaRepository
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.api.schemas.sesion_mesa_schema import (
    SesionMesaCreate,
    SesionMesaResponse,
    SesionMesaSummary,
    SesionMesaUpdate,
    SesionMesaListResponse,
)
from src.business_logic.exceptions.sesion_mesa_exceptions import (
    SesionMesaNotFoundError,
    SesionMesaValidationError,
    SesionMesaConflictError,
    SesionMesaInactivaError,
)


class SesionMesaService:
    """Servicio para la gestión de sesiones de mesa.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con sesiones de mesa, incluyendo creación, validaciones y manejo de excepciones.

    Attributes
    ----------
    repository : SesionMesaRepository
        Repositorio para acceso a datos de sesiones de mesa.
    usuario_repository : UsuarioRepository
        Repositorio para validar usuarios.
    mesa_repository : MesaRepository
        Repositorio para validar mesas.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = SesionMesaRepository(session)
        self.usuario_repository = UsuarioRepository(session)
        self.mesa_repository = MesaRepository(session)

    async def create_sesion_mesa(
        self, id_usuario: str, id_mesa: str
    ) -> SesionMesaResponse:
        """
        Crea una nueva sesión de mesa para un usuario en una mesa.

        Si ya existe una sesión activa para este usuario en esta mesa,
        retorna la sesión existente en lugar de crear una nueva.

        Parameters
        ----------
        id_usuario : str
            ID del usuario que inicia la sesión.
        id_mesa : str
            ID de la mesa donde se inicia la sesión.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa creada o existente.

        Raises
        ------
        SesionMesaValidationError
            Si el usuario o la mesa no existen.
        SesionMesaConflictError
            Si hay un error de integridad al crear la sesión.
        """
        # Validar que el usuario existe
        usuario = await self.usuario_repository.get_by_id(id_usuario)
        if not usuario:
            raise SesionMesaValidationError(
                f"No se encontró el usuario con ID '{id_usuario}'"
            )

        # Validar que la mesa existe
        mesa = await self.mesa_repository.get_by_id(id_mesa)
        if not mesa:
            raise SesionMesaValidationError(
                f"No se encontró la mesa con ID '{id_mesa}'"
            )

        # Verificar si ya existe una sesión activa para este usuario en esta mesa
        sesion_existente = await self.repository.get_active_by_usuario_and_mesa(
            id_usuario, id_mesa
        )
        if sesion_existente:
            # Retornar la sesión existente
            return SesionMesaResponse.model_validate(sesion_existente)

        # Generar token único para la sesión
        token_sesion = str(ULID())

        try:
            # Crear nueva sesión
            sesion = SesionMesaModel(
                id_usuario_creador=id_usuario,
                id_mesa=id_mesa,
                token_sesion=token_sesion,
                estado=EstadoSesionMesa.ACTIVA,
            )

            # Persistir en la base de datos
            created_sesion = await self.repository.create(sesion)

            # Retornar como schema de respuesta
            return SesionMesaResponse.model_validate(created_sesion)
        except IntegrityError as e:
            raise SesionMesaConflictError(f"Error al crear la sesión de mesa: {str(e)}")

    async def get_sesion_by_id(self, sesion_id: str) -> SesionMesaResponse:
        """
        Obtiene una sesión de mesa por su ID.

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a buscar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa encontrada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        """
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )
        return SesionMesaResponse.model_validate(sesion)

    async def get_sesion_by_token(self, token_sesion: str) -> SesionMesaResponse:
        """
        Obtiene una sesión de mesa por su token único.

        Parameters
        ----------
        token_sesion : str
            Token de la sesión a buscar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa encontrada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        """
        sesion = await self.repository.get_by_token(token_sesion)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con token '{token_sesion}'"
            )
        return SesionMesaResponse.model_validate(sesion)

    async def get_active_sesion_by_usuario_mesa(
        self, id_usuario: str, id_mesa: str
    ) -> Optional[SesionMesaResponse]:
        """
        Obtiene una sesión activa para un usuario en una mesa específica.

        Parameters
        ----------
        id_usuario : str
            ID del usuario.
        id_mesa : str
            ID de la mesa.

        Returns
        -------
        Optional[SesionMesaResponse]
            La sesión activa encontrada, o None si no existe.
        """
        sesion = await self.repository.get_active_by_usuario_and_mesa(
            id_usuario, id_mesa
        )
        if not sesion:
            return None
        return SesionMesaResponse.model_validate(sesion)

    async def get_sesiones_by_usuario(
        self, id_usuario: str, skip: int = 0, limit: int = 100
    ) -> List[SesionMesaSummary]:
        """
        Obtiene una lista de sesiones de un usuario (activas y finalizadas).

        Parameters
        ----------
        id_usuario : str
            ID del usuario.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        List[SesionMesaSummary]
            Lista de sesiones del usuario.
        """
        sesiones, _ = await self.repository.get_all(
            skip=skip, limit=limit, id_usuario=id_usuario
        )
        return [SesionMesaSummary.model_validate(sesion) for sesion in sesiones]

    async def finalizar_sesion(self, sesion_id: str) -> SesionMesaResponse:
        """
        Finaliza una sesión de mesa.

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a finalizar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa finalizada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        SesionMesaValidationError
            Si la sesión ya está finalizada.
        """
        # Verificar que la sesión existe
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        # Verificar que la sesión no esté ya finalizada
        if sesion.estado == EstadoSesionMesa.FINALIZADA:
            raise SesionMesaValidationError(
                "La sesión de mesa ya está finalizada"
            )

        # Finalizar la sesión
        sesion_finalizada = await self.repository.finalizar_sesion(sesion_id)

        return SesionMesaResponse.model_validate(sesion_finalizada)

    async def validar_sesion_activa(self, sesion_id: str) -> bool:
        """
        Valida que una sesión existe y está activa.

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a validar.

        Returns
        -------
        bool
            True si la sesión existe y está activa, False en caso contrario.
        """
        try:
            sesion = await self.repository.get_by_id(sesion_id)
            if not sesion:
                return False
            return sesion.estado == EstadoSesionMesa.ACTIVA
        except Exception:
            return False

    async def update_sesion_mesa(
        self, sesion_id: str, sesion_data: SesionMesaUpdate
    ) -> SesionMesaResponse:
        """
        Actualiza una sesión de mesa existente.

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a actualizar.
        sesion_data : SesionMesaUpdate
            Datos a actualizar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa actualizada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        SesionMesaValidationError
            Si los datos no son válidos.
        """
        # Verificar que la sesión existe
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = sesion_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la sesión actual
            return SesionMesaResponse.model_validate(sesion)

        # Si se está cerrando la sesión, actualizar fecha_fin automáticamente
        if "estado" in update_data:
            if update_data["estado"] in (EstadoSesionMesa.CERRADA, EstadoSesionMesa.FINALIZADA):
                from datetime import datetime
                if "fecha_fin" not in update_data:
                    update_data["fecha_fin"] = datetime.now()

        # Actualizar la sesión
        sesion_actualizada = await self.repository.update(sesion_id, update_data)
        if not sesion_actualizada:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        return SesionMesaResponse.model_validate(sesion_actualizada)

    async def cerrar_sesion(self, sesion_id: str) -> SesionMesaResponse:
        """
        Cierra una sesión de mesa (cambia el estado a CERRADO y actualiza fecha_fin).

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a cerrar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa cerrada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        SesionMesaValidationError
            Si la sesión ya está cerrada.
        """
        # Verificar que la sesión existe
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        # Verificar que la sesión no esté ya cerrada
        if sesion.estado in (EstadoSesionMesa.CERRADA, EstadoSesionMesa.FINALIZADA):
            raise SesionMesaValidationError(
                "La sesión de mesa ya está cerrada"
            )

        # Cerrar la sesión
        from datetime import datetime
        update_data = {
            "estado": EstadoSesionMesa.CERRADA,
            "fecha_fin": datetime.now()
        }
        sesion_cerrada = await self.repository.update(sesion_id, update_data)
        if not sesion_cerrada:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        return SesionMesaResponse.model_validate(sesion_cerrada)

    async def cerrar_sesion_por_token(self, token_sesion: str) -> SesionMesaResponse:
        """
        Cierra una sesión de mesa usando el token compartido.

        Este método permite cerrar una sesión usando el token que tienen los clientes,
        sin necesidad de conocer el ID interno de la sesión.

        Parameters
        ----------
        token_sesion : str
            Token de la sesión a cerrar.

        Returns
        -------
        SesionMesaResponse
            La sesión de mesa cerrada.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        SesionMesaValidationError
            Si la sesión ya está cerrada.
        """
        # Buscar sesión por token
        sesion = await self.repository.get_by_token(token_sesion)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con token '{token_sesion}'"
            )

        # Reutilizar el método de cierre existente por ID
        return await self.cerrar_sesion(sesion.id)

    async def delete_sesion_mesa(self, sesion_id: str) -> None:
        """
        Elimina una sesión de mesa del sistema.

        Parameters
        ----------
        sesion_id : str
            ID de la sesión a eliminar.

        Raises
        ------
        SesionMesaNotFoundError
            Si la sesión no existe.
        """
        # Verificar que la sesión existe
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionMesaNotFoundError(
                f"No se encontró la sesión de mesa con ID '{sesion_id}'"
            )

        # Eliminar la sesión usando el repositorio
        await self.repository.delete(sesion_id)

    async def get_sesiones_list(
        self,
        skip: int = 0,
        limit: int = 100,
        id_mesa: Optional[str] = None,
        estado: Optional[EstadoSesionMesa] = None,
    ) -> SesionMesaListResponse:
        """
        Obtiene una lista paginada de sesiones de mesa con filtros opcionales.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_mesa : Optional[str], optional
            Filtrar por ID de mesa específica.
        estado : Optional[EstadoSesionMesa], optional
            Filtrar por estado de la sesión (activa, inactiva, cerrada, finalizada).

        Returns
        -------
        SesionMesaListResponse
            Lista paginada de sesiones de mesa con metadatos.
        """
        # Obtener sesiones con filtros
        sesiones, total = await self.repository.get_all(
            skip=skip,
            limit=limit,
            id_mesa=id_mesa,
            estado=estado
        )

        # Convertir a schemas de respuesta
        sesiones_response = [
            SesionMesaResponse.model_validate(sesion) for sesion in sesiones
        ]

        # Calcular página actual
        page = (skip // limit) + 1 if limit > 0 else 1

        return SesionMesaListResponse(
            total=total,
            page=page,
            limit=limit,
            sesiones=sesiones_response
        )
