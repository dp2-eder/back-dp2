from typing import List, Tuple, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.menu.producto_alergeno_repository import ProductoAlergenoRepository
from src.repositories.menu.producto_repository import ProductoRepository
from src.repositories.mesas.mesa_repository import MesaRepository
from src.repositories.mesas.locales_productos_repository import LocalesProductosRepository
from src.models.menu.producto_model import ProductoModel
from src.api.schemas.producto_schema import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse,
    ProductoSummary,
    ProductoList,
    ProductoCard,
    ProductoCardList,
    ProductoConOpcionesResponse,
    TipoOpcionConOpcionesSchema,
    ProductoOpcionDetalleSchema,
    ProductoCompletoUpdateSchema
)
from src.api.schemas.alergeno_schema import ProductoAlergeno
from src.business_logic.exceptions.producto_exceptions import (
    ProductoValidationError,
    ProductoNotFoundError,
    ProductoConflictError,
)
from src.core.utils.text_utils import normalize_product_name, normalize_category_name

class ProductoService:
    """Servicio para la gestión de productos en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con productos, incluyendo validaciones, transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : ProductoRepository
        Repositorio para acceso a datos de productos.
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
        self.repository = ProductoRepository(session)
        self.mesa_repository = MesaRepository(session)
        self.locales_productos_repository = LocalesProductosRepository(session)
        self.alergeno_repository = ProductoAlergenoRepository(session)

    @staticmethod
    def _transformar_alergenos_a_schema(producto: ProductoModel) -> List[ProductoAlergeno]:
        """
        Transforma los alérgenos de un producto a ProductoAlergeno schema.
        
        Parameters
        ----------
        producto : ProductoModel
            Modelo de producto con productos_alergenos cargados.
            
        Returns
        -------
        List[ProductoAlergeno]
            Lista de alérgenos transformados con metadatos.
        """
        return [
            ProductoAlergeno.model_validate({
                'id': pa.alergeno.id,
                'nombre': pa.alergeno.nombre,
                'icono': pa.alergeno.icono,
                'nivel_riesgo': pa.alergeno.nivel_riesgo,
                'nivel_presencia': pa.nivel_presencia.value if pa.nivel_presencia else 'contiene',
                'notas': pa.notas
            })
            for pa in producto.productos_alergenos
        ]

    @staticmethod
    def _agrupar_opciones_por_tipo(producto: ProductoModel) -> List[TipoOpcionConOpcionesSchema]:
        """
        Agrupa las opciones del producto por tipo de opción.
        
        Transforma producto.opciones (ProductoOpcionModel) en una estructura
        agrupada por tipo de opción con todas sus opciones correspondientes.
        
        Parameters
        ----------
        producto : ProductoModel
            Modelo de producto con opciones cargadas (eager loaded).
            
        Returns
        -------
        List[TipoOpcionConOpcionesSchema]
            Lista de tipos de opciones con sus opciones agrupadas y ordenadas.
        """
        # Diccionario para agrupar por tipo
        tipos_dict: Dict[str, Dict] = {}
        
        # Agrupar opciones por tipo
        for opcion in producto.opciones:
            tipo_id = str(opcion.id_tipo_opcion)
            
            # Si es la primera opción de este tipo, crear la estructura
            if tipo_id not in tipos_dict:
                tipo_opcion = opcion.tipo_opcion
                tipos_dict[tipo_id] = {
                    "id_tipo_opcion": tipo_id,
                    "nombre_tipo": tipo_opcion.nombre,
                    "descripcion_tipo": tipo_opcion.descripcion,
                    "seleccion_minima": tipo_opcion.seleccion_minima,
                    "seleccion_maxima": tipo_opcion.seleccion_maxima,
                    "orden_tipo": tipo_opcion.orden if tipo_opcion.orden else 0,
                    "opciones": []
                }
            
            # Agregar la opción al tipo
            tipos_dict[tipo_id]["opciones"].append({
                "id": opcion.id,
                "nombre": opcion.nombre,
                "precio_adicional": opcion.precio_adicional,
                "activo": opcion.activo,
                "orden": opcion.orden if opcion.orden else 0,
                "fecha_creacion": opcion.fecha_creacion,
                "fecha_modificacion": opcion.fecha_modificacion
            })
        
        # Convertir a lista y ordenar
        tipos_list = list(tipos_dict.values())
        tipos_list.sort(key=lambda x: x["orden_tipo"])
        
        # Ordenar opciones dentro de cada tipo
        for tipo in tipos_list:
            tipo["opciones"].sort(key=lambda x: x["orden"])
        
        # Convertir a schemas Pydantic
        return [
            TipoOpcionConOpcionesSchema(
                id_tipo_opcion=tipo["id_tipo_opcion"],
                nombre_tipo=tipo["nombre_tipo"],
                descripcion_tipo=tipo["descripcion_tipo"],
                seleccion_minima=tipo["seleccion_minima"],
                seleccion_maxima=tipo["seleccion_maxima"],
                orden_tipo=tipo["orden_tipo"],
                opciones=[
                    ProductoOpcionDetalleSchema(**opcion)
                    for opcion in tipo["opciones"]
                ]
            )
            for tipo in tipos_list
        ]

    async def create_producto(self, producto_data: ProductoCreate) -> ProductoResponse:
        """
        Crea un nuevo producto en el sistema.

        Parameters
        ----------
        producto_data : ProductoCreate
            Datos para crear el nuevo producto.

        Returns
        -------
        ProductoResponse
            Esquema de respuesta con los datos del producto creado.

        Raises
        ------
        ProductoConflictError
            Si ya existe un producto con el mismo nombre.
        """
        try:
            # Crear modelo de producto desde los datos
            producto = ProductoModel(
                id_categoria=producto_data.id_categoria,
                nombre=producto_data.nombre,
                descripcion=producto_data.descripcion,
                precio_base=producto_data.precio_base,
                imagen_path=producto_data.imagen_path,
                imagen_alt_text=producto_data.imagen_alt_text,
            )

            # Persistir en la base de datos
            created_producto = await self.repository.create(producto)

            # Normalizar el nombre antes de retornar
            created_producto.nombre = normalize_product_name(created_producto.nombre)

            # Convertir y retornar como esquema de respuesta
            return ProductoResponse.model_validate(created_producto)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            raise ProductoConflictError(
                f"Ya existe un producto con el nombre '{producto_data.nombre}'"
            )

    async def get_producto_by_id(self, producto_id: str) -> ProductoResponse:
        """
        Obtiene un producto por su ID.

        Parameters
        ----------
        producto_id : str
            Identificador único del producto a buscar (ULID).

        Returns
        -------
        ProductoResponse
            Esquema de respuesta con los datos del producto.

        Raises
        ------
        ProductoNotFoundError
            Si no se encuentra un producto con el ID proporcionado.
        """
        # Buscar el producto por su ID (ahora incluye alérgenos)
        producto = await self.repository.get_by_id(producto_id)

        # Verificar si existe
        if not producto:
            raise ProductoNotFoundError(f"No se encontró el producto con ID {producto_id}")

        # Convertir a dict
        producto_dict = producto.to_dict()
        
        # Transformar productos_alergenos usando método helper
        producto_dict['alergenos'] = self._transformar_alergenos_a_schema(producto)

        # Convertir y retornar como esquema de respuesta
        return ProductoResponse.model_validate(producto_dict)

    async def get_producto_con_opciones(self, producto_id: str) -> ProductoConOpcionesResponse:
        """
        Obtiene un producto por su ID con todas sus opciones agrupadas por tipo.
        Returns
        -------
        ProductoConOpcionesResponse
            Esquema de respuesta con el producto y opciones agrupadas por tipo.
        """
        # Buscar el producto con opciones
        producto = await self.repository.get_by_id_with_opciones(producto_id)
        if not producto:
            raise ProductoNotFoundError(
                f"No se encontró el producto con el ID proporcionado"
            )

        # Transformar alérgenos y opciones usando métodos helpers
        alergenos_detallados = self._transformar_alergenos_a_schema(producto)
        tipos_opciones_schemas = self._agrupar_opciones_por_tipo(producto)

        return ProductoConOpcionesResponse(
            id=producto.id,
            nombre=normalize_product_name(producto.nombre),
            descripcion=producto.descripcion,
            precio_base=producto.precio_base,
            imagen_path=producto.imagen_path,
            imagen_alt_text=producto.imagen_alt_text,
            id_categoria=str(producto.id_categoria),
            disponible=producto.disponible,
            destacado=producto.destacado,
            alergenos=alergenos_detallados,
            fecha_creacion=producto.fecha_creacion,
            fecha_modificacion=producto.fecha_modificacion,
            tipos_opciones=tipos_opciones_schemas
        )

    async def delete_producto(self, producto_id: str) -> bool:
        """
        Elimina un producto por su ID.

        Parameters
        ----------
        producto_id : str
            Identificador único del producto a eliminar (ULID).

        Returns
        -------
        bool
            True si el producto fue eliminado correctamente.

        Raises
        ------
        ProductoNotFoundError
            Si no se encuentra un producto con el ID proporcionado.
        """
        # Verificar primero si el producto existe
        producto = await self.repository.get_by_id(producto_id)
        if not producto:
            raise ProductoNotFoundError(f"No se encontró el producto con ID {producto_id}")

        # Eliminar el producto
        result = await self.repository.delete(producto_id)
        return result

    async def get_productos(
        self,
        skip: int = 0,
        limit: int = 100,
        id_categoria: str | None = None,
        id_mesa: Optional[str] = None,
        id_local: Optional[str] = None
    ) -> ProductoList:
        """
        Obtiene una lista paginada de productos.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.
        id_categoria : str, optional
            ID de categoría para filtrar productos.
        id_mesa : str, optional
            ID de mesa para filtrar por local (el backend resuelve local automáticamente).
        id_local : str, optional
            ID de local para filtrar directamente.

        Returns
        -------
        ProductoList
            Esquema con la lista de productos y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ProductoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ProductoValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Resolver local desde mesa si es necesario
        local_id = None

        if id_mesa:
            # Resolver: mesa → zona → local
            local = await self.mesa_repository.get_local_by_mesa_id(id_mesa)
            if local:
                local_id = local.id
            else:
                raise ProductoValidationError(f"La mesa {id_mesa} no tiene un local asignado")
        elif id_local:
            local_id = id_local

        # Filtrar por local si tenemos uno
        if local_id:
            return await self._get_productos_con_local(local_id, skip, limit, id_categoria)
        else:
            # Sin filtro - retornar todos los productos (backward compatible)
            productos, total = await self.repository.get_all(skip, limit, id_categoria)

            # Normalizar nombres y convertir modelos a esquemas de resumen
            for producto in productos:
                producto.nombre = normalize_product_name(producto.nombre)
            producto_summaries = [ProductoSummary.model_validate(producto) for producto in productos]

            # Retornar esquema de lista
            return ProductoList(items=producto_summaries, total=total)

    async def _get_productos_con_local(
        self,
        id_local: str,
        skip: int,
        limit: int,
        id_categoria: Optional[str] = None
    ) -> ProductoList:
        """
        Obtiene productos filtrados por local con overrides aplicados.

        Parameters
        ----------
        id_local : str
            ID del local para filtrar.
        skip : int
            Número de registros a omitir.
        limit : int
            Número máximo de registros a retornar.
        id_categoria : str, optional
            ID de categoría para filtrar productos.

        Returns
        -------
        ProductoList
            Lista de productos con overrides aplicados.
        """
        from decimal import Decimal

        # Obtener relaciones local-producto activas
        relaciones, total = await self.locales_productos_repository.get_productos_by_local(
            id_local, activo=True, skip=skip, limit=limit
        )

        # Cargar productos completos y aplicar overrides
        productos_con_overrides = []
        for relacion in relaciones:
            producto = await self.repository.get_by_id(relacion.id_producto)
            if producto:
                # Filtrar por categoría si se especificó
                if id_categoria and str(producto.id_categoria) != id_categoria:
                    total -= 1  # Ajustar el total
                    continue

                # Aplicar overrides (NULL = usar original, NOT NULL = usar custom)
                producto_dict = producto.to_dict()
                producto_dict['nombre'] = normalize_product_name(
                    relacion.nombre_override if relacion.nombre_override is not None else producto.nombre
                )
                producto_dict['precio_base'] = (
                    relacion.precio_override if relacion.precio_override is not None else producto.precio_base
                )
                producto_dict['descripcion'] = (
                    relacion.descripcion_override if relacion.descripcion_override is not None else producto.descripcion
                )
                producto_dict['disponible'] = (
                    relacion.disponible_override if relacion.disponible_override is not None else producto.disponible
                )

                productos_con_overrides.append(ProductoSummary.model_validate(producto_dict))

        return ProductoList(items=productos_con_overrides, total=total)

    async def update_producto(self, producto_id: str, producto_data: ProductoUpdate) -> ProductoResponse:
        """
        Actualiza un producto existente.

        Parameters
        ----------
        producto_id : str
            Identificador único del producto a actualizar (ULID).
        producto_data : ProductoUpdate
            Datos para actualizar el producto.

        Returns
        -------
        ProductoResponse
            Esquema de respuesta con los datos del producto actualizado.

        Raises
        ------
        ProductoNotFoundError
            Si no se encuentra un producto con el ID proporcionado.
        ProductoConflictError
            Si ya existe otro producto con el mismo nombre.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = producto_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar el producto actual
            return await self.get_producto_by_id(producto_id)

        try:
            # Actualizar el producto
            updated_producto = await self.repository.update(producto_id, **update_data)

            # Verificar si el producto fue encontrado
            if not updated_producto:
                raise ProductoNotFoundError(f"No se encontró el producto con ID {producto_id}")

            # Normalizar el nombre antes de retornar
            updated_producto.nombre = normalize_product_name(updated_producto.nombre)

            # Convertir y retornar como esquema de respuesta
            return ProductoResponse.model_validate(updated_producto)
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            if "nombre" in update_data:
                raise ProductoConflictError(
                    f"Ya existe un producto con el nombre '{update_data['nombre']}'"
                )
            # Si no es por nombre, reenviar la excepción original
            raise

    async def batch_create_productos(
        self, productos_data: List[ProductoCreate]
    ) -> List[ProductoResponse]:
        """
        Crea múltiples productos en una sola operación.

        Parameters
        ----------
        productos_data : List[ProductoCreate]
            Lista de datos para crear nuevos productos.

        Returns
        -------
        List[ProductoResponse]
            Lista de esquemas de respuesta con los datos de los productos creados.

        Raises
        ------
        ProductoConflictError
            Si ya existe un producto con alguno de los nombres proporcionados.
        """
        if not productos_data:
            return []

        try:
            # Crear modelos de productos desde los datos
            producto_models = [
                ProductoModel(
                    id_categoria=producto_data.id_categoria,
                    nombre=producto_data.nombre,
                    descripcion=producto_data.descripcion,
                    precio_base=producto_data.precio_base,
                    imagen_path=producto_data.imagen_path,
                    imagen_alt_text=producto_data.imagen_alt_text,
                )
                for producto_data in productos_data
            ]

            # Persistir en la base de datos usando batch insert
            created_productos = await self.repository.batch_insert(producto_models)

            # Normalizar nombres y convertir a esquemas de respuesta
            for producto in created_productos:
                producto.nombre = normalize_product_name(producto.nombre)
            return [
                ProductoResponse.model_validate(producto)
                for producto in created_productos
            ]
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            raise ProductoConflictError(
                "Uno o más productos ya existen con el mismo nombre"
            )

    async def batch_update_productos(
        self, updates: List[Tuple[str, ProductoUpdate]]
    ) -> List[ProductoResponse]:
        """
        Actualiza múltiples productos en una sola operación.

        Parameters
        ----------
        updates : List[Tuple[str, ProductoUpdate]]
            Lista de tuplas con el ID (ULID) del producto y los datos para actualizarlo.

        Returns
        -------
        List[ProductoResponse]
            Lista de esquemas de respuesta con los datos de los productos actualizados.

        Raises
        ------
        ProductoNotFoundError
            Si alguno de los productos no existe.
        ProductoConflictError
            Si hay conflictos de integridad (nombres duplicados).
        """
        if not updates:
            return []

        try:
            # Preparar los datos para el repositorio
            repository_updates = []

            for producto_id, producto_data in updates:
                # Convertir el esquema de actualización a un diccionario,
                # excluyendo valores None (campos no proporcionados)
                update_data = producto_data.model_dump(exclude_none=True)

                if update_data:  # Solo incluir si hay datos para actualizar
                    repository_updates.append((producto_id, update_data))

            # Realizar actualización en lote
            updated_productos = await self.repository.batch_update(repository_updates)

            # Verificar si todos los productos fueron actualizados
            if len(updated_productos) != len(repository_updates):
                missing_ids = set(u[0] for u in repository_updates) - set(
                    str(p.id) for p in updated_productos
                )
                if missing_ids:
                    raise ProductoNotFoundError(
                        f"No se encontraron los productos con IDs: {missing_ids}"
                    )

            # Normalizar nombres y convertir a esquemas de respuesta
            for producto in updated_productos:
                producto.nombre = normalize_product_name(producto.nombre)
            return [
                ProductoResponse.model_validate(producto)
                for producto in updated_productos
            ]
        except IntegrityError:
            # Capturar errores de integridad (nombre duplicado)
            raise ProductoConflictError(
                "Una o más actualizaciones causaron conflictos de integridad"
            )

    async def get_productos_cards_by_categoria(
        self,
        categoria_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> ProductoCardList:
        """
        Obtiene una lista paginada de productos en formato card (nombre, imagen, categoría).

        Parameters
        ----------
        categoria_id : str | None, optional
            ID de la categoría para filtrar productos. Si es None, retorna todos los productos.
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        ProductoCardList
            Esquema con la lista de productos en formato card y el total.

        Raises
        ------
        ProductoValidationError
            Si los parámetros de paginación son inválidos.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ProductoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ProductoValidationError("El parámetro 'limit' debe ser mayor a cero")

        # Obtener productos desde el repositorio (con o sin filtro de categoría)
        productos, total = await self.repository.get_all(skip, limit, categoria_id)

        # Convertir modelos a esquemas de card
        # Necesitamos incluir la información de la categoría para cada producto
        producto_cards = []
        for producto in productos:
            # Construir el objeto ProductoCard con información de categoría (nombres normalizados)
            card_data = {
                "id": producto.id,
                "nombre": normalize_product_name(producto.nombre),
                "imagen_path": producto.imagen_path,
                "precio_base": producto.precio_base,
                "categoria": {
                    "id": producto.categoria.id,
                    "nombre": normalize_category_name(producto.categoria.nombre),
                    "imagen_path": producto.categoria.imagen_path,
                }
            }
            producto_cards.append(ProductoCard.model_validate(card_data))

        # Retornar esquema de lista
        return ProductoCardList(items=producto_cards, total=total)

    async def update_producto_completo(
        self, producto_id: str, producto_data: ProductoCompletoUpdateSchema
    ) -> ProductoConOpcionesResponse:
        """
        Actualiza completamente un producto con todos sus datos relacionados.

        Actualiza el producto base, sus alérgenos, secciones, tipos de opciones y opciones.
        Reemplaza completamente las relaciones existentes.

        Parameters
        ----------
        producto_id : str
            Identificador único del producto a actualizar.
        producto_data : ProductoCompletoUpdateSchema
            Esquema con todos los datos del producto a actualizar.

        Returns
        -------
        ProductoConOpcionesResponse
            Esquema de respuesta con el producto actualizado y todas sus relaciones.

        Raises
        ------
        ProductoNotFoundError
            Si no se encuentra el producto con el ID especificado.
        ProductoConflictError
            Si hay conflictos de integridad (ej. nombre duplicado).
        ProductoValidationError
            Si los datos de entrada son inválidos.
        """
        try:
            # Verificar que el producto existe
            producto = await self.repository.get_by_id(producto_id)
            if not producto:
                raise ProductoNotFoundError(f"No se encontró el producto con ID {producto_id}")

            # Actualizar datos básicos del producto
            update_data = {
                "descripcion": producto_data.descripcion,
                "disponible": producto_data.disponible,
                "destacado": producto_data.destacado,
            }

            # Actualizar el producto base usando **kwargs
            updated_producto = await self.repository.update(producto_id, **update_data)

            # TODO: Actualizar alérgenos del producto
            # await self._update_producto_alergenos(producto_id, producto_data.alergenos)

            # TODO: Actualizar secciones del producto
            # await self._update_producto_secciones(producto_id, producto_data.secciones)

            # TODO: Actualizar tipos de opciones y opciones del producto
            # await self._update_producto_tipos_opciones(producto_id, producto_data.tipos_opciones)

            # Obtener el producto actualizado con todas sus relaciones
            producto_completo = await self.repository.get_by_id_with_opciones(producto_id)
            if not producto_completo:
                raise ProductoNotFoundError(f"Error al obtener el producto actualizado con ID {producto_id}")

            # Normalizar nombres antes de retornar
            producto_completo.nombre = normalize_product_name(producto_completo.nombre)

            # Transformar y estructurar los datos de opciones por tipo
            tipos_opciones_response = []
            if hasattr(producto_completo, 'opciones') and producto_completo.opciones:
                # Agrupar opciones por tipo
                tipos_dict = {}
                for opcion in producto_completo.opciones:
                    tipo_id = opcion.tipo_opcion.id
                    if tipo_id not in tipos_dict:
                        tipos_dict[tipo_id] = {
                            "id_tipo_opcion": opcion.tipo_opcion.id,
                            "nombre_tipo": opcion.tipo_opcion.nombre,
                            "descripcion_tipo": opcion.tipo_opcion.descripcion,
                            "seleccion_minima": opcion.tipo_opcion.seleccion_minima,
                            "seleccion_maxima": opcion.tipo_opcion.seleccion_maxima,
                            "orden_tipo": opcion.tipo_opcion.orden,
                            "opciones": []
                        }

                    tipos_dict[tipo_id]["opciones"].append(
                        ProductoOpcionDetalleSchema.model_validate(opcion)
                    )

                # Convertir el diccionario a lista ordenada por orden_tipo
                tipos_opciones_response = [
                    TipoOpcionConOpcionesSchema.model_validate(tipo_data)
                    for tipo_data in sorted(tipos_dict.values(), key=lambda x: x["orden_tipo"])
                ]

            # Construir respuesta con estructura completa
            response_data = {
                "id": producto_completo.id,
                "nombre": producto_completo.nombre,
                "descripcion": producto_completo.descripcion,
                "precio_base": producto_completo.precio_base,
                "imagen_path": producto_completo.imagen_path,
                "imagen_alt_text": producto_completo.imagen_alt_text,
                "id_categoria": producto_completo.id_categoria,
                "disponible": producto_completo.disponible,
                "destacado": producto_completo.destacado,
                "alergenos": producto_completo.alergenos if hasattr(producto_completo, 'alergenos') else [],
                "fecha_creacion": producto_completo.fecha_creacion,
                "fecha_modificacion": producto_completo.fecha_modificacion,
                "tipos_opciones": tipos_opciones_response
            }

            return ProductoConOpcionesResponse.model_validate(response_data)

        except IntegrityError as e:
            raise ProductoValidationError(f"Error de integridad en los datos: {str(e)}")
        except Exception as e:
            # Capturar otros errores y convertir a excepción de validación
            if isinstance(e, (ProductoNotFoundError, ProductoConflictError, ProductoValidationError)):
                raise
            raise ProductoValidationError(f"Error al actualizar el producto: {str(e)}")
