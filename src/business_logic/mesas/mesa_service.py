"""
Servicio para la gestión de mesas en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.mesa_repository import MesaRepository
from src.models.mesas.mesa_model import MesaModel
from src.api.schemas.mesa_schema import (
    MesaCreate,
    MesaUpdate,
    MesaResponse,
    MesaSummary,
    MesaList,
)
from src.api.schemas.mesa_schema_detalle import MesaDetalleResponse
from src.api.schemas.local_schema import LocalResponse
from src.business_logic.exceptions.mesa_exceptions import (
    MesaValidationError,
    MesaNotFoundError,
    MesaConflictError,
)


class MesaService:
    async def batch_create_mesas(self, mesas_data: list[MesaCreate]) -> list[MesaResponse]:
        """
        Crea múltiples mesas en una sola operación batch.

        Parameters
        ----------
        mesas_data : list[MesaCreate]
            Lista de datos para crear las mesas.

        Returns
        -------
        list[MesaResponse]
            Lista de esquemas de respuesta con los datos de las mesas creadas.
        """
        mesas_models = [
            MesaModel(
                numero=mesa.numero,
                capacidad=mesa.capacidad,
                id_zona=mesa.id_zona,
                estado=mesa.estado
            )
            for mesa in mesas_data
        ]
        created_mesas = await self.repository.batch_insert(mesas_models)
        return [MesaResponse.model_validate(mesa) for mesa in created_mesas]

    async def batch_delete_mesas(self, mesa_ids: list[str]) -> int:
        """
        Elimina múltiples mesas por sus IDs en una sola operación batch.

        Parameters
        ----------
        mesa_ids : list[UUID]
            Lista de IDs de las mesas a eliminar.

        Returns
        -------
        int
            Número de mesas eliminadas.
        """
        deleted_count = await self.repository.batch_delete(mesa_ids)
        return deleted_count
    """Servicio para la gestión de mesas en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con mesas, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : MesaRepository
        Repositorio para acceso a datos de mesas.
    """    


    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = MesaRepository(session)

    async def create_mesa(self, mesa_data: MesaCreate) -> MesaResponse:
        """
        Crea una nueva mesa en el sistema.

        Parameters
        ----------
        mesa_data : MesaCreate
            Datos para crear la nueva mesa.

        Returns
        -------
        MesaResponse
            Esquema de respuesta con los datos de la mesa creada.

        Raises
        ------
        MesaConflictError
            Si ya existe una mesa con el mismo nombre.
        """
        try:
            # Crear modelo de mesa desde los datos
            mesa = MesaModel(
                numero=mesa_data.numero,
                capacidad=mesa_data.capacidad,
                id_zona=mesa_data.id_zona,
                estado=mesa_data.estado
            )

            # Persistir en la base de datos
            created_mesa = await self.repository.create(mesa)

            # Convertir y retornar como esquema de respuesta
            return MesaResponse.model_validate(created_mesa)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            raise MesaConflictError(
                f"Ya existe una mesa con el número '{mesa_data.numero}'"
            )

    async def get_mesa_by_id(self, mesa_id: str) -> MesaDetalleResponse:
        """
        Obtiene una mesa por su ID con datos de zona y local.

        Parameters
        ----------
        mesa_id : UUID
            Identificador único de la mesa a buscar.

        Returns
        -------
        MesaDetalleResponse
            Esquema de respuesta con los datos de la mesa, zona y local.

        Raises
        ------
        MesaNotFoundError
            Si no se encuentra una mesa con el ID proporcionado.
        """
        # Buscar la mesa por su ID
        mesa = await self.repository.get_by_id(mesa_id)

        # Verificar si existe
        if not mesa:
            raise MesaNotFoundError(f"No se encontró la mesa con ID {mesa_id}")

        # Preparar datos completos con zona y local
        mesa_dict = mesa.to_dict()

        # Agregar datos de zona si existe
        if mesa.zona:
            mesa_dict["zona"] = mesa.zona.to_dict()
            # Agregar datos de local si la zona tiene local
            if mesa.zona.local:
                mesa_dict["local"] = mesa.zona.local.to_dict()
            else:
                mesa_dict["local"] = None
        else:
            mesa_dict["zona"] = None
            mesa_dict["local"] = None

        # Convertir y retornar como esquema de respuesta detallado
        return MesaDetalleResponse(**mesa_dict)

    async def delete_mesa(self, mesa_id: str) -> bool:
        """
        Elimina una mesa por su ID.

        Parameters
        ----------
        mesa_id : UUID
            Identificador único de la mesa a eliminar.

        Returns
        -------
        bool
            True si la mesa fue eliminada correctamente.

        Raises
        ------
        MesaNotFoundError
            Si no se encuentra una mesa con el ID proporcionado.
        """
        # Verificar primero si la mesa existe
        mesa = await self.repository.get_by_id(mesa_id)
        if not mesa:
            raise MesaNotFoundError(f"No se encontró la mesa con ID {mesa_id}")

        # Eliminar la mesa
        result = await self.repository.delete(mesa_id)
        return result

    async def get_mesas(self, skip: int = 0, limit: int = 100) -> MesaList:
        """
        Obtiene una lista paginada de mesas.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        MesaList
            Esquema con la lista de mesas y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise MesaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise MesaValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener mesas desde el repositorio con local eager-loaded
        mesas, total = await self.repository.get_all_with_local(skip, limit)

        # Convertir modelos a esquemas de resumen con local
        mesa_summaries = []
        for mesa in mesas:
            mesa_dict = MesaSummary.model_validate(mesa).model_dump()
            # Agregar local si la mesa tiene zona
            if mesa.zona and mesa.zona.local:
                mesa_dict['local'] = LocalResponse.model_validate(mesa.zona.local)
            mesa_summaries.append(MesaSummary.model_validate(mesa_dict))

        # Retornar esquema de lista
        return MesaList(items=mesa_summaries, total=total)

    async def update_mesa(self, mesa_id: str, mesa_data: MesaUpdate) -> MesaResponse:
        """
        Actualiza una mesa existente.

        Parameters
        ----------
        mesa_id : UUID
            Identificador único de la mesa a actualizar.
        mesa_data : MesaUpdate
            Datos para actualizar la mesa.

        Returns
        -------
        MesaResponse
            Esquema de respuesta con los datos de la mesa actualizada.

        Raises
        ------
        MesaNotFoundError
            Si no se encuentra una mesa con el ID proporcionado.
        MesaConflictError
            Si ya existe otra mesa con el mismo nombre.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = mesa_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la mesa actual
            return await self.get_mesa_by_id(mesa_id)

        try:
            # Actualizar la mesa
            updated_mesa = await self.repository.update(mesa_id, **update_data)

            # Verificar si la mesa fue encontrada
            if not updated_mesa:
                raise MesaNotFoundError(f"No se encontró la mesa con ID {mesa_id}")

            # Convertir y retornar como esquema de respuesta
            return MesaResponse.model_validate(updated_mesa)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            if "nombre" in update_data:
                raise MesaConflictError(
                    f"Ya existe una mesa con el nombre '{update_data['nombre']}'"
                )
            # Si no es por nombre, reenviar la excepción original
            raise

    async def get_local_by_mesa(self, mesa_id: str) -> LocalResponse:
        """
        Obtiene el local asociado a una mesa (via zona).

        Parameters
        ----------
        mesa_id : str
            ID de la mesa.

        Returns
        -------
        LocalResponse
            Esquema de respuesta con los datos del local.

        Raises
        ------
        MesaNotFoundError
            Si no se encuentra la mesa.
        MesaValidationError
            Si la mesa no tiene zona o la zona no tiene local asignado.
        """
        # Primero verificar que la mesa existe
        mesa = await self.repository.get_by_id(mesa_id)
        if not mesa:
            raise MesaNotFoundError(f"No se encontró la mesa con ID {mesa_id}")

        # Obtener el local via repository
        local = await self.repository.get_local_by_mesa_id(mesa_id)

        if not local:
            raise MesaValidationError(
                f"La mesa {mesa_id} no tiene un local asignado (debe estar asociada a una zona con local)"
            )

        return LocalResponse.model_validate(local)