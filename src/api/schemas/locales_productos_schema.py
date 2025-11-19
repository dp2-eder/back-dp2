"""
Pydantic schemas for LocalesProductos (Local-Product relationship) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class LocalesProductosBase(BaseModel):
    """Base schema for LocalesProductos."""

    id_local: str = Field(description="Local ID")
    id_producto: str = Field(description="Product ID")
    activo: bool = Field(default=True, description="Indicates if the product is active for this local")
    precio_override: Optional[Decimal] = Field(
        default=None,
        description="Custom price for this local (NULL = use original price)",
        max_digits=10,
        decimal_places=2
    )
    disponible_override: Optional[bool] = Field(
        default=None,
        description="Custom availability for this local (NULL = use original availability)"
    )
    nombre_override: Optional[str] = Field(
        default=None,
        description="Custom name for this local (NULL = use original name)",
        max_length=100
    )
    descripcion_override: Optional[str] = Field(
        default=None,
        description="Custom description for this local (NULL = use original description)",
        max_length=500
    )


class LocalesProductosCreate(LocalesProductosBase):
    """Schema for creating a new local-product relationship."""
    pass


class LocalesProductosUpdate(BaseModel):
    """Schema for updating local-product relationship."""

    activo: Optional[bool] = Field(default=None, description="Indicates if the product is active")
    precio_override: Optional[Decimal] = Field(
        default=None,
        description="Custom price for this local",
        max_digits=10,
        decimal_places=2
    )
    disponible_override: Optional[bool] = Field(
        default=None,
        description="Custom availability for this local"
    )
    nombre_override: Optional[str] = Field(
        default=None,
        description="Custom name for this local",
        max_length=100
    )
    descripcion_override: Optional[str] = Field(
        default=None,
        description="Custom description for this local",
        max_length=500
    )


class LocalesProductosResponse(LocalesProductosBase):
    """Schema for local-product relationship responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class LocalesProductosSummary(BaseModel):
    """Schema for summarized local-product relationship information."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    id_local: str = Field(description="Local ID")
    id_producto: str = Field(description="Product ID")
    activo: bool = Field(description="Indicates if the product is active")
    precio_override: Optional[Decimal] = Field(default=None, description="Custom price")
    disponible_override: Optional[bool] = Field(default=None, description="Custom availability")
    nombre_override: Optional[str] = Field(default=None, description="Custom name")
    descripcion_override: Optional[str] = Field(default=None, description="Custom description")


class LocalesProductosListResponse(BaseModel):
    """Schema for paginated list of local-product relationships."""

    items: List[LocalesProductosSummary]
    total: int = Field(description="Total number of relationships")


# Schemas for activation/deactivation operations
class ActivarProductoRequest(BaseModel):
    """Schema for activating a product in a local with optional overrides."""

    id_producto: str = Field(description="Product ID to activate")
    precio_override: Optional[Decimal] = Field(
        default=None,
        description="Custom price (optional)",
        max_digits=10,
        decimal_places=2
    )
    disponible_override: Optional[bool] = Field(
        default=None,
        description="Custom availability (optional)"
    )
    nombre_override: Optional[str] = Field(
        default=None,
        description="Custom name (optional)",
        max_length=100
    )
    descripcion_override: Optional[str] = Field(
        default=None,
        description="Custom description (optional)",
        max_length=500
    )


class DesactivarProductoRequest(BaseModel):
    """Schema for deactivating a product in a local."""

    id_producto: str = Field(description="Product ID to deactivate")


class ActualizarOverridesRequest(BaseModel):
    """Schema for updating override values for a product in a local."""

    id_producto: str = Field(description="Product ID")
    precio_override: Optional[Decimal] = Field(
        default=None,
        description="Custom price (None = use original)",
        max_digits=10,
        decimal_places=2
    )
    disponible_override: Optional[bool] = Field(
        default=None,
        description="Custom availability (None = use original)"
    )
    nombre_override: Optional[str] = Field(
        default=None,
        description="Custom name (None = use original)",
        max_length=100
    )
    descripcion_override: Optional[str] = Field(
        default=None,
        description="Custom description (None = use original)",
        max_length=500
    )


class ActivarProductosLoteRequest(BaseModel):
    """Schema for batch activating multiple products in a local."""

    productos: List[ActivarProductoRequest] = Field(
        description="List of products to activate with their overrides"
    )


class OperacionLoteResponse(BaseModel):
    """Schema for batch operation response."""

    exitosos: int = Field(description="Number of successful operations")
    fallidos: int = Field(description="Number of failed operations")
    detalles: List[LocalesProductosResponse] = Field(
        default_factory=list,
        description="Details of successful operations"
    )
