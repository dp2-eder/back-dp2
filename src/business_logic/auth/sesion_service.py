"""
Servicio para la gestión de sesiones en el sistema.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.auth.sesion_repository import SesionRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.auth.sesion_model import SesionModel
from src.core.enums.sesion_enums import EstadoSesion
from src.api.schemas.sesion_schema import (
    SesionCreate,
    SesionUpdate,
    SesionResponse,
    SesionSummary,
    SesionList,
)
from src.business_logic.exceptions.sesion_exceptions import (
    SesionValidationError,
    SesionNotFoundError,
    SesionConflictError,
)


class SesionService:
    """Servicio para la gestión de sesiones en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con sesiones, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : SesionRepository
        Repositorio para acceso a datos de sesiones.
    local_repository : LocalRepository
        Repositorio para validar la existencia de locales.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = SesionRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_sesion(self, sesion_data: SesionCreate) -> SesionResponse:
        """
        Crea una nueva sesión en el sistema.

        Parameters
        ----------
        sesion_data : SesionCreate
            Datos para crear la nueva sesión.

        Returns
        -------
        SesionResponse
            Esquema de respuesta con los datos de la sesión creada.

        Raises
        ------
        SesionValidationError
            Si los datos no cumplen con las validaciones o el local no existe.
        SesionConflictError
            Si hay un conflicto al crear la sesión.
        """
        # Validar que id_domotica no esté vacío
        if not sesion_data.id_domotica or sesion_data.id_domotica.strip() == "":
            raise SesionValidationError("El id_domotica no puede estar vacío")

        # Validar que el local existe
        local = await self.local_repository.get_by_id(sesion_data.id_local)
        if not local:
            raise SesionValidationError(
                f"El local con ID '{sesion_data.id_local}' no existe"
            )

        try:
            # Crear modelo de sesión desde los datos
            sesion = SesionModel(
                id_domotica=sesion_data.id_domotica,
                id_local=sesion_data.id_local,
                estado=sesion_data.estado,
                orden=sesion_data.orden,
            )

            # Persistir en la base de datos
            created_sesion = await self.repository.create(sesion)

            # Convertir y retornar como esquema de respuesta
            return SesionResponse.model_validate(created_sesion)
        except IntegrityError as e:
            raise SesionConflictError(f"Error al crear la sesión: {str(e)}")

    async def get_sesion_by_id(self, sesion_id: str) -> SesionResponse:
        """
        Obtiene una sesión por su ID.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión a buscar (ULID).

        Returns
        -------
        SesionResponse
            Esquema de respuesta con los datos de la sesión.

        Raises
        ------
        SesionNotFoundError
            Si no se encuentra una sesión con el ID proporcionado.
        """
        # Buscar la sesión por su ID
        sesion = await self.repository.get_by_id(sesion_id)

        # Verificar si existe
        if not sesion:
            raise SesionNotFoundError(f"No se encontró la sesión con ID {sesion_id}")

        # Convertir y retornar como esquema de respuesta
        return SesionResponse.model_validate(sesion)

    async def get_sesiones_by_local(
        self, local_id: str, skip: int = 0, limit: int = 100
    ) -> SesionList:
        """
        Obtiene una lista paginada de sesiones por local.

        Parameters
        ----------
        local_id : str
            ID del local para filtrar sesiones.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        SesionList
            Esquema con la lista de sesiones y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise SesionValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise SesionValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener sesiones desde el repositorio
        sesiones, total = await self.repository.get_by_local(local_id, skip, limit)

        # Convertir modelos a esquemas de resumen
        sesion_summaries = [SesionSummary.model_validate(sesion) for sesion in sesiones]

        # Retornar esquema de lista
        return SesionList(items=sesion_summaries, total=total)

    async def get_sesiones_by_estado(
        self, estado: EstadoSesion, skip: int = 0, limit: int = 100
    ) -> SesionList:
        """
        Obtiene una lista paginada de sesiones por estado.

        Parameters
        ----------
        estado : EstadoSesion
            Estado para filtrar sesiones.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        SesionList
            Esquema con la lista de sesiones y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise SesionValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise SesionValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener sesiones desde el repositorio
        sesiones, total = await self.repository.get_by_estado(estado, skip, limit)

        # Convertir modelos a esquemas de resumen
        sesion_summaries = [SesionSummary.model_validate(sesion) for sesion in sesiones]

        # Retornar esquema de lista
        return SesionList(items=sesion_summaries, total=total)

    async def delete_sesion(self, sesion_id: str) -> bool:
        """
        Elimina una sesión por su ID.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión a eliminar (ULID).

        Returns
        -------
        bool
            True si la sesión fue eliminada correctamente.

        Raises
        ------
        SesionNotFoundError
            Si no se encuentra una sesión con el ID proporcionado.
        """
        # Verificar primero si la sesión existe
        sesion = await self.repository.get_by_id(sesion_id)
        if not sesion:
            raise SesionNotFoundError(f"No se encontró la sesión con ID {sesion_id}")

        # Eliminar la sesión
        result = await self.repository.delete(sesion_id)
        return result

    async def get_sesiones(
        self, skip: int = 0, limit: int = 100, estado: Optional[EstadoSesion] = None
    ) -> SesionList:
        """
        Obtiene una lista paginada de sesiones con filtro opcional por estado.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        estado : Optional[EstadoSesion], optional
            Estado para filtrar sesiones, por defecto None (sin filtro).

        Returns
        -------
        SesionList
            Esquema con la lista de sesiones y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise SesionValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise SesionValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener sesiones desde el repositorio
        sesiones, total = await self.repository.get_all(skip, limit, estado)

        # Convertir modelos a esquemas de resumen
        sesion_summaries = [SesionSummary.model_validate(sesion) for sesion in sesiones]

        # Retornar esquema de lista
        return SesionList(items=sesion_summaries, total=total)

    async def update_sesion(
        self, sesion_id: str, sesion_data: SesionUpdate
    ) -> SesionResponse:
        """
        Actualiza una sesión existente.

        Parameters
        ----------
        sesion_id : str
            Identificador único de la sesión a actualizar (ULID).
        sesion_data : SesionUpdate
            Datos para actualizar la sesión.

        Returns
        -------
        SesionResponse
            Esquema de respuesta con los datos de la sesión actualizada.

        Raises
        ------
        SesionNotFoundError
            Si no se encuentra una sesión con el ID proporcionado.
        SesionValidationError
            Si el local especificado no existe.
        SesionConflictError
            Si hay un conflicto al actualizar la sesión.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = sesion_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la sesión actual
            return await self.get_sesion_by_id(sesion_id)

        # Validar id_local si se proporciona
        if "id_local" in update_data:
            local = await self.local_repository.get_by_id(update_data["id_local"])
            if not local:
                raise SesionValidationError(
                    f"El local con ID '{update_data['id_local']}' no existe"
                )

        # Validar id_domotica si se proporciona
        if "id_domotica" in update_data:
            if not update_data["id_domotica"] or update_data["id_domotica"].strip() == "":
                raise SesionValidationError("El id_domotica no puede estar vacío")

        try:
            # Actualizar la sesión
            updated_sesion = await self.repository.update(sesion_id, **update_data)

            # Verificar si la sesión fue encontrada
            if not updated_sesion:
                raise SesionNotFoundError(f"No se encontró la sesión con ID {sesion_id}")

            # Convertir y retornar como esquema de respuesta
            return SesionResponse.model_validate(updated_sesion)
        except IntegrityError as e:
            raise SesionConflictError(f"Error al actualizar la sesión: {str(e)}")
