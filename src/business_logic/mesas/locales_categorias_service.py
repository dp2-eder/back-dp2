"""
Servicio para la gestión de relaciones Local-Categoría.
"""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.mesas.locales_categorias_repository import LocalesCategoriasRepository
from src.repositories.menu.categoria_repository import CategoriaRepository
from src.repositories.mesas.local_repository import LocalRepository
from src.models.mesas.locales_categorias_model import LocalesCategoriasModel
from src.api.schemas.locales_categorias_schema import (
    LocalesCategoriasCreate,
    LocalesCategoriasUpdate,
    LocalesCategoriasResponse,
    LocalesCategoriasSummary,
    LocalesCategoriasListResponse,
    ActivarCategoriaRequest,
    ActivarCategoriasLoteRequest,
    OperacionLoteResponse,
)
from src.business_logic.exceptions.categoria_exceptions import CategoriaNotFoundError
from src.business_logic.exceptions.local_exceptions import LocalNotFoundError


class LocalesCategoriasConflictError(Exception):
    """Excepción para conflictos en relaciones local-categoría."""
    pass


class LocalesCategoriasNotFoundError(Exception):
    """Excepción cuando no se encuentra una relación local-categoría."""
    pass


class LocalesCategoriasService:
    """Servicio para la gestión de relaciones Local-Categoría.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con la activación y configuración de categorías por local.

    Attributes
    ----------
    repository : LocalesCategoriasRepository
        Repositorio para acceso a datos de relaciones local-categoría.
    categoria_repository : CategoriaRepository
        Repositorio para validar existencia de categorías.
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
        self.repository = LocalesCategoriasRepository(session)
        self.categoria_repository = CategoriaRepository(session)
        self.local_repository = LocalRepository(session)

    async def create_relacion(
        self, relacion_data: LocalesCategoriasCreate
    ) -> LocalesCategoriasResponse:
        """
        Crea una nueva relación local-categoría.

        Parameters
        ----------
        relacion_data : LocalesCategoriasCreate
            Datos para crear la relación.

        Returns
        -------
        LocalesCategoriasResponse
            Esquema de respuesta con los datos de la relación creada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        CategoriaNotFoundError
            Si no existe la categoría especificada.
        LocalesCategoriasConflictError
            Si ya existe la relación.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(relacion_data.id_local)
        if not local:
            raise LocalNotFoundError(
                f"No se encontró el local con ID {relacion_data.id_local}"
            )

        # Validar que la categoría existe
        categoria = await self.categoria_repository.get_by_id(relacion_data.id_categoria)
        if not categoria:
            raise CategoriaNotFoundError(
                f"No se encontró la categoría con ID {relacion_data.id_categoria}"
            )

        try:
            # Crear modelo desde los datos
            relacion = LocalesCategoriasModel(
                id_local=relacion_data.id_local,
                id_categoria=relacion_data.id_categoria,
                activo=relacion_data.activo,
                orden_override=relacion_data.orden_override,
            )

            # Persistir en la base de datos
            created_relacion = await self.repository.create(relacion)

            # Convertir y retornar como esquema de respuesta
            return LocalesCategoriasResponse.model_validate(created_relacion)
        except IntegrityError:
            raise LocalesCategoriasConflictError(
                f"Ya existe una relación entre el local {relacion_data.id_local} "
                f"y la categoría {relacion_data.id_categoria}"
            )

    async def get_relacion_by_id(self, relacion_id: str) -> LocalesCategoriasResponse:
        """
        Obtiene una relación por su ID.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.

        Returns
        -------
        LocalesCategoriasResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        LocalesCategoriasNotFoundError
            Si no se encuentra la relación.
        """
        relacion = await self.repository.get_by_id(relacion_id)

        if not relacion:
            raise LocalesCategoriasNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        return LocalesCategoriasResponse.model_validate(relacion)

    async def get_categorias_by_local(
        self,
        id_local: str,
        activo: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> LocalesCategoriasListResponse:
        """
        Obtiene todas las categorías configuradas para un local.

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
        LocalesCategoriasListResponse
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

        relaciones, total = await self.repository.get_categorias_by_local(
            id_local, activo, skip, limit
        )

        items = [LocalesCategoriasSummary.model_validate(r) for r in relaciones]

        return LocalesCategoriasListResponse(items=items, total=total)

    async def update_relacion(
        self, relacion_id: str, relacion_data: LocalesCategoriasUpdate
    ) -> LocalesCategoriasResponse:
        """
        Actualiza una relación local-categoría existente.

        Parameters
        ----------
        relacion_id : str
            Identificador único de la relación.
        relacion_data : LocalesCategoriasUpdate
            Datos a actualizar.

        Returns
        -------
        LocalesCategoriasResponse
            Esquema de respuesta con los datos actualizados.

        Raises
        ------
        LocalesCategoriasNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        existing = await self.repository.get_by_id(relacion_id)
        if not existing:
            raise LocalesCategoriasNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        # Actualizar solo los campos proporcionados
        update_data = relacion_data.model_dump(exclude_unset=True)
        updated_relacion = await self.repository.update(relacion_id, **update_data)

        return LocalesCategoriasResponse.model_validate(updated_relacion)

    async def delete_relacion(self, relacion_id: str) -> bool:
        """
        Elimina una relación local-categoría.

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
        LocalesCategoriasNotFoundError
            Si no se encuentra la relación.
        """
        # Verificar que existe
        relacion = await self.repository.get_by_id(relacion_id)
        if not relacion:
            raise LocalesCategoriasNotFoundError(
                f"No se encontró la relación con ID {relacion_id}"
            )

        result = await self.repository.delete(relacion_id)
        return result

    async def activar_categoria(
        self, id_local: str, request: ActivarCategoriaRequest
    ) -> LocalesCategoriasResponse:
        """
        Activa una categoría para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarCategoriaRequest
            Datos de la categoría a activar.

        Returns
        -------
        LocalesCategoriasResponse
            Relación creada o actualizada.

        Raises
        ------
        LocalNotFoundError
            Si no existe el local especificado.
        CategoriaNotFoundError
            Si no existe la categoría especificada.
        """
        # Validar que el local existe
        local = await self.local_repository.get_by_id(id_local)
        if not local:
            raise LocalNotFoundError(f"No se encontró el local con ID {id_local}")

        # Validar que la categoría existe
        categoria = await self.categoria_repository.get_by_id(request.id_categoria)
        if not categoria:
            raise CategoriaNotFoundError(
                f"No se encontró la categoría con ID {request.id_categoria}"
            )

        # Activar o actualizar la relación
        relacion = await self.repository.activate_categoria_for_local(
            id_local, request.id_categoria, request.orden_override
        )

        return LocalesCategoriasResponse.model_validate(relacion)

    async def desactivar_categoria(
        self, id_local: str, id_categoria: str
    ) -> LocalesCategoriasResponse:
        """
        Desactiva una categoría para un local específico.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        id_categoria : str
            Identificador de la categoría.

        Returns
        -------
        LocalesCategoriasResponse
            Relación actualizada.

        Raises
        ------
        LocalesCategoriasNotFoundError
            Si no existe la relación.
        """
        relacion = await self.repository.deactivate_categoria_for_local(
            id_local, id_categoria
        )

        if not relacion:
            raise LocalesCategoriasNotFoundError(
                f"No existe una relación entre el local {id_local} "
                f"y la categoría {id_categoria}"
            )

        return LocalesCategoriasResponse.model_validate(relacion)

    async def activar_categorias_lote(
        self, id_local: str, request: ActivarCategoriasLoteRequest
    ) -> OperacionLoteResponse:
        """
        Activa múltiples categorías para un local en una sola operación.

        Parameters
        ----------
        id_local : str
            Identificador del local.
        request : ActivarCategoriasLoteRequest
            Lista de categorías a activar.

        Returns
        -------
        OperacionLoteResponse
            Resultado de la operación batch.
        """
        exitosos = 0
        fallidos = 0
        detalles = []

        for cat_request in request.categorias:
            try:
                relacion = await self.activar_categoria(id_local, cat_request)
                detalles.append(relacion)
                exitosos += 1
            except Exception:
                fallidos += 1

        return OperacionLoteResponse(
            exitosos=exitosos, fallidos=fallidos, detalles=detalles
        )
