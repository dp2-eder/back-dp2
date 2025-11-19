"""
Schemas de Pydantic para la entidad DivisionCuentaDetalle.

Este módulo define las estructuras de datos para crear, actualizar y
representar los detalles de división de cuenta en la API.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class DivisionCuentaDetalleBase(BaseModel):
    """
    Schema base con los campos comunes para un detalle de división.

    Attributes
    ----------
    persona_numero : int
        Identificador de persona (1, 2, 3, etc).
    monto_asignado : Decimal
        Monto que esta persona debe pagar por este item.
    """

    persona_numero: int = Field(
        ge=1,
        description="Identificador de persona (1, 2, 3, etc)."
    )
    monto_asignado: Decimal = Field(
        ge=0,
        decimal_places=2,
        description="Monto que esta persona debe pagar por este item."
    )


class DivisionCuentaDetalleCreate(DivisionCuentaDetalleBase):
    """
    Schema para la creación de un nuevo detalle de división.

    Attributes
    ----------
    id_division_cuenta : str
        Identificador de la división de cuenta.
    id_pedido_producto : str
        Identificador del producto del pedido.
    """

    id_division_cuenta: str = Field(
        description="Identificador de la división de cuenta.",
        min_length=1,
        max_length=36
    )
    id_pedido_producto: str = Field(
        description="Identificador del producto del pedido.",
        min_length=1,
        max_length=36
    )


class DivisionCuentaDetalleUpdate(BaseModel):
    """
    Schema para la actualización parcial de un detalle de división.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """

    persona_numero: Optional[int] = Field(
        default=None,
        ge=1,
        description="Nuevo identificador de persona."
    )
    monto_asignado: Optional[Decimal] = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Nuevo monto asignado."
    )


class DivisionCuentaDetalleResponse(DivisionCuentaDetalleBase):
    """
    Schema para representar un detalle de división en las respuestas de la API.

    Incluye campos de solo lectura que no se exponen en la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del detalle (ULID).")
    id_division_cuenta: str = Field(description="Identificador de la división de cuenta.")
    id_pedido_producto: str = Field(description="Identificador del producto del pedido.")
    created_at: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación."
    )


class DivisionCuentaDetalleSummary(BaseModel):
    """
    Schema con información resumida de un detalle de división para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del detalle (ULID).")
    persona_numero: int = Field(description="Identificador de persona.")
    monto_asignado: Decimal = Field(description="Monto asignado.")
    id_pedido_producto: str = Field(description="ID del producto del pedido.")


class DivisionCuentaDetalleList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de detalles de división."""
    items: List[DivisionCuentaDetalleSummary] = Field(description="Lista de detalles en la página actual.")
    total: int = Field(description="Número total de detalles que coinciden con la consulta.")
