"""
Pydantic schemas for PedidoProducto (Order Item) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PedidoProductoBase(BaseModel):
    """Base schema for PedidoProducto."""

    id_pedido: str = Field(description="Pedido ID (ULID)", min_length=1, max_length=36)
    id_producto: str = Field(description="Producto ID (ULID)", min_length=1, max_length=36)
    cantidad: int = Field(default=1, description="Quantity", ge=1)
    precio_unitario: Decimal = Field(description="Unit price", gt=0, decimal_places=2)
    precio_opciones: Optional[Decimal] = Field(
        default=Decimal("0.00"),
        description="Options price",
        ge=0,
        decimal_places=2
    )
    notas_personalizacion: Optional[str] = Field(
        default=None, description="Customization notes"
    )

    @field_validator('precio_unitario', 'precio_opciones', mode='before')
    @classmethod
    def validate_decimals(cls, v):
        """Validate and convert decimal values."""
        if v is None:
            return Decimal("0.00")
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class PedidoProductoCreate(PedidoProductoBase):
    """Schema for creating a new pedido producto.

    Note: subtotal is calculated automatically by the service.
    """
    pass


class PedidoProductoUpdate(BaseModel):
    """Schema for updating pedido producto.

    All fields are optional to allow partial updates.
    Note: subtotal is recalculated automatically when cantidad or prices change.
    """

    cantidad: Optional[int] = Field(default=None, description="Quantity", ge=1)
    precio_unitario: Optional[Decimal] = Field(
        default=None,
        description="Unit price",
        gt=0,
        decimal_places=2
    )
    precio_opciones: Optional[Decimal] = Field(
        default=None,
        description="Options price",
        ge=0,
        decimal_places=2
    )
    notas_personalizacion: Optional[str] = Field(
        default=None, description="Customization notes"
    )

    @field_validator('precio_unitario', 'precio_opciones', mode='before')
    @classmethod
    def validate_decimals(cls, v):
        """Validate and convert decimal values."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class PedidoProductoResponse(PedidoProductoBase):
    """Schema for pedido producto responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="PedidoProducto ID (ULID)")
    subtotal: Decimal = Field(description="Subtotal amount (calculated)")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class PedidoProductoSummary(BaseModel):
    """Schema for summarized pedido producto information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="PedidoProducto ID (ULID)")
    id_pedido: str = Field(description="Pedido ID (ULID)")
    id_producto: str = Field(description="Producto ID (ULID)")
    cantidad: int = Field(description="Quantity")
    precio_unitario: Decimal = Field(description="Unit price")
    precio_opciones: Decimal = Field(description="Options price")
    subtotal: Decimal = Field(description="Subtotal amount")


class PedidoProductoList(BaseModel):
    """Schema for paginated list of pedido productos."""

    items: List[PedidoProductoSummary]
    total: int = Field(description="Total number of pedido productos")
