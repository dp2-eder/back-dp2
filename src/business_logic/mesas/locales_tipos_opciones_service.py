"""
Servicio para la gestión de relaciones Local-TipoOpcion.
"""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.locales_tipos_opciones_repository import (
    LocalesTiposOpcionesRepository,
)
from src.repositories.pedidos.tipo_opciones_repository import TipoOpcionRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.locales_tipos_opciones_model import LocalesTiposOpcionesModel
from src.api.schemas.locales_tipos_opciones_schema import (
    LocalesTiposOpcionesCreate,
    LocalesTiposOpcionesUpdate,
    LocalesTiposOpcionesResponse,
    LocalesTiposOpcionesSummary,
    LocalesTiposOpcionesListResponse,
    ActivarTipoOpcionRequest,
    ActivarTiposOpcionesLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.tipo_opciones_exceptions import TipoOpcionNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError


class LocalesTiposOpcionesConflictError(Exception):
    """Excepción para conflictos en relaciones local-tipo_opcion."""
    pass


class LocalesTiposOpcionesNotFoundError(Exception):
    """Excepción cuando no se encuentra una relación local-tipo_opcion."""
    pass


class LocalesTiposOpcionesService:
    """Servicio para la gestión de relaciones Local-TipoOpcion.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con la activación y configuración de tipos de opciones por local.

    Attributes
    ----------
    repository : LocalesTiposOpcionesRepository
        Repositorio para acceso a datos de relaciones local-tipo_opcion.
    tipo_opcion_repository : TipoOpcionRepository
        Repositorio para validar existencia de tipos de opciones.
    local_repository : LocalRepository
        Repositorio para validar existencia de locales.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy.
        """
        self.repository = LocalesTiposOpcionesRepository(session)
        self.tipo_opcion_repository = TipoOpcionRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_relacion(
        self, relacion_data: LocalesTiposOpcionesCreate
    ) -> LocalesTiposOpcionesResponse:
        """
        Crea una nueva relación local-tipo_opcion.

        Parameters
        ----------
        relacion_data : LocalesTiposOpcionesCreate
            Datos para crear la relación.

        Returns
        -------
        LocalesTiposOpcionesResponse
            Esquema de respuesta con los datos de la relación creada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        TipoOpcionNotFoundError
            Si no existe el tipo de opción especificado.
        LocalesTiposOpcionesConflictError
            Si ya existe la relación.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(relacion_data.id_local)
        if not local:
            raise LocalNotFoundError(
                f"No se encontró el local con ID {relacion_data.id_local}"
            )

        # Validar que el tipo de opción existe
        tipo_opcion = await self.tipo_opcion_repository.get_by_id(
            relacion_data.id_tipo_opcion
        )
        if not tipo_opcion:
            raise TipoOpcionNotFoundError(
                f"No se encontró el tipo de opción con ID {relacion_data.id_tipo_opcion}"
            )

        try:
            # Crear modelo desde los datos
            relacion = LocalesTiposOpcionesModel(
                id_local=relacion_data.id_local,
                id_tipo_opcion=relacion_data.id_tipo_opcion,
                activo=relacion_data.activo,
            )

            # Persistir en la base de datos
            created_relacion = await self.repository.create(relacion)

            # Convertir y retornar como esquema de respuesta
            return LocalesTiposOpcionesResponse.model_validate(created_relacion)
        except IntegrityError:
            raise LocalesTiposOpcionesConflictError(
                f"Ya existe una relación entre el local {relacion_data.id_local} "
                f"y el tipo de opción {relacion_data.id_tipo_opcion}"
            )

    async def get_relacion_by_id(
        self, relacion_id: str
    ) -> LocalesTiposOpcionesResponse:
        """
        Obtiene una relación por su ID.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        LocalesTiposOpcionesResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        LocalesTiposOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        relacion = await self.repository.get_by_id(relacion_id)

        if not relacion:
            raise LocalesTiposOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        return LocalesTiposOpcionesResponse.model_validate(relacion)

    async def get_tipos_opciones_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> LocalesTiposOpcionesListResponse:
        """
        Obtiene todos los tipos de opciones configurados para un local.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        activo : Optional[bool], optional
            Filtrar por estado activo/inactivo.
        skip : int, optional
            Número de registros a omitir, por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        LocalesTiposOpcionesListResponse
            Lista paginada de relaciones.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        relaciones, total = await self.repository.get_tipos_opciones_by_local(
            id_local, activo, skip, limit
        )

        items = [LocalesTiposOpcionesSummary.model_validate(r) for r in relaciones]

        return LocalesTiposOpcionesListResponse(items=items, total=total)

    async def update_relacion(
        self, relacion_id: str, relacion_data: LocalesTiposOpcionesUpdate
    ) -> LocalesTiposOpcionesResponse:
        """
        Actualiza una relación local-tipo_opcion existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        relacion_data : LocalesTiposOpcionesUpdate
            Datos a actualizar.

        Returns
        -------
        LocalesTiposOpcionesResponse
            Esquema de respuesta con los datos actualizados.

        Raises
        ------
        LocalesTiposOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        existing = await self.repository.get_by_id(relacion_id)
        if not existing:
            raise LocalesTiposOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        # Actualizar solo los campos proporcionados
        update_data = relacion_data.model_dump(exclude_unset=True)
        updated_relacion = await self.repository.update(relacion_id, **update_data)

        return LocalesTiposOpcionesResponse.model_validate(updated_relacion)

    async def delete_relacion(self, relacion_id: str) -> bool:
        """
        Elimina una relación local-tipo_opcion.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        bool
            True si fue eliminada correctamente.

        Raises
        ------
        LocalesTiposOpcionesNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        relacion = await self.repository.get_by_id(relacion_id)
        if not relacion:
            raise LocalesTiposOpcionesNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        result = await self.repository.delete(relacion_id)
        return result

    async def activar_tipo_opcion(
        self, id_local: str, request: ActivarTipoOpcionRequest
    ) -> LocalesTiposOpcionesResponse:
        """
        Activa un tipo de opción para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarTipoOpcionRequest
            Datos del tipo de opción a activar.

        Returns
        -------
        LocalesTiposOpcionesResponse
            Relación creada o actualizada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        TipoOpcionNotFoundError
            Si no existe el tipo de opción especificado.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        # Validar que el tipo de opción existe
        tipo_opcion = await self.tipo_opcion_repository.get_by_id(
            request.id_tipo_opcion
        )
        if not tipo_opcion:
            raise TipoOpcionNotFoundError(
                f"No se encontró el tipo de opción con ID {request.id_tipo_opcion}"
            )

        # Activar o actualizar la relación
        relacion = await self.repository.activate_tipo_opcion_for_local(
            id_local, request.id_tipo_opcion
        )

        return LocalesTiposOpcionesResponse.model_validate(relacion)

    async def desactivar_tipo_opcion(
        self, id_local: str, id_tipo_opcion: str
    ) -> LocalesTiposOpcionesResponse:
        """
        Desactiva un tipo de opción para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_tipo_opcion : str
            Identificador del tipo de opción.

        Returns
        -------
        LocalesTiposOpcionesResponse
            Relación actualizada.

        Raises
        ------
        LocalesTiposOpcionesNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.deactivate_tipo_opcion_for_local(
            id_local, id_tipo_opcion
        )

        if not relacion:
            raise LocalesTiposOpcionesNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y el tipo de opción {id_tipo_opcion}"
            )

        return LocalesTiposOpcionesResponse.model_validate(relacion)

    async def activar_tipos_opciones_lote(
        self, id_local: str, request: ActivarTiposOpcionesLoteRequest
    ) -> OperacionLoteResponse:
        """
        Activa múltiples tipos de opciones para un local en una sola operación.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarTiposOpcionesLoteRequest
            Lista de tipos de opciones a activar.

        Returns
        -------
        OperacionLoteResponse
            Resultado de la operación batch.
        """
        exitosos = 0
        fallidos = 0
        detalles = []

        for tipo_request in request.tipos_opciones:
            try:
                relacion = await self.activar_tipo_opcion(id_local, tipo_request)
                detalles.append(relacion)
                exitosos += 1
            except Exception:
                fallidos += 1

        return OperacionLoteResponse(
            exitosos=exitosos, fallidos=fallidos, detalles=detalles
        )
