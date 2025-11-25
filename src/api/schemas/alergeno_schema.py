"""
Schemas de Pydantic para la entidad Alergeno.

Este módulo define las estructuras de datos para crear, actualizar y
representar los alérgenos en la API.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.alergeno_enums import NivelRiesgo


class AlergenoBase(BaseModel):
    """
    Schema base con los campos comunes para un alérgeno.

    Attributes
    ----------
    nombre : str
        Nombre del alérgeno (ej: "Gluten", "Lactosa").
    descripcion : Optional[str]
        Descripción detallada sobre el alérgeno y sus efectos.
    icono : Optional[str]
        Representación visual (emoji o nombre de icono) para la interfaz.
    nivel_riesgo : NivelRiesgo
        Nivel de peligrosidad o riesgo asociado al alérgeno.
    """
    nombre: str = Field(
        description="Nombre identificativo del alérgeno.",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Texto descriptivo sobre el alérgeno."
    )
    icono: Optional[str] = Field(
        default=None,
        description="Icono o emoji para representar el alérgeno en la UI.",
        max_length=50
    )
    nivel_riesgo: NivelRiesgo = Field(
        default=NivelRiesgo.MEDIO,
        description="Nivel de riesgo asociado al alérgeno (Bajo, Medio, Alto)."
    )


class AlergenoCreate(AlergenoBase):
    """
    Schema para la creación de un nuevo alérgeno.

    Hereda todos los campos de AlergenoBase y se utiliza como cuerpo
    de la petición (request body) en el endpoint de creación.
    """
    pass


class AlergenoUpdate(BaseModel):
    """
    Schema para la actualización parcial de un alérgeno.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """
    nombre: Optional[str] = Field(
        default=None,
        description="Nuevo nombre del alérgeno.",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Nueva descripción del alérgeno."
    )
    icono: Optional[str] = Field(
        default=None,
        description="Nuevo icono o emoji del alérgeno.",
        max_length=50
    )
    nivel_riesgo: Optional[NivelRiesgo] = Field(
        default=None,
        description="Nuevo nivel de riesgo del alérgeno."
    )


class AlergenoResponse(AlergenoBase):
    """
    Schema para representar un alérgeno en las respuestas de la API.

    Incluye campos de auditoría y de solo lectura que no se exponen en
    la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del alérgeno (UUID).")
    activo: bool = Field(description="Indica si el alérgeno está activo en el sistema.")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación del registro."
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Fecha y hora de la última modificación."
    )


class AlergenoSummary(BaseModel):
    """
    Schema con información resumida de un alérgeno para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único del alérgeno.")
    nombre: str = Field(description="Nombre del alérgeno.")
    nivel_riesgo: NivelRiesgo = Field(description="Nivel de riesgo asociado.")
    activo: bool = Field(description="Indica si el alérgeno está activo.")


class AlergenoList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de alérgenos."""
    items: List[AlergenoSummary] = Field(description="Lista de alérgenos en la página actual.")
    total: int = Field(description="Número total de alérgenos que coinciden con la consulta.")


class ProductoAlergeno(BaseModel):
    """Schema detallado para la relación producto-alérgeno con metadatos."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
    
    id: str = Field(description="ID del alérgeno")
    nombre: str = Field(description="Nombre del alérgeno")
    icono: Optional[str] = Field(default=None, description="Icono del alérgeno")
    nivel_riesgo: NivelRiesgo = Field(description="Nivel de riesgo")
    nivel_presencia: str = Field(description="Nivel de presencia en el producto (contiene, trazas, puede_contener)")
    notas: Optional[str] = Field(default=None, description="Notas adicionales sobre el alérgeno en este producto")
