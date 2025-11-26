"""
Servicio para la gestión de categorías en el sistema.
"""

from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.menu.categoria_repository import CategoriaRepository
from src.repositories.mesas.mesa_repository import MesaRepository
from src.repositories.mesas.locales_categorias_repository import LocalesCategoriasRepository
from src.models.menu.categoria_model import CategoriaModel
from src.api.schemas.categoria_schema import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse,
    CategoriaSummary,
    CategoriaList,
    ProductoCardMinimal,
    CategoriaConProductosCard,
    CategoriaConProductosCardList,
)
from src.business_logic.exceptions.categoria_exceptions import (
    CategoriaValidationError,
    CategoriaNotFoundError,
    CategoriaConflictError,
)
from src.core.utils.text_utils import normalize_category_name, normalize_product_name


class CategoriaService:
    """Servicio para la gestión de categorías en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con categorías, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : CategoriaRepository
        Repositorio para acceso a datos de categorías.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.session = session
        self.repository = CategoriaRepository(session)
        self.mesa_repository = MesaRepository(session)
        self.locales_categorias_repository = LocalesCategoriasRepository(session)

    async def get_categorias(
        self,
        skip: int = 0,
        limit: int = 100,
        id_mesa: Optional[str] = None,
        id_local: Optional[str] = None
    ) -> CategoriaList:
        """
        Obtiene una lista paginada de categorías.

        Si se proporciona id_mesa o id_local, filtra categorías activas para ese local
        y aplica orden personalizado si existe.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_mesa : Optional[str], optional
            ID de mesa para filtrar categorías por su local.
        id_local : Optional[str], optional
            ID de local para filtrar categorías directamente.

        Returns
        -------
        CategoriaList
            Esquema con la lista de categorías y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise CategoriaValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise CategoriaValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Resolver local desde mesa si es necesario
        local_id = None

        if id_mesa:
            # Resolver: mesa → zona → local
            local = await self.mesa_repository.get_local_by_mesa_id(id_mesa)
            if local:
                local_id = local.id
            else:
                raise CategoriaValidationError(
                    f"La mesa {id_mesa} no tiene un local asignado"
                )
        elif id_local:
            local_id = id_local

        # Filtrar por local si tenemos uno
        if local_id:
            return await self._get_categorias_con_local(local_id, skip, limit)
        else:
            # Sin filtro - retornar todas las categorías
            categorias, total = await self.repository.get_all(skip, limit)

            # Normalizar nombres y convertir modelos a esquemas de resumen
            for categoria in categorias:
                categoria.nombre = normalize_category_name(categoria.nombre)
            categoria_summaries = [CategoriaSummary.model_validate(categoria) for categoria in categorias]

            # Retornar esquema de lista
            return CategoriaList(items=categoria_summaries, total=total)

    async def _get_categorias_con_local(
        self,
        id_local: str,
        skip: int,
        limit: int
    ) -> CategoriaList:
        """
        Obtiene categorías activas para un local con orden personalizado si existe.

        Parameters
        ----------
        id_local : str
            ID del local para filtrar.
        skip : int
            Número de registros a omitir.
        limit : int
            Número máximo de registros.

        Returns
        -------
        CategoriaList
            Lista de categorías activas para el local.
        """
        # Obtener relaciones local-categoría activas
        relaciones, total = await self.locales_categorias_repository.get_categorias_by_local(
            id_local,
            activo=True,
            skip=skip,
            limit=limit
        )

        # Cargar categorías completas y aplicar orden personalizado
        categorias_con_orden = []
        for relacion in relaciones:
            categoria = await self.repository.get_by_id(relacion.id_categoria)
            if categoria:
                # Normalizar nombre
                categoria.nombre = normalize_category_name(categoria.nombre)

                # Convertir a dict para modificar
                categoria_dict = CategoriaSummary.model_validate(categoria).model_dump()

                # Si hay orden_override, se puede incluir en metadata (opcional)
                # categoria_dict['orden_local'] = relacion.orden_override

                categorias_con_orden.append(CategoriaSummary.model_validate(categoria_dict))

        return CategoriaList(items=categorias_con_orden, total=total)

    async def batch_create_categorias(
        self, categorias_data: List[CategoriaCreate]
    ) -> List[CategoriaResponse]:
        """
        Crea múltiples categorías en una sola operación.

        Parameters
        ----------
        categorias_data : List[CategoriaCreate]
            Lista de datos para crear nuevas categorías.

        Returns
        -------
        List[CategoriaResponse]
            Lista de esquemas de respuesta con los datos de las categorías creadas.

        Raises
        ------
        CategoriaConflictError
            Si ya existe una categoría con alguno de los nombres proporcionados.
        """
        if not categorias_data:
            return []

        try:
            categoria_models = [
                CategoriaModel(
                    nombre=categoria_data.nombre,
                    descripcion=categoria_data.descripcion,
                    imagen_path=categoria_data.imagen_path,
                )
                for categoria_data in categorias_data
            ]
            created_categorias = await self.repository.batch_insert(categoria_models)
            # Normalizar nombres y convertir a esquemas de respuesta
            for categoria in created_categorias:
                categoria.nombre = normalize_category_name(categoria.nombre)
            return [
                CategoriaResponse.model_validate(categoria)
                for categoria in created_categorias
            ]
        except IntegrityError:
            raise CategoriaConflictError(
                "Una o más categorías ya existen con el mismo nombre"
            )

    async def get_categorias_con_productos_cards(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> CategoriaConProductosCardList:
        """
        Obtiene una lista de categorías con sus productos en formato minimal (solo id, nombre, imagen).

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        CategoriaConProductosCardList
            Lista de categorías con sus productos en formato minimal.
        """
        # Obtener categorías con productos eager-loaded
        categorias, total = await self.repository.get_all_with_productos(
            skip=skip,
            limit=limit,
            activo=True  # Solo categorías activas
        )

        # Construir la lista de categorías con productos
        items = []
        for categoria in categorias:
            # Normalizar el nombre de la categoría
            categoria_nombre_normalizado = normalize_category_name(categoria.nombre)
            
            # Construir lista de productos minimal (con nombres normalizados)
            productos_minimal = [
                ProductoCardMinimal(
                    id=producto.id,
                    nombre=normalize_product_name(producto.nombre),
                    imagen_path=producto.imagen_path
                )
                for producto in categoria.productos
            ]

            # Construir categoría con productos (usando nombre normalizado)
            categoria_card = CategoriaConProductosCard(
                id=categoria.id,
                nombre=categoria_nombre_normalizado,
                imagen_path=categoria.imagen_path,
                productos=productos_minimal
            )
            items.append(categoria_card)

        return CategoriaConProductosCardList(items=items, total=total)

    async def activate_categorias(self, ids: List[str]) -> int:
        """
        Activa una categoría por su ID.

        Parameters
        ----------
        categoria_id : str
            ID de la categoría a activar.

        Returns
        -------
        CategoriaResponse
            Esquema de respuesta con los datos de la categoría activada.

        Raises
        ------
        CategoriaNotFoundError
            Si no se encuentra la categoría con el ID proporcionado.
        """
        if not ids:
            return 0
        
        exist_all = await self.repository.exist_all_by_ids(ids)
        if not exist_all:
            raise CategoriaNotFoundError("No se encontraron algunas categorías para activar")

        return await self.repository.batch_update(ids, activo=True)
        
    async def deactivate_categorias(self, ids: List[str]) -> int:
        """
        Desactiva una categoría por su ID.

        Parameters
        ----------
        categoria_id : str
            ID de la categoría a desactivar.

        Returns
        -------
        CategoriaResponse
            Esquema de respuesta con los datos de la categoría desactivada.

        Raises
        ------
        CategoriaNotFoundError
            Si no se encuentra la categoría con el ID proporcionado.
        """
        if not ids:
            return 0
        
        exist_all = await self.repository.exist_all_by_ids(ids)
        if not exist_all:
            raise CategoriaNotFoundError("No se encontraron algunas categorías para desactivar")

        return await self.repository.batch_update(ids, activo=False)