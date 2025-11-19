"""
Servicio para la gestión de detalles de división de cuenta en el sistema.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from src.repositories.pagos.division_cuenta_detalle_repository import DivisionCuentaDetalleRepository
from src.repositories.pagos.division_cuenta_repository import DivisionCuentaRepository
from src.repositories.pedidos.pedido_producto_repository import PedidoProductoRepository
from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel
from src.api.schemas.division_cuenta_detalle_schema import (
    DivisionCuentaDetalleCreate,
    DivisionCuentaDetalleUpdate,
    DivisionCuentaDetalleResponse,
    DivisionCuentaDetalleSummary,
    DivisionCuentaDetalleList,
)
from src.business_logic.exceptions.division_cuenta_exceptions import (
    DivisionCuentaValidationError,
    DivisionCuentaNotFoundError,
    DivisionCuentaConflictError,
)


class DivisionCuentaDetalleService:
    """Servicio para la gestión de detalles de división de cuenta."""

    def __init__(self, session: AsyncSession):
        self.repository = DivisionCuentaDetalleRepository(session)
        self.division_repository = DivisionCuentaRepository(session)
        self.pedido_producto_repository = PedidoProductoRepository(session)

    async def create_detalle(
        self, detalle_data: DivisionCuentaDetalleCreate
    ) -> DivisionCuentaDetalleResponse:
        """Crea un nuevo detalle de división."""
        # Validar división existe
        division = await self.division_repository.get_by_id(detalle_data.id_division_cuenta)
        if not division:
            raise DivisionCuentaValidationError(
                f"La división con ID '{detalle_data.id_division_cuenta}' no existe"
            )

        # Validar pedido_producto existe
        pedido_producto = await self.pedido_producto_repository.get_by_id(
            detalle_data.id_pedido_producto
        )
        if not pedido_producto:
            raise DivisionCuentaValidationError(
                f"El producto del pedido con ID '{detalle_data.id_pedido_producto}' no existe"
            )

        # Validar persona_numero dentro del rango
        if detalle_data.persona_numero > division.cantidad_personas:
            raise DivisionCuentaValidationError(
                f"persona_numero debe estar entre 1 y {division.cantidad_personas}"
            )

        # Validar monto no negativo
        if detalle_data.monto_asignado < 0:
            raise DivisionCuentaValidationError("El monto asignado no puede ser negativo")

        try:
            detalle = DivisionCuentaDetalleModel(
                id_division_cuenta=detalle_data.id_division_cuenta,
                id_pedido_producto=detalle_data.id_pedido_producto,
                persona_numero=detalle_data.persona_numero,
                monto_asignado=detalle_data.monto_asignado,
            )

            created_detalle = await self.repository.create(detalle)
            return DivisionCuentaDetalleResponse.model_validate(created_detalle)
        except IntegrityError as e:
            raise DivisionCuentaConflictError(f"Error al crear el detalle: {str(e)}")

    async def get_detalle_by_id(self, detalle_id: str) -> DivisionCuentaDetalleResponse:
        """Obtiene un detalle por su ID."""
        detalle = await self.repository.get_by_id(detalle_id)

        if not detalle:
            raise DivisionCuentaNotFoundError(
                f"No se encontró el detalle con ID {detalle_id}"
            )

        return DivisionCuentaDetalleResponse.model_validate(detalle)

    async def get_detalles_by_division(
        self, division_id: str
    ) -> List[DivisionCuentaDetalleResponse]:
        """Obtiene detalles por división."""
        detalles = await self.repository.get_by_division(division_id)
        return [DivisionCuentaDetalleResponse.model_validate(d) for d in detalles]

    async def get_detalles_by_persona(
        self, division_id: str, persona_numero: int
    ) -> List[DivisionCuentaDetalleResponse]:
        """Obtiene detalles asignados a una persona."""
        detalles = await self.repository.get_by_persona(division_id, persona_numero)
        return [DivisionCuentaDetalleResponse.model_validate(d) for d in detalles]

    async def update_detalle(
        self, detalle_id: str, detalle_data: DivisionCuentaDetalleUpdate
    ) -> DivisionCuentaDetalleResponse:
        """Actualiza un detalle existente."""
        update_data = detalle_data.model_dump(exclude_none=True)

        if not update_data:
            return await self.get_detalle_by_id(detalle_id)

        # Validaciones
        if "monto_asignado" in update_data and update_data["monto_asignado"] < 0:
            raise DivisionCuentaValidationError("El monto asignado no puede ser negativo")

        try:
            updated_detalle = await self.repository.update(detalle_id, **update_data)

            if not updated_detalle:
                raise DivisionCuentaNotFoundError(
                    f"No se encontró el detalle con ID {detalle_id}"
                )

            return DivisionCuentaDetalleResponse.model_validate(updated_detalle)
        except IntegrityError as e:
            raise DivisionCuentaConflictError(f"Error al actualizar el detalle: {str(e)}")

    async def delete_detalle(self, detalle_id: str) -> bool:
        """Elimina un detalle por su ID."""
        detalle = await self.repository.get_by_id(detalle_id)
        if not detalle:
            raise DivisionCuentaNotFoundError(
                f"No se encontró el detalle con ID {detalle_id}"
            )

        result = await self.repository.delete(detalle_id)
        return result
