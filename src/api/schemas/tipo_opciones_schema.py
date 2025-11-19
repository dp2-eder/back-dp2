"""
Schemas de Pydantic para la entidad TipoOpcion.

Este módulo define las estructuras de datos para crear, actualizar y
representar los tipos de opciones en la API.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TipoOpcionBase(BaseModel):
    """
    Schema base con los campos comunes para un tipo de opción.

    Attributes
    ----------
    codigo : str
        Código interno o identificador corto del tipo de opción (e.g. 'nivel_aji').
    nombre : str
        Nombre descriptivo del tipo de opción (e.g. 'Nivel de Ají').
    descripcion : Optional[str]
        Descripción más detallada del propósito o aplicación de este tipo de opción.
    activo : bool
        Indica si el tipo de opción está activo o no.
    orden : Optional[int]
        Orden de visualización o prioridad para mostrar este tipo.
    """
    codigo: str = Field(
        description="Código interno o identificador corto del tipo de opción.",
        min_length=1,
        max_length=50
    )
    nombre: str = Field(
        description="Nombre descriptivo del tipo de opción.",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripción detallada del tipo de opción.",
        max_length=255
    )
    activo: bool = Field(
        default=True,
        description="Indica si el tipo de opción está activo en el sistema."
    )
    orden: Optional[int] = Field(
        default=None,
        description="Orden de visualización o prioridad."
    )
    seleccion_minima: Optional[int] = Field(
        default=0,
        description="Cantidad mínima de opciones a seleccionar (0 = opcional)"
    )
    seleccion_maxima: Optional[int] = Field(
        default=None,
        description="Cantidad máxima de opciones (None = sin límite)"
    )


class TipoOpcionCreate(TipoOpcionBase):
    """
    Schema para la creación de un nuevo tipo de opción.

    Hereda todos los campos de TipoOpcionBase y se utiliza como cuerpo
    de la petición (request body) en el endpoint de creación.
    """
    pass


class TipoOpcionUpdate(BaseModel):
    """
    Schema para la actualización parcial de un tipo de opción.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """
    codigo: Optional[str] = Field(
        default=None,
        description="Nuevo código del tipo de opción.",
        min_length=1,
        max_length=50
    )
    nombre: Optional[str] = Field(
        default=None,
        description="Nuevo nombre del tipo de opción.",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Nueva descripción del tipo de opción.",
        max_length=255
    )
    activo: Optional[bool] = Field(
        default=None,
        description="Nuevo estado activo del tipo de opción."
    )
    orden: Optional[int] = Field(
        default=None,
        description="Nuevo orden de visualización."
    )
    seleccion_minima: Optional[int] = Field(
        default=None,
        description="Nueva cantidad mínima de opciones a seleccionar."
    )
    seleccion_maxima: Optional[int] = Field(
        default=None,
        description="Nueva cantidad máxima de opciones."
    )


class TipoOpcionResponse(TipoOpcionBase):
    """
    Schema para representar un tipo de opción en las respuestas de la API.

    Incluye campos de auditoría y de solo lectura que no se exponen en
    la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del tipo de opción (str).")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación del registro."
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de la última modificación."
    )


class TipoOpcionSummary(BaseModel):
    """
    Schema con información resumida de un tipo de opción para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del tipo de opción.")
    codigo: str = Field(description="Código del tipo de opción.")
    nombre: str = Field(description="Nombre del tipo de opción.")
    activo: bool = Field(description="Indica si el tipo de opción está activo.")
    orden: Optional[int] = Field(description="Orden de visualización.")
    seleccion_minima: Optional[int] = Field(default=0, description="Cantidad mínima de opciones a seleccionar (0 = opcional)")
    seleccion_maxima: Optional[int] = Field(default=None, description="Cantidad máxima de opciones (None = sin límite)")


class TipoOpcionList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de tipos de opciones."""
    items: List[TipoOpcionSummary] = Field(description="Lista de tipos de opciones en la página actual.")
    total: int = Field(description="Número total de tipos de opciones que coinciden con la consulta.")

