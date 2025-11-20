"""
Pydantic schemas for ProductoAlergeno (Product-Allergen relationship) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.core.enums.alergeno_enums import NivelPresencia


class ProductoAlergenoBase(BaseModel):
    """Base schema for ProductoAlergeno."""

    id_producto: str = Field(description="Product ID")
    id_alergeno: str = Field(description="Allergen ID")
    nivel_presencia: NivelPresencia = Field(
        default=NivelPresencia.CONTIENE,
        description="Allergen presence level: contiene, trazas, puede_contener"
    )
    notas: Optional[str] = Field(
        default=None,
        description="Additional information about the allergen in this product",
        max_length=255
    )


class ProductoAlergenoCreate(ProductoAlergenoBase):
    """Schema for creating a new producto-alergeno relationship."""

    pass


class ProductoAlergenoUpdate(BaseModel):
    """Schema for updating producto-alergeno relationship."""

    nivel_presencia: Optional[NivelPresencia] = Field(
        default=None,
        description="Allergen presence level: contiene, trazas, puede_contener"
    )
    notas: Optional[str] = Field(
        default=None,
        description="Additional information about the allergen in this product",
        max_length=255
    )
    activo: Optional[bool] = Field(
        default=None,
        description="Indicates if the relationship is active"
    )


class ProductoAlergenoResponse(ProductoAlergenoBase):
    """Schema for producto-alergeno responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique relationship ID (ULID)")
    activo: bool = Field(description="Indicates if the relationship is active")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class ProductoAlergenoSummary(BaseModel):
    """Schema for summarized producto-alergeno information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Unique relationship ID (ULID)")
    id_producto: str = Field(description="Product ID")
    id_alergeno: str = Field(description="Allergen ID")
    nivel_presencia: NivelPresencia = Field(
        description="Allergen presence level"
    )
    activo: bool = Field(description="Indicates if the relationship is active")


class ProductoAlergenoList(BaseModel):
    """Schema for paginated list of producto-alergeno relationships."""

    items: List[ProductoAlergenoSummary]
    total: int = Field(description="Total number of producto-alergeno relationships")


class ProductoAlergenoUpdateInput(BaseModel):
    """Schema for allergen input in product update operations."""

    id_alergeno: str = Field(description="Allergen ID")
    nivel_presencia: NivelPresencia = Field(
        default=NivelPresencia.CONTIENE,
        description="Allergen presence level: contiene, trazas, puede_contener"
    )
    notas: Optional[str] = Field(
        default=None,
        description="Additional notes about the allergen",
        max_length=255
    )
