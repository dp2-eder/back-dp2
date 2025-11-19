"""
Pydantic schemas for Rol (Role) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RolBase(BaseModel):
    """Base schema for Rol."""

    nombre: str = Field(description="Role name", min_length=1, max_length=50)
    descripcion: Optional[str] = Field(
        default=None, description="Role description", max_length=255
    )


class RolCreate(RolBase):
    """Schema for creating a new rol."""

    pass


class RolUpdate(BaseModel):
    """Schema for updating rol."""

    nombre: Optional[str] = Field(
        default=None, description="Role name", min_length=1, max_length=50
    )
    descripcion: Optional[str] = Field(
        default=None, description="Role description", max_length=255
    )


class RolResponse(RolBase):
    """Schema for rol responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Role ID")
    activo: bool = Field(description="Indicates if the role is active")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )
    
    
class RolSummary(BaseModel):
    """Schema for summarized rol information in lists."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Role ID")
    nombre: str = Field(description="Role name")
    activo: bool = Field(description="Indicates if the role is active")


class RolList(BaseModel):
    """Schema for paginated list of roles."""
    
    items: List[RolSummary]
    total: int = Field(description="Total number of roles")
