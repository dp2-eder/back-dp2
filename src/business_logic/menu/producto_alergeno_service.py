"""
Servicio para la gestión de relaciones producto-alérgeno en el sistema.
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.menu.producto_alergeno_repository import ProductoAlergenoRepository
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.api.schemas.producto_alergeno_schema import (
    ProductoAlergenoCreate,
    ProductoAlergenoUpdate,
    ProductoAlergenoResponse,
    ProductoAlergenoSummary,
    ProductoAlergenoList,
)
from src.business_logic.exceptions.producto_alergeno_exceptions import (
    ProductoAlergenoValidationError,
    ProductoAlergenoNotFoundError,
    ProductoAlergenoConflictError,
)


class ProductoAlergenoService:
    """Servicio para la gestión de relaciones producto-alérgeno en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con la asignación de alérgenos a productos del menú, incluyendo validaciones,
    transformaciones y manejo de excepciones.

    Attributes
    ----------
    repository : ProductoAlergenoRepository
        Repositorio para acceso a datos de relaciones producto-alérgeno.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = ProductoAlergenoRepository(session)

    async def create_producto_alergeno(
        self, producto_alergeno_data: ProductoAlergenoCreate
    ) -> ProductoAlergenoResponse:
        """
        Crea una nueva relación producto-alérgeno en el sistema.
        
        Parameters
        ----------
        producto_alergeno_data : ProductoAlergenoCreate
            Datos para crear la nueva relación.

        Returns
        -------
        ProductoAlergenoResponse
            Esquema de respuesta con los datos de la relación creada.

        Raises
        ------
        ProductoAlergenoConflictError
            Si ya existe una relación entre el mismo producto y alérgeno.
        """
        try:
            # Crear modelo de relación desde los datos
            producto_alergeno = ProductoAlergenoModel(
                id_producto=producto_alergeno_data.id_producto,
                id_alergeno=producto_alergeno_data.id_alergeno,
                nivel_presencia=producto_alergeno_data.nivel_presencia,
                notas=producto_alergeno_data.notas,
            )

            # Persistir en la base de datos
            created_producto_alergeno = await self.repository.create(producto_alergeno)

            # Convertir y retornar como esquema de respuesta
            return ProductoAlergenoResponse.model_validate(created_producto_alergeno)
        except IntegrityError:
            # Capturar errores de integridad (relación duplicada)
            raise ProductoAlergenoConflictError(
                f"Ya existe una relación entre el producto "
                f"{producto_alergeno_data.id_producto} y el alérgeno "
                f"{producto_alergeno_data.id_alergeno}"
            )

    async def get_producto_alergeno_by_id(
        self, id: str
    ) -> ProductoAlergenoResponse:
        """
        Obtiene una relación producto-alérgeno por su ID simple (ULID).

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.

        Returns
        -------
        ProductoAlergenoResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con el ID proporcionado.
        """
        # Buscar la relación por su ID
        producto_alergeno = await self.repository.get_by_id(id)

        # Verificar si existe
        if not producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación con ID {id}"
            )

        # Convertir y retornar como esquema de respuesta
        return ProductoAlergenoResponse.model_validate(producto_alergeno)

    async def get_producto_alergeno_by_combination(
        self, id_producto: str, id_alergeno: str
    ) -> ProductoAlergenoResponse:
        """
        Obtiene una relación producto-alérgeno por combinación (backward compatibility).

        LEGACY METHOD: Usar get_producto_alergeno_by_id() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto (ULID).
        id_alergeno : str
            Identificador único del alérgeno (ULID).

        Returns
        -------
        ProductoAlergenoResponse
            Esquema de respuesta con los datos de la relación.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con los IDs proporcionados.
        """
        # Buscar la relación por su clave compuesta
        producto_alergeno = await self.repository.get_by_producto_alergeno(id_producto, id_alergeno)

        # Verificar si existe
        if not producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {id_producto} "
                f"y alérgeno {id_alergeno}"
            )

        # Convertir y retornar como esquema de respuesta
        return ProductoAlergenoResponse.model_validate(producto_alergeno)

    async def delete_producto_alergeno(
        self, id: str
    ) -> bool:
        """
        Elimina una relación producto-alérgeno por su ID simple (ULID).

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.

        Returns
        -------
        bool
            True si la relación fue eliminada correctamente.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con el ID proporcionado.
        """
        # Verificar primero si la relación existe
        producto_alergeno = await self.repository.get_by_id(id)
        if not producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación con ID {id}"
            )

        # Eliminar la relación
        result = await self.repository.delete(id)
        return result

    async def delete_producto_alergeno_by_combination(
        self, id_producto: str, id_alergeno: str
    ) -> bool:
        """
        Elimina una relación por combinación (backward compatibility).

        LEGACY METHOD: Usar delete_producto_alergeno() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto (ULID).
        id_alergeno : str
            Identificador único del alérgeno (ULID).

        Returns
        -------
        bool
            True si la relación fue eliminada correctamente.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con los IDs proporcionados.
        """
        # Verificar primero si la relación existe
        producto_alergeno = await self.repository.get_by_producto_alergeno(id_producto, id_alergeno)
        if not producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {id_producto} "
                f"y alérgeno {id_alergeno}"
            )

        # Eliminar la relación
        result = await self.repository.delete_by_producto_alergeno(id_producto, id_alergeno)
        return result

    async def get_producto_alergenos(
        self, skip: int = 0, limit: int = 100
    ) -> ProductoAlergenoList:
        """
        Obtiene una lista paginada de relaciones producto-alérgeno.

        Parameters
        ----------
        skip : int, optional
            Número de registros a omitir (offset), por defecto 0.
        limit : int, optional
            Número máximo de registros a retornar, por defecto 100.

        Returns
        -------
        ProductoAlergenoList
            Esquema con la lista de relaciones y el total.
        """
        # Validar parámetros de entrada
        if skip < 0:
            raise ProductoAlergenoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit < 1:
            raise ProductoAlergenoValidationError(
                "El parámetro 'limit' debe ser mayor a cero"
            )

        # Obtener relaciones desde el repositorio
        producto_alergenos, total = await self.repository.get_all(skip, limit)

        # Convertir modelos a esquemas de resumen
        producto_alergeno_summaries = [
            ProductoAlergenoSummary.model_validate(pa) for pa in producto_alergenos
        ]

        # Retornar esquema de lista
        return ProductoAlergenoList(items=producto_alergeno_summaries, total=total)

    async def get_alergenos_by_producto(self, id_producto: str) -> List:
        """
        Obtiene todos los alérgenos asociados a un producto específico.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto (ULID).

        Returns
        -------
        List[AlergenoResponse]
            Lista de alérgenos asociados al producto.

        Raises
        ------
        ProductoAlergenoValidationError
            Si los parámetros de entrada no son válidos.
        """
        if not id_producto:
            raise ProductoAlergenoValidationError(
                "El ID del producto es requerido"
            )

        # Obtener alérgenos desde el repositorio
        alergenos = await self.repository.get_alergenos_by_producto(id_producto)

        # Convertir modelos a esquemas de respuesta
        # Importación tardía para evitar referencias circulares
        try:
            from src.api.schemas.alergeno_schema import AlergenoResponse
            return [AlergenoResponse.model_validate(alergeno) for alergeno in alergenos]
        except ImportError as e:
            # Si hay problema con el schema, devolver diccionarios simples
            return [alergeno.to_dict() for alergeno in alergenos]

    async def update_producto_alergeno(
        self,
        id: str,
        producto_alergeno_data: ProductoAlergenoUpdate,
    ) -> ProductoAlergenoResponse:
        """
        Actualiza una relación producto-alérgeno existente por su ID simple (ULID).

        Parameters
        ----------
        id : str
            Identificador único ULID de la relación.
        producto_alergeno_data : ProductoAlergenoUpdate
            Datos para actualizar la relación.

        Returns
        -------
        ProductoAlergenoResponse
            Esquema de respuesta con los datos de la relación actualizada.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con el ID proporcionado.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = producto_alergeno_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la relación actual
            return await self.get_producto_alergeno_by_id(id)

        # Actualizar la relación
        updated_producto_alergeno = await self.repository.update(
            id, **update_data
        )

        # Verificar si la relación fue encontrada
        if not updated_producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación con ID {id}"
            )

        # Convertir y retornar como esquema de respuesta
        return ProductoAlergenoResponse.model_validate(updated_producto_alergeno)

    async def update_producto_alergeno_by_combination(
        self,
        id_producto: str,
        id_alergeno: str,
        producto_alergeno_data: ProductoAlergenoUpdate,
    ) -> ProductoAlergenoResponse:
        """
        Actualiza una relación por combinación (backward compatibility).

        LEGACY METHOD: Usar update_producto_alergeno() para nuevas implementaciones.

        Parameters
        ----------
        id_producto : str
            Identificador único del producto (ULID).
        id_alergeno : str
            Identificador único del alérgeno (ULID).
        producto_alergeno_data : ProductoAlergenoUpdate
            Datos para actualizar la relación.

        Returns
        -------
        ProductoAlergenoResponse
            Esquema de respuesta con los datos de la relación actualizada.

        Raises
        ------
        ProductoAlergenoNotFoundError
            Si no se encuentra la relación con los IDs proporcionados.
        """
        # Convertir el esquema de actualización a un diccionario,
        # excluyendo valores None (campos no proporcionados para actualizar)
        update_data = producto_alergeno_data.model_dump(exclude_none=True)

        if not update_data:
            # Si no hay datos para actualizar, simplemente retornar la relación actual
            return await self.get_producto_alergeno_by_combination(id_producto, id_alergeno)

        # Actualizar la relación
        updated_producto_alergeno = await self.repository.update_by_producto_alergeno(
            id_producto, id_alergeno, **update_data
        )

        # Verificar si la relación fue encontrada
        if not updated_producto_alergeno:
            raise ProductoAlergenoNotFoundError(
                f"No se encontró la relación entre producto {id_producto} "
                f"y alérgeno {id_alergeno}"
            )

        # Convertir y retornar como esquema de respuesta
        return ProductoAlergenoResponse.model_validate(updated_producto_alergeno)
