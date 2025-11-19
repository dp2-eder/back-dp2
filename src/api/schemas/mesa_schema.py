"""
Schemas de Pydantic para la entidad Mesa.

Este módulo define las estructuras de datos para crear, actualizar y
representar las mesas en la API.
"""


from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.mesa_enums import EstadoMesa
from src.api.schemas.local_schema import LocalResponse

class MesaBase(BaseModel):
    """
    Schema base con los campos comunes para una mesa.

    Attributes
    ----------
    numero : str
        Numero de la mesa
    capacidad : Optional[int]
        Capacidad de la mesa.
    zona : Optional[str]
        Zona donde se encuentra la mesa.
    qr_code : Optional[str]
        Código QR asociado a la mesa para identificación rápida.
    estado : EstadoMesaEnum
        Estado actual de la mesa (libre, ocupada, reservada, fuera de servicio).
    """
    numero: str = Field(
        description="Número identificativo de la mesa.",
        min_length=1,
        max_length=20
    )
    capacidad: Optional[int] = Field(
        default=None,
        description="Capacidad de la mesa."
    )
    id_zona: Optional[str] = Field(
        default=None,
        description="ID de la zona donde se encuentra la mesa."
    )
    nota: Optional[str] = Field(
        default=None,
        description="Notas adicionales sobre la mesa."
    )
    estado: EstadoMesa = Field(
        default=EstadoMesa.DISPONIBLE,
        description="Estado actual de la mesa (libre, disponible, ocupada, reservada, fuera de servicio)."
    )


class MesaCreate(MesaBase):
    """
    Schema para la creación de una nueva mesa.

    Hereda todos los campos de MesaBase y se utiliza como cuerpo
    de la petición (request body) en el endpoint de creación.
    """
    pass


class MesaUpdate(BaseModel):
    """
    Schema para la actualización parcial de una mesa.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """
    numero: Optional[str] = Field(
        default=None,
        description="Nuevo número identificativo de la mesa.",
        min_length=1,
        max_length=20
    )
    capacidad: Optional[int] = Field(
        default=None,
        description="Nueva capacidad de la mesa."
    )
    id_zona: Optional[str] = Field(
        default=None,
        description="Nuevo ID de la zona donde se encuentra la mesa."
    )
    nota: Optional[str] = Field(
        default=None,
        description="Nueva nota de la mesa."
    )
    estado: Optional[EstadoMesa] = Field(
        default=None,
        description="Nuevo estado de la mesa (libre, disponible, ocupada, reservada, fuera de servicio)."
    )


class MesaResponse(MesaBase):
    """
    Schema para representar una mesa en las respuestas de la API.

    Incluye campos de auditoría y de solo lectura que no se exponen en
    la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la mesa (ULID).")
    activo: bool = Field(description="Indica si la mesa está activa en el sistema.")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación del registro."
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de la última modificación."
    )


class MesaSummary(BaseModel):
    """
    Schema con información resumida de una mesa para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la mesa (ULID).")
    numero: str = Field(description="Número de la mesa.")
    capacidad: Optional[int] = Field(description="Capacidad de la mesa.")
    id_zona: Optional[str] = Field(description="ID de la zona donde se encuentra la mesa.")
    nota: Optional[str] = Field(description="Notas adicionales sobre la mesa.")
    estado: EstadoMesa = Field(description="Estado actual de la mesa.")
    local: Optional[LocalResponse] = Field(default=None, description="Información del local al que pertenece esta mesa (via zona).")

class MesaList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de mesas."""
    items: List[MesaSummary] = Field(description="Lista de mesas en la página actual.")
    total: int = Field(description="Número total de mesas que coinciden con la consulta.")
