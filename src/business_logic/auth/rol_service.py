"""
Servicio para la gestión de roles en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.auth.rol_repository import RolRepository
from src.repositories.auth.usuario_repository import UsuarioRepository
from src.models.auth.rol_model import RolModel
from src.api.schemas.rol_schema import (
    RolCreate,
    RolUpdate,
    RolResponse,
    RolSummary,
    RolList,
)
from src.business_logic.exceptions.rol_exceptions import (
    RolValidationError,
    RolNotFoundError,
    RolConflictError,
)


class RolService:
    """Servicio para la gestión de roles en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con roles, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : RolRepository
        Repositorio para acceso a datos de roles.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = RolRepository(session)
        self.usuario_repository = UsuarioRepository(session)

    async def create_rol(self, rol_data: RolCreate) -> RolResponse:
        """
        Crea un nuevo rol en el sistema.
        
        Parameters
        ----------
        rol_data : RolCreate
            Datos para crear el nuevo rol.

        Returns
        -------
        RolResponse
            Esquema de respuesta con los datos del rol creado.

        Raises
        ------
        RolConflictError
            Si ya existe un rol con el mismo nombre.
        """
        try:
            # Crear modelo de rol desde los datos
            rol = RolModel(nombre=rol_data.nombre, descripcion=rol_data.descripcion)

            # Persistir en la base de datos
            created_rol = await self.repository.create(rol)

            # Convertir y retornar como esquema de respuesta
            return RolResponse.model_validate(created_rol)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            raise RolConflictError(
                f"Ya existe un rol con el nombre '{rol_data.nombre}'"
            )

    async def get_rol_by_id(self, rol_id: str) -> RolResponse:
        """
        Obtiene un rol por su ID.

        Parameters
        ----------
        rol_id : str
            Identificador único del rol a buscar (ULID).

        Returns
        -------
        RolResponse
            Esquema de respuesta con los datos del rol.

        Raises
        ------
        RolNotFoundError
            Si no se encuentra un rol con el ID proporcionado.
        """
        # Buscar el rol por su ID
        rol = await self.repository.get_by_id(rol_id)

        # Verificar si existe
        if not rol:
            raise RolNotFoundError(f"No se encontró el rol con ID {rol_id}")

        # Convertir y retornar como esquema de respuesta
        return RolResponse.model_validate(rol)

    async def delete_rol(self, rol_id: str) -> bool:
        """
        Elimina un rol por su ID.
        
        Parameters
        ----------
        rol_id : str
            Identificador único del rol a eliminar (ULID).

        Returns
        -------
        bool
            True si el rol fue eliminado correctamente.

        Raises
        ------
        RolNotFoundError
            Si no se encuentra un rol con el ID proporcionado.
        """
        # Verificar primero si el rol existe
        rol = await self.repository.get_by_id(rol_id)
        if not rol:
            raise RolNotFoundError(f"No se encontró el rol con ID {rol_id}")

        # Eliminar el rol
        result = await self.repository.delete(rol_id)
        return result

    async def get_roles(self, skip: int = 0, limit: int = 100) -> RolList:
        """
        Obtiene una lista paginada de roles.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        RolList
            Esquema con la lista de roles y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise RolValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise RolValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener roles desde el repositorio
        roles, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        rol_summaries = [RolSummary.model_validate(rol) for rol in roles]

        # Retornar esquema de lista
        return RolList(items=rol_summaries, total=total)

    async def update_rol(self, rol_id: str, rol_data: RolUpdate) -> RolResponse:
        """
        Actualiza un rol existente.

        Parameters
        ----------
        rol_id : str
            Identificador único del rol a actualizar (ULID).
        rol_data : RolUpdate
            Datos para actualizar el rol.

        Returns
        -------
        RolResponse
            Esquema de respuesta con los datos del rol actualizado.

        Raises
        ------
        RolNotFoundError
            Si no se encuentra un rol con el ID proporcionado.
        RolConflictError
            Si ya existe otro rol con el mismo nombre.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = rol_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el rol actual
            return await self.get_rol_by_id(rol_id)

        try:
            # Actualizar el rol
            updated_rol = await self.repository.update(rol_id, **update_data)

            # Verificar si el rol fue encontrado
            if not updated_rol:
                raise RolNotFoundError(f"No se encontró el rol con ID {rol_id}")

            # Convertir y retornar como esquema de respuesta
            return RolResponse.model_validate(updated_rol)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            if "nombre" in update_data:
                raise RolConflictError(
                    f"Ya existe un rol con el nombre '{update_data['nombre']}'"
                )
            # Si no es por nombre, reenviar la excepción original
            raise

    async def get_nombre_rol_by_usuario_id(self, usuario_id: str) -> dict:
        """
        Obtiene el nombre del rol de un usuario por su ID.

        Parameters
        ----------
        usuario_id : str
            Identificador único del usuario (ULID).

        Returns
        -------
        dict
            Diccionario con el nombre del rol: {"nombre_rol": "COMENSAL"}

        Raises
        ------
        RolNotFoundError
            Si no se encuentra el usuario, no tiene rol asignado, o el rol no existe.
        """
        # Buscar el usuario por su ID
        usuario = await self.usuario_repository.get_by_id(usuario_id)
        if not usuario:
            raise RolNotFoundError(f"No se encontró el usuario con ID {usuario_id}")

        # Verificar que el usuario tenga un rol asignado
        if not usuario.id_rol:
            raise RolNotFoundError(f"El usuario con ID {usuario_id} no tiene un rol asignado")

        # Buscar el rol por su ID
        rol = await self.repository.get_by_id(usuario.id_rol)
        if not rol:
            raise RolNotFoundError(f"No se encontró el rol con ID {usuario.id_rol}")

        # Retornar solo el nombre del rol
        return {"nombre_rol": rol.nombre}
