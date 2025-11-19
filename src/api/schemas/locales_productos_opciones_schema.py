"""
Pydantic schemas for LocalesProductosOpciones (Local-ProductOption relationship) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class LocalesProductosOpcionesBase(BaseModel):
    """Base schema for LocalesProductosOpciones."""

    id_local: str = Field(description="Local ID")
    id_producto_opcion: str = Field(description="Product option ID")
    activo: bool = Field(default=True, description="Indicates if the product option is active for this local")
    precio_adicional_override: Optional[Decimal] = Field(
        default=None,
        description="Custom additional price for this local (NULL = use original additional price)",
        max_digits=10,
        decimal_places=2
    )


class LocalesProductosOpcionesCreate(LocalesProductosOpcionesBase):
    """Schema for creating a new local-product_option relationship."""
    pass


class LocalesProductosOpcionesUpdate(BaseModel):
    """Schema for updating local-product_option relationship."""

    activo: Optional[bool] = Field(default=None, description="Indicates if the product option is active")
    precio_adicional_override: Optional[Decimal] = Field(
        default=None,
        description="Custom additional price for this local",
        max_digits=10,
        decimal_places=2
    )


class LocalesProductosOpcionesResponse(LocalesProductosOpcionesBase):
    """Schema for local-product_option relationship responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class LocalesProductosOpcionesSummary(BaseModel):
    """Schema for summarized local-product_option relationship information."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    id_local: str = Field(description="Local ID")
    id_producto_opcion: str = Field(description="Product option ID")
    activo: bool = Field(description="Indicates if the product option is active")
    precio_adicional_override: Optional[Decimal] = Field(
        default=None,
        description="Custom additional price"
    )


class LocalesProductosOpcionesListResponse(BaseModel):
    """Schema for paginated list of local-product_option relationships."""

    items: List[LocalesProductosOpcionesSummary]
    total: int = Field(description="Total number of relationships")


# Schemas for activation/deactivation operations
class ActivarProductoOpcionRequest(BaseModel):
    """Schema for activating a product option in a local with optional price override."""

    id_producto_opcion: str = Field(description="Product option ID to activate")
    precio_adicional_override: Optional[Decimal] = Field(
        default=None,
        description="Custom additional price (optional)",
        max_digits=10,
        decimal_places=2
    )


class DesactivarProductoOpcionRequest(BaseModel):
    """Schema for deactivating a product option in a local."""

    id_producto_opcion: str = Field(description="Product option ID to deactivate")


class ActualizarPrecioAdicionalRequest(BaseModel):
    """Schema for updating additional price override for a product option in a local."""

    id_producto_opcion: str = Field(description="Product option ID")
    precio_adicional_override: Optional[Decimal] = Field(
        default=None,
        description="Custom additional price (None = use original)",
        max_digits=10,
        decimal_places=2
    )


class ActivarProductosOpcionesLoteRequest(BaseModel):
    """Schema for batch activating multiple product options in a local."""

    productos_opciones: List[ActivarProductoOpcionRequest] = Field(
        description="List of product options to activate with their price overrides"
    )


class OperacionLoteResponse(BaseModel):
    """Schema for batch operation response."""

    exitosos: int = Field(description="Number of successful operations")
    fallidos: int = Field(description="Number of failed operations")
    detalles: List[LocalesProductosOpcionesResponse] = Field(
        default_factory=list,
        description="Details of successful operations"
    )
