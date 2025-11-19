"""
Pydantic schemas for Local (Restaurant Location) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from src.core.enums.local_enums import TipoLocal


class LocalBase(BaseModel):
    """Base schema for Local."""

    codigo: str = Field(
        description="Código único del local (ej: CEV-001)",
        min_length=1,
        max_length=20
    )
    nombre: str = Field(
        description="Nombre del local",
        min_length=1,
        max_length=100
    )
    direccion: str = Field(
        description="Dirección física del local",
        min_length=1,
        max_length=255
    )
    distrito: Optional[str] = Field(
        default=None,
        description="Distrito donde se ubica el local",
        max_length=100
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad donde se ubica el local",
        max_length=100
    )
    telefono: Optional[str] = Field(
        default=None,
        description="Número de teléfono del local",
        max_length=20
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Correo electrónico del local"
    )
    tipo_local: TipoLocal = Field(
        description="Tipo de local (CENTRAL o SUCURSAL)"
    )
    capacidad_total: Optional[int] = Field(
        default=None,
        description="Capacidad total de personas",
        gt=0
    )
    fecha_apertura: Optional[date] = Field(
        default=None,
        description="Fecha de apertura del local"
    )


class LocalCreate(LocalBase):
    """Schema for creating a new local."""

    pass


class LocalUpdate(BaseModel):
    """Schema for updating local."""

    codigo: Optional[str] = Field(
        default=None,
        description="Código único del local",
        min_length=1,
        max_length=20
    )
    nombre: Optional[str] = Field(
        default=None,
        description="Nombre del local",
        min_length=1,
        max_length=100
    )
    direccion: Optional[str] = Field(
        default=None,
        description="Dirección física del local",
        min_length=1,
        max_length=255
    )
    distrito: Optional[str] = Field(
        default=None,
        description="Distrito donde se ubica el local",
        max_length=100
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad donde se ubica el local",
        max_length=100
    )
    telefono: Optional[str] = Field(
        default=None,
        description="Número de teléfono del local",
        max_length=20
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Correo electrónico del local"
    )
    tipo_local: Optional[TipoLocal] = Field(
        default=None,
        description="Tipo de local (CENTRAL o SUCURSAL)"
    )
    capacidad_total: Optional[int] = Field(
        default=None,
        description="Capacidad total de personas",
        gt=0
    )
    fecha_apertura: Optional[date] = Field(
        default=None,
        description="Fecha de apertura del local"
    )


class LocalResponse(LocalBase):
    """Schema for local responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Local ID")
    activo: bool = Field(description="Indica si el local está activo")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class LocalSummary(BaseModel):
    """Schema for summarized local information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Local ID")
    codigo: str = Field(description="Código del local")
    nombre: str = Field(description="Nombre del local")
    tipo_local: TipoLocal = Field(description="Tipo de local")
    activo: bool = Field(description="Indica si el local está activo")


class LocalList(BaseModel):
    """Schema for paginated list of locales."""

    items: List[LocalSummary]
    total: int = Field(description="Total number of locales")
