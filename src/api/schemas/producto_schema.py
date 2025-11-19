"""
Pydantic schemas for Producto (Product) entities.
"""

from typing import Optional, ClassVar, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

if TYPE_CHECKING:
    from src.api.schemas.producto_opcion_schema import ProductoOpcionResponse


class ProductoBase(BaseModel):
    """Base schema for Producto."""

    nombre: str = Field(description="Product name", min_length=1, max_length=255)
    descripcion: Optional[str] = Field(
        default=None, description="Product description"
    )
    precio_base: Decimal = Field(description="Base price", gt=0)
    imagen_path: Optional[str] = Field(
        default=None, description="Product image path", max_length=255
    )
    imagen_alt_text: Optional[str] = Field(
        default=None, description="Image alt text", max_length=255
    )


class ProductoCreate(ProductoBase):
    """Schema for creating a new producto."""

    id_categoria: str = Field(description="Category ID")


class ProductoUpdate(BaseModel):
    """Schema for updating producto."""

    nombre: Optional[str] = Field(
        default=None, description="Product name", min_length=1, max_length=255
    )
    descripcion: Optional[str] = Field(
        default=None, description="Product description"
    )
    precio_base: Optional[Decimal] = Field(
        default=None, description="Base price", gt=0
    )
    imagen_path: Optional[str] = Field(
        default=None, description="Product image path", max_length=255
    )
    imagen_alt_text: Optional[str] = Field(
        default=None, description="Image alt text", max_length=255
    )
    id_categoria: Optional[str] = Field(
        default=None, description="Category ID"
    )
    disponible: Optional[bool] = Field(
        default=None, description="Product availability"
    )
    destacado: Optional[bool] = Field(
        default=None, description="Featured product"
    )


class ProductoResponse(ProductoBase):
    """Schema for producto responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: str = Field(description="Product ID")
    id_categoria: str = Field(description="Category ID")
    disponible: bool = Field(description="Indicates if the product is available")
    destacado: bool = Field(description="Indicates if the product is featured")
    alergenos: List["AlergenoInfo"] = Field(default=[], description="List of allergens")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )
    
    
class ProductoSummary(BaseModel):
    """Schema for summarized producto information in lists."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Product ID")
    nombre: str = Field(description="Product name")
    imagen_path: Optional[str] = Field(default=None, description="Product image path")
    precio_base: Decimal = Field(description="Base price")
    disponible: bool = Field(description="Indicates if the product is available")


class ProductoList(BaseModel):
    """Schema for paginated list of products."""
    
    items: List[ProductoSummary]
    total: int = Field(description="Total number of products")


class ProductoOpcionDetalleSchema(BaseModel):
    """Schema for individual product option within a type."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Option ID")
    nombre: str = Field(description="Option name")
    precio_adicional: Decimal = Field(description="Additional price for this option")
    activo: bool = Field(description="Whether the option is active")
    orden: int = Field(description="Display order")
    fecha_creacion: datetime = Field(description="Creation timestamp")
    fecha_modificacion: datetime = Field(description="Last modification timestamp")


class TipoOpcionConOpcionesSchema(BaseModel):
    """Schema for option type with its grouped options."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id_tipo_opcion: str = Field(description="Option type ID")
    nombre_tipo: str = Field(description="Option type name")
    descripcion_tipo: Optional[str] = Field(
        default=None, 
        description="Option type description"
    )
    seleccion_minima: int = Field(
        default=0,
        ge=0,
        description="Minimum number of options to select (0 = optional)"
    )
    seleccion_maxima: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of options to select (null = unlimited)"
    )
    orden_tipo: int = Field(description="Display order of this type")
    opciones: List[ProductoOpcionDetalleSchema] = Field(
        default_factory=list,
        description="List of options in this type"
    )


class ProductoConOpcionesResponse(ProductoResponse):
    """
    Schema for producto with all its opciones grouped by type.
    
    Modified to include description, price, and options grouped by type.
    """
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    tipos_opciones: List[TipoOpcionConOpcionesSchema] = Field(
        default_factory=list,
        description="List of option types with their grouped options"
    )


class AlergenoInfo(BaseModel):
    """Schema for alergeno information in products."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Alergeno ID")
    nombre: str = Field(description="Alergeno name")
    icono: Optional[str] = Field(default=None, description="Alergeno icon")
    nivel_riesgo: str = Field(description="Risk level")


class CategoriaInfo(BaseModel):
    """Schema for categoria information in product cards."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Category ID")
    nombre: str = Field(description="Category name")
    imagen_path: Optional[str] = Field(default=None, description="Category image path")


class ProductoCard(BaseModel):
    """Schema for minimal product information (cards/thumbnails)."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Product ID")
    nombre: str = Field(description="Product name")
    imagen_path: Optional[str] = Field(default=None, description="Product image path")
    precio_base: Decimal = Field(description="Base price")
    categoria: CategoriaInfo = Field(description="Category information")


class ProductoCardList(BaseModel):
    """Schema for paginated list of product cards."""
    
    items: List[ProductoCard]
    total: int = Field(description="Total number of products")


# Import real después de definir las clases para evitar circular import
from src.api.schemas.producto_opcion_schema import ProductoOpcionResponse  # noqa: E402

# Actualizar forward references
ProductoConOpcionesResponse.model_rebuild()

