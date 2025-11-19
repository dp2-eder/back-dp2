"""
Pydantic schemas for SesionMesa (Mesa Session) entities.
"""

from typing import Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.sesion_mesa_enums import EstadoSesionMesa


class SesionMesaBase(BaseModel):
    """Base schema for SesionMesa."""

    id_usuario: str = Field(
        description="ID del usuario asociado a la sesión", min_length=1, max_length=36
    )
    id_mesa: str = Field(
        description="ID de la mesa donde se realiza la sesión",
        min_length=1,
        max_length=36,
    )


class SesionMesaCreate(SesionMesaBase):
    """Schema for creating a new sesion mesa."""

    pass


class SesionMesaUpdate(BaseModel):
    """Schema for updating sesion mesa."""

    estado: Optional[EstadoSesionMesa] = Field(
        default=None, description="Nuevo estado de la sesión"
    )
    fecha_fin: Optional[datetime] = Field(
        default=None, description="Fecha de finalización de la sesión"
    )


class SesionMesaResponse(SesionMesaBase):
    """Schema for sesion mesa responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Sesion Mesa ID (ULID)")
    token_sesion: str = Field(description="Token único de la sesión")
    estado: EstadoSesionMesa = Field(description="Estado actual de la sesión")
    fecha_inicio: datetime = Field(description="Fecha de inicio de la sesión")
    fecha_fin: Optional[datetime] = Field(
        default=None, description="Fecha de finalización de la sesión"
    )
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha de creación del registro"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Última modificación del registro"
    )


class SesionMesaSummary(BaseModel):
    """Schema for summarized sesion mesa information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Sesion Mesa ID (ULID)")
    token_sesion: str = Field(description="Token único de la sesión")
    id_mesa: str = Field(description="ID de la mesa")
    estado: EstadoSesionMesa = Field(description="Estado actual de la sesión")
    fecha_inicio: datetime = Field(description="Fecha de inicio de la sesión")
