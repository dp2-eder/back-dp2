"""
Pydantic schemas for Zona (Zone) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ZonaBase(BaseModel):
    """Base schema for Zona."""

    nombre: str = Field(
        description="Nombre de la zona (ej: Terraza, Interior, VIP)",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripción de la zona",
        max_length=200
    )
    nivel: int = Field(
        default=0,
        description="Nivel jerárquico (0=principal, 1=sub-zona, 2=sub-sub-zona)",
        ge=0,
        le=2
    )
    capacidad_maxima: Optional[int] = Field(
        default=None,
        description="Capacidad máxima de personas",
        gt=0
    )
    id_local: str = Field(
        description="ID del local al que pertenece la zona"
    )


class ZonaCreate(ZonaBase):
    """Schema for creating a new zona."""

    pass


class ZonaUpdate(BaseModel):
    """Schema for updating zona."""

    nombre: Optional[str] = Field(
        default=None,
        description="Nombre de la zona",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripción de la zona",
        max_length=200
    )
    nivel: Optional[int] = Field(
        default=None,
        description="Nivel jerárquico (0=principal, 1=sub-zona, 2=sub-sub-zona)",
        ge=0,
        le=2
    )
    capacidad_maxima: Optional[int] = Field(
        default=None,
        description="Capacidad máxima de personas",
        gt=0
    )
    id_local: Optional[str] = Field(
        default=None,
        description="ID del local al que pertenece la zona"
    )


class LocalInfo(BaseModel):
    """Schema for local information within zona response."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Local ID")
    codigo: str = Field(description="Código del local")
    nombre: str = Field(description="Nombre del local")


class ZonaResponse(ZonaBase):
    """Schema for zona responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Zona ID")
    activo: bool = Field(description="Indica si la zona está activa")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )
    local: Optional[LocalInfo] = Field(
        default=None, description="Información del local"
    )


class ZonaSummary(BaseModel):
    """Schema for summarized zona information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Zona ID")
    nombre: str = Field(description="Nombre de la zona")
    nivel: int = Field(description="Nivel jerárquico")
    activo: bool = Field(description="Indica si la zona está activa")
    id_local: str = Field(description="ID del local")
    nombre_local: Optional[str] = Field(
        default=None, description="Nombre del local"
    )


class ZonaList(BaseModel):
    """Schema for paginated list of zonas."""

    items: List[ZonaSummary]
    total: int = Field(description="Total number of zonas")
