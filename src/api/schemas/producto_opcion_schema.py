"""
Pydantic schemas for ProductoOpcion (Product Option) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class ProductoOpcionBase(BaseModel):
    """Base schema for ProductoOpcion."""

    nombre: str = Field(
        description="Option name (e.g., 'Sin ají', 'Ají suave', 'Con choclo')", 
        min_length=1, 
        max_length=100
    )
    precio_adicional: Decimal = Field(
        default=Decimal("0.00"),
        description="Additional price for this option",
        ge=0
    )
    activo: bool = Field(
        default=True,
        description="Indicates if the option is active"
    )
    orden: Optional[int] = Field(
        default=0,
        description="Display order for the option",
        ge=0
    )


class ProductoOpcionCreate(ProductoOpcionBase):
    """Schema for creating a new producto opcion."""

    id_producto: str = Field(description="Product ID")
    id_tipo_opcion: str = Field(description="Option type ID")


class ProductoOpcionUpdate(BaseModel):
    """Schema for updating producto opcion."""

    nombre: Optional[str] = Field(
        default=None,
        description="Option name",
        min_length=1,
        max_length=100
    )
    precio_adicional: Optional[Decimal] = Field(
        default=None,
        description="Additional price for this option",
        ge=0
    )
    activo: Optional[bool] = Field(
        default=None,
        description="Indicates if the option is active"
    )
    orden: Optional[int] = Field(
        default=None,
        description="Display order for the option",
        ge=0
    )
    id_producto: Optional[str] = Field(
        default=None,
        description="Product ID"
    )
    id_tipo_opcion: Optional[str] = Field(
        default=None,
        description="Option type ID"
    )


class ProductoOpcionResponse(ProductoOpcionBase):
    """Schema for producto opcion responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Product option ID")
    id_producto: str = Field(description="Product ID")
    id_tipo_opcion: str = Field(description="Option type ID")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class ProductoOpcionSummary(BaseModel):
    """Schema for summarized producto opcion information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Product option ID")
    id_producto: str = Field(description="Product ID")
    id_tipo_opcion: str = Field(description="Option type ID")
    nombre: str = Field(description="Option name")
    precio_adicional: Decimal = Field(description="Additional price")
    activo: bool = Field(description="Indicates if the option is active")
    orden: int = Field(default=0, description="Display order for the option")


class ProductoOpcionList(BaseModel):
    """Schema for paginated list of product options."""

    items: List[ProductoOpcionSummary]
    total: int = Field(description="Total number of product options")
