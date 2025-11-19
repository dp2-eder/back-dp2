"""
Pydantic schemas for LocalesTiposOpciones (Local-OptionType relationship) entities.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LocalesTiposOpcionesBase(BaseModel):
    """Base schema for LocalesTiposOpciones."""

    id_local: str = Field(description="Local ID")
    id_tipo_opcion: str = Field(description="Option type ID")
    activo: bool = Field(default=True, description="Indicates if the option type is active for this local")


class LocalesTiposOpcionesCreate(LocalesTiposOpcionesBase):
    """Schema for creating a new local-option_type relationship."""
    pass


class LocalesTiposOpcionesUpdate(BaseModel):
    """Schema for updating local-option_type relationship."""

    activo: Optional[bool] = Field(default=None, description="Indicates if the option type is active")


class LocalesTiposOpcionesResponse(LocalesTiposOpcionesBase):
    """Schema for local-option_type relationship responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Last modification timestamp"
    )


class LocalesTiposOpcionesSummary(BaseModel):
    """Schema for summarized local-option_type relationship information."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Relationship ID")
    id_local: str = Field(description="Local ID")
    id_tipo_opcion: str = Field(description="Option type ID")
    activo: bool = Field(description="Indicates if the option type is active")


class LocalesTiposOpcionesListResponse(BaseModel):
    """Schema for paginated list of local-option_type relationships."""

    items: List[LocalesTiposOpcionesSummary]
    total: int = Field(description="Total number of relationships")


# Schemas for activation/deactivation operations
class ActivarTipoOpcionRequest(BaseModel):
    """Schema for activating an option type in a local."""

    id_tipo_opcion: str = Field(description="Option type ID to activate")


class DesactivarTipoOpcionRequest(BaseModel):
    """Schema for deactivating an option type in a local."""

    id_tipo_opcion: str = Field(description="Option type ID to deactivate")


class ActivarTiposOpcionesLoteRequest(BaseModel):
    """Schema for batch activating multiple option types in a local."""

    tipos_opciones: List[ActivarTipoOpcionRequest] = Field(
        description="List of option types to activate"
    )


class OperacionLoteResponse(BaseModel):
    """Schema for batch operation response."""

    exitosos: int = Field(description="Number of successful operations")
    fallidos: int = Field(description="Number of failed operations")
    detalles: List[LocalesTiposOpcionesResponse] = Field(
        default_factory=list,
        description="Details of successful operations"
    )
