"""
Pydantic schemas for PedidoOpcion (Order Option) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PedidoOpcionBase(BaseModel):
    """Base schema for PedidoOpcion."""

    id_pedido_producto: str = Field(description="Pedido Producto ID (ULID)", min_length=1, max_length=36)
    id_producto_opcion: str = Field(description="Producto Opcion ID (ULID)", min_length=1, max_length=36)
    precio_adicional: Decimal = Field(
        default=Decimal("0.00"),
        description="Additional price at order time",
        ge=0,
        decimal_places=2
    )

    @field_validator('precio_adicional', mode='before')
    @classmethod
    def validate_decimals(cls, v):
        """Validate and convert decimal values."""
        if v is None:
            return Decimal("0.00")
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class PedidoOpcionCreate(PedidoOpcionBase):
    """Schema for creating a new pedido opcion."""
    pass


class PedidoOpcionUpdate(BaseModel):
    """Schema for updating pedido opcion.

    All fields are optional to allow partial updates.
    """

    precio_adicional: Optional[Decimal] = Field(
        default=None,
        description="Additional price",
        ge=0,
        decimal_places=2
    )

    @field_validator('precio_adicional', mode='before')
    @classmethod
    def validate_decimals(cls, v):
        """Validate and convert decimal values."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class PedidoOpcionResponse(PedidoOpcionBase):
    """Schema for pedido opcion responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="PedidoOpcion ID (ULID)")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    creado_por: Optional[str] = Field(
        default=None, description="Created by user ID"
    )
    modificado_por: Optional[str] = Field(
        default=None, description="Modified by user ID"
    )


class PedidoOpcionSummary(BaseModel):
    """Schema for summarized pedido opcion information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="PedidoOpcion ID (ULID)")
    id_pedido_producto: str = Field(description="Pedido Producto ID (ULID)")
    id_producto_opcion: str = Field(description="Producto Opcion ID (ULID)")
    precio_adicional: Decimal = Field(description="Additional price")


class PedidoOpcionList(BaseModel):
    """Schema for paginated list of pedido opciones."""

    items: List[PedidoOpcionSummary]
    total: int = Field(description="Total number of pedido opciones")
