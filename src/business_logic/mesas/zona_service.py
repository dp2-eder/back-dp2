"""
Servicio para la gestión de zonas en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.zona_repository import ZonaRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.zona_model import ZonaModel
from src.api.schemas.zona_schema import (
    ZonaCreate,
    ZonaUpdate,
    ZonaResponse,
    ZonaSummary,
    ZonaList,
)
from src.business_logic.exceptions.zona_exceptions import (
    ZonaValidationError,
    ZonaNotFoundError,
    ZonaConflictError,
)


class ZonaService:
    """Servicio para la gestión de zonas en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con zonas, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : ZonaRepository
        Repositorio para acceso a datos de zonas.
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
        self.repository = ZonaRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_zona(self, zona_data: ZonaCreate) -> ZonaResponse:
        """
        Crea una nueva zona en el sistema.

        Parameters
        ----------
        zona_data : ZonaCreate
            Datos para crear la nueva zona.

        Returns
        -------
        ZonaResponse
            Esquema de respuesta con los datos de la zona creada.

        Raises
        ------
        ZonaValidationError
            Si el local especificado no existe o el nivel es inválido.
        ZonaConflictError
            Si hay un conflicto al crear la zona.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(zona_data.id_local)
        if not local:
            raise ZonaValidationError(
                f"El local con ID '{zona_data.id_local}' no existe"
            )

        # Validar nivel jerárquico
        if zona_data.nivel not in [0, 1, 2]:
            raise ZonaValidationError(
                f"El nivel debe ser 0 (principal), 1 (sub-zona) o 2 (sub-sub-zona)"
            )

        try:
            # Crear modelo de zona desde los datos
            zona = ZonaModel(
                id_local=zona_data.id_local,
                nombre=zona_data.nombre,
                descripcion=zona_data.descripcion,
                nivel=zona_data.nivel,
                capacidad_maxima=zona_data.capacidad_maxima,
            )

            # Persistir en la base de datos
            created_zona = await self.repository.create(zona)

            # Convertir y retornar como esquema de respuesta
            return ZonaResponse.model_validate(created_zona)
        except IntegrityError as e:
            raise ZonaConflictError(f"Error al crear la zona: {str(e)}")

    async def get_zona_by_id(self, zona_id: str) -> ZonaResponse:
        """
        Obtiene una zona por su ID.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a buscar (ULID).

        Returns
        -------
        ZonaResponse
            Esquema de respuesta con los datos de la zona.

        Raises
        ------
        ZonaNotFoundError
            Si no se encuentra una zona con el ID proporcionado.
        """
        # Buscar la zona por su ID
        zona = await self.repository.get_by_id(zona_id)

        # Verificar si existe
        if not zona:
            raise ZonaNotFoundError(f"No se encontró la zona con ID {zona_id}")

        # Convertir y retornar como esquema de respuesta
        return ZonaResponse.model_validate(zona)

    async def get_zonas_by_local(
        self, local_id: str, skip: int = 0, limit: int = 100
    ) -> ZonaList:
        """
        Obtiene una lista paginada de zonas por local.

        Parameters
        ----------
        local_id : str
            ID del local para filtrar zonas.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        ZonaList
            Esquema con la lista de zonas y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ZonaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ZonaValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener zonas desde el repositorio
        zonas, total = await self.repository.get_by_local(local_id, skip, limit)

        # Convertir modelos a esquemas de resumen
        zona_summaries = []
        for zona in zonas:
            summary = ZonaSummary.model_validate(zona)
            # Agregar nombre del local si está disponible
            if zona.local:
                summary.nombre_local = zona.local.nombre
            zona_summaries.append(summary)

        # Retornar esquema de lista
        return ZonaList(items=zona_summaries, total=total)

    async def get_zonas_by_nivel(
        self, nivel: int, skip: int = 0, limit: int = 100
    ) -> ZonaList:
        """
        Obtiene una lista paginada de zonas por nivel jerárquico.

        Parameters
        ----------
        nivel : int
            Nivel jerárquico para filtrar zonas (0, 1, 2).
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        ZonaList
            Esquema con la lista de zonas y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ZonaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ZonaValidationError("El parámetro 'limit' debe ser mayor a cero")

        if nivel not in [0, 1, 2]:
            raise ZonaValidationError(
                "El nivel debe ser 0 (principal), 1 (sub-zona) o 2 (sub-sub-zona)"
            )

        # Obtener zonas desde el repositorio
        zonas, total = await self.repository.get_by_nivel(nivel, skip, limit)

        # Convertir modelos a esquemas de resumen
        zona_summaries = []
        for zona in zonas:
            summary = ZonaSummary.model_validate(zona)
            # Agregar nombre del local si está disponible
            if zona.local:
                summary.nombre_local = zona.local.nombre
            zona_summaries.append(summary)

        # Retornar esquema de lista
        return ZonaList(items=zona_summaries, total=total)

    async def delete_zona(self, zona_id: str) -> bool:
        """
        Elimina una zona por su ID.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a eliminar (ULID).

        Returns
        -------
        bool
            True si la zona fue eliminada correctamente.

        Raises
        ------
        ZonaNotFoundError
            Si no se encuentra una zona con el ID proporcionado.
        """
        # Verificar primero si la zona existe
        zona = await self.repository.get_by_id(zona_id)
        if not zona:
            raise ZonaNotFoundError(f"No se encontró la zona con ID {zona_id}")

        # Eliminar la zona
        result = await self.repository.delete(zona_id)
        return result

    async def get_zonas(self, skip: int = 0, limit: int = 100) -> ZonaList:
        """
        Obtiene una lista paginada de zonas.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        ZonaList
            Esquema con la lista de zonas y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ZonaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ZonaValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener zonas desde el repositorio
        zonas, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        zona_summaries = []
        for zona in zonas:
            summary = ZonaSummary.model_validate(zona)
            # Agregar nombre del local si está disponible
            if zona.local:
                summary.nombre_local = zona.local.nombre
            zona_summaries.append(summary)

        # Retornar esquema de lista
        return ZonaList(items=zona_summaries, total=total)

    async def update_zona(self, zona_id: str, zona_data: ZonaUpdate) -> ZonaResponse:
        """
        Actualiza una zona existente.

        Parameters
        ----------
        zona_id : str
            Identificador único de la zona a actualizar (ULID).
        zona_data : ZonaUpdate
            Datos para actualizar la zona.

        Returns
        -------
        ZonaResponse
            Esquema de respuesta con los datos de la zona actualizada.

        Raises
        ------
        ZonaNotFoundError
            Si no se encuentra una zona con el ID proporcionado.
        ZonaValidationError
            Si el local especificado no existe o el nivel es inválido.
        ZonaConflictError
            Si hay un conflicto al actualizar la zona.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = zona_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la zona actual
            return await self.get_zona_by_id(zona_id)

        # Validar id_local si se proporciona
        if "id_local" in update_data:
            local = await self.local_repository.get_by_id(update_data["id_local"])
            if not local:
                raise ZonaValidationError(
                    f"El local con ID '{update_data['id_local']}' no existe"
                )

        # Validar nivel si se proporciona
        if "nivel" in update_data and update_data["nivel"] not in [0, 1, 2]:
            raise ZonaValidationError(
                "El nivel debe ser 0 (principal), 1 (sub-zona) o 2 (sub-sub-zona)"
            )

        try:
            # Actualizar la zona
            updated_zona = await self.repository.update(zona_id, **update_data)

            # Verificar si la zona fue encontrada
            if not updated_zona:
                raise ZonaNotFoundError(f"No se encontró la zona con ID {zona_id}")

            # Convertir y retornar como esquema de respuesta
            return ZonaResponse.model_validate(updated_zona)
        except IntegrityError as e:
            raise ZonaConflictError(f"Error al actualizar la zona: {str(e)}")
