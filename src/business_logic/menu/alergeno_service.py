"""Servicio de lógica de negocio para alérgenos."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.alergeno_schema import AlergenoList, AlergenoSummary
from src.business_logic.exceptions.alergeno_exceptions import AlergenoValidationError
from src.business_logic.exceptions.base_exceptions import ValidationError
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

    async def get_alergenos(
        self, skip: int = 0, limit: int = 100
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
        try:
            result, total = await self._repository.get_all(skip=skip, limit=limit)
        except ValidationError as e:
            raise AlergenoValidationError(f"Error de validación en parámetros: {str(e)}")

        return AlergenoList(
            items=[AlergenoSummary.model_validate(alergeno) for alergeno in result],
            total=total,
        )
