"""
Pydantic schemas for Categoria (Category) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CategoriaBase(BaseModel):
    """Base schema for Categoria."""

    nombre: str = Field(description="Category name", min_length=1, max_length=100)
    descripcion: Optional[str] = Field(
        default=None, 
        description="Category description",
        max_length=1000  # Límite razonable para Text
    )
    imagen_path: Optional[str] = Field(
        default=None, 
        description="Category image path", 
        max_length=255
    )


class CategoriaCreate(CategoriaBase):
    """Schema for creating a new categoria."""
    
    pass


class CategoriaUpdate(BaseModel):
    """Schema for updating categoria."""

    nombre: Optional[str] = Field(
        default=None, 
        description="Category name", 
        min_length=1, 
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None, 
        description="Category description",
        max_length=1000
    )
    imagen_path: Optional[str] = Field(
        default=None, 
        description="Category image path", 
        max_length=255
    )
    # NOTA: activo se maneja por endpoint separado (como en rol_schema)


class CategoriaResponse(CategoriaBase):
    """Schema for categoria responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Category ID")
    activo: bool = Field(description="Indicates if the category is active")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class CategoriaSummary(BaseModel):
    """Schema for summarized categoria information in lists."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Category ID")
    nombre: str = Field(description="Category name")
    descripcion: Optional[str] = Field(default=None, description="Category description")
    imagen_path: Optional[str] = Field(default=None, description="Category image path")
    activo: bool = Field(description="Indicates if the category is active")


class CategoriaList(BaseModel):
    """Schema for paginated list of categorias."""
    
    items: List[CategoriaSummary]
    total: int = Field(description="Total number of categorias")


# ===== SCHEMAS PARA CARDS (SOLO ID, NOMBRE, IMAGEN) =====

class ProductoCardMinimal(BaseModel):
    """Schema minimal para producto (solo ID, nombre, imagen)."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Product ID")
    nombre: str = Field(description="Product name")
    imagen_path: Optional[str] = Field(default=None, description="Product image path")


class CategoriaConProductosCard(BaseModel):
    """Schema para categoría con sus productos (solo ID, nombre, imagen)."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Category ID")
    nombre: str = Field(description="Category name")
    imagen_path: Optional[str] = Field(default=None, description="Category image path")
    productos: List[ProductoCardMinimal] = Field(default_factory=list, description="Products in this category")


class CategoriaConProductosCardList(BaseModel):
    """Schema para lista de categorías con sus productos."""
    
    items: List[CategoriaConProductosCard]
    total: int = Field(description="Total number of categories")
