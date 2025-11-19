"""
Servicio para la gestión de locales en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.local_model import LocalModel
from src.api.schemas.local_schema import (
    LocalCreate,
    LocalUpdate,
    LocalResponse,
    LocalSummary,
    LocalList,
)
from src.business_logic.exceptions.local_exceptions import (
    LocalValidationError,
    LocalNotFoundError,
    LocalConflictError,
)


class LocalService:
    """Servicio para la gestión de locales en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con locales, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : LocalRepository
        Repositorio para acceso a datos de locales.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = LocalRepository(session)

    async def create_local(self, local_data: LocalCreate) -> LocalResponse:
        """
        Crea un nuevo local en el sistema.

        Parameters
        ----------
        local_data : LocalCreate
            Datos para crear el nuevo local.

        Returns
        -------
        LocalResponse
            Esquema de respuesta con los datos del local creado.

        Raises
        ------
        LocalConflictError
            Si ya existe un local con el mismo código.
        """
        try:
            # Crear modelo de local desde los datos
            local = LocalModel(
                codigo=local_data.codigo,
                nombre=local_data.nombre,
                direccion=local_data.direccion,
                distrito=local_data.distrito,
                ciudad=local_data.ciudad,
                telefono=local_data.telefono,
                email=local_data.email,
                tipo_local=local_data.tipo_local,
                capacidad_total=local_data.capacidad_total,
                fecha_apertura=local_data.fecha_apertura,
            )

            # Persistir en la base de datos
            created_local = await self.repository.create(local)

            # Convertir y retornar como esquema de respuesta
            return LocalResponse.model_validate(created_local)
        except IntegrityError:
            # Capturar errores de integridad (código duplicado)
            raise LocalConflictError(
                f"Ya existe un local con el código '{local_data.codigo}'"
            )

    async def get_local_by_id(self, local_id: str) -> LocalResponse:
        """
        Obtiene un local por su ID.

        Parameters
        ----------
        local_id : str
            Identificador único del local a buscar (ULID).

        Returns
        -------
        LocalResponse
            Esquema de respuesta con los datos del local.

        Raises
        ------
        LocalNotFoundError
            Si no se encuentra un local con el ID proporcionado.
        """
        # Buscar el local por su ID
        local = await self.repository.get_by_id(local_id)

        # Verificar si existe
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {local_id}")

        # Convertir y retornar como esquema de respuesta
        return LocalResponse.model_validate(local)

    async def get_local_by_codigo(self, codigo: str) -> LocalResponse:
        """
        Obtiene un local por su código único.

        Parameters
        ----------
        codigo : str
            Código único del local a buscar (ej: CEV-001).

        Returns
        -------
        LocalResponse
            Esquema de respuesta con los datos del local.

        Raises
        ------
        LocalNotFoundError
            Si no se encuentra un local con el código proporcionado.
        """
        # Buscar el local por su código
        local = await self.repository.get_by_codigo(codigo)

        # Verificar si existe
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con código '{codigo}'")

        # Convertir y retornar como esquema de respuesta
        return LocalResponse.model_validate(local)

    async def delete_local(self, local_id: str) -> bool:
        """
        Elimina un local por su ID.

        Parameters
        ----------
        local_id : str
            Identificador único del local a eliminar (ULID).

        Returns
        -------
        bool
            True si el local fue eliminado correctamente.

        Raises
        ------
        LocalNotFoundError
            Si no se encuentra un local con el ID proporcionado.
        """
        # Verificar primero si el local existe
        local = await self.repository.get_by_id(local_id)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {local_id}")

        # Eliminar el local
        result = await self.repository.delete(local_id)
        return result

    async def get_locales(self, skip: int = 0, limit: int = 100) -> LocalList:
        """
        Obtiene una lista paginada de locales.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        LocalList
            Esquema con la lista de locales y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise LocalValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise LocalValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener locales desde el repositorio
        locales, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        local_summaries = [LocalSummary.model_validate(local) for local in locales]

        # Retornar esquema de lista
        return LocalList(items=local_summaries, total=total)

    async def update_local(self, local_id: str, local_data: LocalUpdate) -> LocalResponse:
        """
        Actualiza un local existente.

        Parameters
        ----------
        local_id : str
            Identificador único del local a actualizar (ULID).
        local_data : LocalUpdate
            Datos para actualizar el local.

        Returns
        -------
        LocalResponse
            Esquema de respuesta con los datos del local actualizado.

        Raises
        ------
        LocalNotFoundError
            Si no se encuentra un local con el ID proporcionado.
        LocalConflictError
            Si ya existe otro local con el mismo código.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = local_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el local actual
            return await self.get_local_by_id(local_id)

        try:
            # Actualizar el local
            updated_local = await self.repository.update(local_id, **update_data)

            # Verificar si el local fue encontrado
            if not updated_local:
                raise LocalNotFoundError(f"No se encontró el local con ID {local_id}")

            # Convertir y retornar como esquema de respuesta
            return LocalResponse.model_validate(updated_local)
        except IntegrityError:
            # Capturar errores de integridad (código duplicado)
            if "codigo" in update_data:
                raise LocalConflictError(
                    f"Ya existe un local con el código '{update_data['codigo']}'"
                )
            # Si no es por código, reenviar la excepción original
            raise
