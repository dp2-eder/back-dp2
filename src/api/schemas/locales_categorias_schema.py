"""
Pydantic schemas for LocalesCategorias (Local-Category relationship) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LocalesCategoriasBase(BaseModel):
    """Base schema for LocalesCategorias."""

    id_local: str = Field(description="Local ID")
    id_categoria: str = Field(description="Category ID")
    activo: bool = Field(default=True, description="Indicates if the category is active for this local")
    orden_override: Optional[int] = Field(
        default=None,
        description="Custom order for this local (NULL = use original order)"
    )


class LocalesCategoriasCreate(LocalesCategoriasBase):
    """Schema for creating a new local-category relationship."""
    pass


class LocalesCategoriasUpdate(BaseModel):
    """Schema for updating local-category relationship."""

    activo: Optional[bool] = Field(default=None, description="Indicates if the category is active")
    orden_override: Optional[int] = Field(default=None, description="Custom order for this local")


class LocalesCategoriasResponse(LocalesCategoriasBase):
    """Schema for local-category relationship responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class LocalesCategoriasSummary(BaseModel):
    """Schema for summarized local-category relationship information."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    id_local: str = Field(description="Local ID")
    id_categoria: str = Field(description="Category ID")
    activo: bool = Field(description="Indicates if the category is active")
    orden_override: Optional[int] = Field(default=None, description="Custom order")


class LocalesCategoriasListResponse(BaseModel):
    """Schema for paginated list of local-category relationships."""

    items: List[LocalesCategoriasSummary]
    total: int = Field(description="Total number of relationships")


# Schemas for activation/deactivation operations
class ActivarCategoriaRequest(BaseModel):
    """Schema for activating a category in a local."""

    id_categoria: str = Field(description="Category ID to activate")
    orden_override: Optional[int] = Field(
        default=None,
        description="Custom order for this local (optional)"
    )


class DesactivarCategoriaRequest(BaseModel):
    """Schema for deactivating a category in a local."""

    id_categoria: str = Field(description="Category ID to deactivate")


class ActivarCategoriasLoteRequest(BaseModel):
    """Schema for batch activating multiple categories in a local."""

    categorias: List[ActivarCategoriaRequest] = Field(
        description="List of categories to activate"
    )


class OperacionLoteResponse(BaseModel):
    """Schema for batch operation response."""

    exitosos: int = Field(description="Number of successful operations")
    fallidos: int = Field(description="Number of failed operations")
    detalles: List[LocalesCategoriasResponse] = Field(
        default_factory=list,
        description="Details of successful operations"
    )
