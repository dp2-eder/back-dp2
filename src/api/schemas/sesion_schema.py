"""
Schemas de Pydantic para la entidad Sesion.

Este módulo define las estructuras de datos para crear, actualizar y
representar las sesiones en la API.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.sesion_enums import EstadoSesion


class SesionBase(BaseModel):
    """
    Schema base con los campos comunes para una sesión.

    Attributes
    ----------
    id_domotica : str
        Identificador del sistema Domotica asociado a la sesión.
    id_local : str
        Identificador del local donde se registró la sesión.
    estado : EstadoSesion
        Estado actual de la sesión (ACTIVO, INACTIVO, CERRADO).
    """

    id_domotica: str = Field(
        description="Identificador del sistema Domotica asociado a la sesión.",
        min_length=1,
        max_length=36
    )
    id_local: str = Field(
        description="Identificador del local donde se registró la sesión.",
        min_length=1,
        max_length=36
    )
    orden: int = Field(
        default=1,
        description="Jerarquía de la sesión, 1 es la más alta."
    )    
    estado: EstadoSesion = Field(
        default=EstadoSesion.ACTIVO,
        description="Estado actual de la sesión (ACTIVO, INACTIVO, CERRADO)."
    )


class SesionCreate(SesionBase):
    """
    Schema para la creación de una nueva sesión.

    Hereda todos los campos de SesionBase y se utiliza como cuerpo
    de la petición (request body) en el endpoint de creación.
    """
    pass


class SesionUpdate(BaseModel):
    """
    Schema para la actualización parcial de una sesión.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """

    id_domotica: Optional[str] = Field(
        default=None,
        description="Nuevo identificador del sistema Domotica.",
        min_length=1,
        max_length=36
    )
    id_local: Optional[str] = Field(
        default=None,
        description="Nuevo identificador del local.",
        min_length=1,
        max_length=36
    )
    orden: Optional[int] = Field(
        default=None,
        description="Nuevo valor de jerarquía de la sesión."
    )
    estado: Optional[EstadoSesion] = Field(
        default=None,
        description="Nuevo estado de la sesión (ACTIVO, INACTIVO, CERRADO)."
    )


class SesionResponse(SesionBase):
    """
    Schema para representar una sesión en las respuestas de la API.

    Incluye campos de auditoría y de solo lectura que no se exponen en
    la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la sesión (ULID).")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación del registro."
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de la última modificación."
    )


class SesionSummary(BaseModel):
    """
    Schema con información resumida de una sesión para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la sesión (ULID).")
    id_domotica: str = Field(description="Identificador del sistema Domotica.")
    id_local: str = Field(description="Identificador del local.")
    orden: int = Field(description="Jerarquía de la sesión.")
    estado: EstadoSesion = Field(description="Estado actual de la sesión.")
    fecha_creacion: Optional[datetime] = Field(description="Fecha de creación.")
    fecha_modificacion: Optional[datetime] = Field(description="Fecha de última modificación.")


class SesionList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de sesiones."""
    items: List[SesionSummary] = Field(description="Lista de sesiones en la página actual.")
    total: int = Field(description="Número total de sesiones que coinciden con la consulta.")
