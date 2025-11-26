"""Servicio de lógica de negocio para alérgenos."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.alergeno_schema import AlergenoList, AlergenoSummary
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.repositories.menu.alergeno_repository import AlergenoRepository


class AlergenoService:
    """Gestiona la lógica de negocio de alérgenos.

    Responsabilidades:
    - Validar reglas de negocio
    - Orquestar operaciones del repositorio
    - Transformar excepciones técnicas en excepciones de dominio
    """

    __slots__ = ("_repository",)

    def __init__(self, session: AsyncSession) -> None:
        """Inicializa el servicio.

        Args:
            session: Sesión de base de datos (inyectada por dependencia)
        """
        self._repository = AlergenoRepository(session)

    def _validate_pagination(self, skip: int, limit: int) -> None:
        """Valida parámetros de paginación.

        Args:
            skip: Offset de paginación
            limit: Límite de registros

        Raises:
            AlergenoValidationError: Si los parámetros son inválidos
        """
        if skip < 0:
            raise AlergenoValidationError(
                "El parámetro 'skip' debe ser mayor o igual a cero"
            )
        if limit <= 0:
            raise AlergenoValidationError("El parámetro 'limit' debe ser mayor a cero")

    async def get_alergenos(
        self, skip: int = 0, limit: int = 100, producto_id: Optional[str] = None
    ) -> AlergenoList:
        """Obtiene lista paginada de alérgenos.

        Args:
            skip: Offset de paginación (por defecto 0)
            limit: Límite de registros (por defecto 100)
            producto_id: ID del producto para filtrar alérgenos por asociación.
                Si se proporciona, retorna solo los alérgenos asociados al producto.
                La lógica de filtrado es delegada a la capa de repositorio.

        Returns:
            Lista paginada de alérgenos

        Raises:
            AlergenoValidationError: Si los parámetros de paginación son inválidos
        """
        self._validate_pagination(skip=skip, limit=limit)
        result = await self._repository.get_all(skip=skip, limit=limit, producto_id=producto_id)

        return AlergenoList(
            items=[AlergenoSummary.model_validate(alergeno) for alergeno in result],
            total=len(result),
        )
