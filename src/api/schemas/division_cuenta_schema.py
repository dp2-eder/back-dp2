"""
Schemas de Pydantic para la entidad DivisionCuenta.

Este módulo define las estructuras de datos para crear, actualizar y
representar las divisiones de cuenta en la API.
"""

from typing import Optional, ClassVar, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.pedido_enums import TipoDivision


class DivisionCuentaBase(BaseModel):
    """
    Schema base con los campos comunes para una división de cuenta.

    Attributes
    ----------
    tipo_division : TipoDivision
        Tipo de división (equitativa, por_items, manual).
    cantidad_personas : int
        Número de personas entre las que se divide la cuenta.
    notas : str, optional
        Notas adicionales sobre la división.
    """

    tipo_division: TipoDivision = Field(
        description="Tipo de división (equitativa, por_items, manual)."
    )
    cantidad_personas: int = Field(
        ge=1,
        description="Número de personas entre las que se divide la cuenta."
    )
    notas: Optional[str] = Field(
        default=None,
        description="Notas adicionales sobre la división."
    )


class DivisionCuentaCreate(DivisionCuentaBase):
    """
    Schema para la creación de una nueva división de cuenta.

    Attributes
    ----------
    id_pedido : str
        Identificador del pedido asociado.
    """

    id_pedido: str = Field(
        description="Identificador del pedido asociado.",
        min_length=1,
        max_length=36
    )


class DivisionCuentaUpdate(BaseModel):
    """
    Schema para la actualización parcial de una división de cuenta.

    Todos los campos son opcionales para permitir actualizaciones
    parciales (método PATCH).
    """

    tipo_division: Optional[TipoDivision] = Field(
        default=None,
        description="Nuevo tipo de división."
    )
    cantidad_personas: Optional[int] = Field(
        default=None,
        ge=1,
        description="Nuevo número de personas."
    )
    notas: Optional[str] = Field(
        default=None,
        description="Nuevas notas."
    )


class DivisionCuentaResponse(DivisionCuentaBase):
    """
    Schema para representar una división de cuenta en las respuestas de la API.

    Incluye campos de solo lectura que no se exponen en la creación o actualización.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la división (ULID).")
    id_pedido: str = Field(description="Identificador del pedido asociado.")
    created_at: Optional[datetime] = Field(
        default=None, description="Fecha y hora de creación."
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Fecha y hora de última modificación."
    )


class DivisionCuentaSummary(BaseModel):
    """
    Schema con información resumida de una división de cuenta para listas.

    Diseñado para ser ligero y eficiente al devolver múltiples registros.
    """
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único de la división (ULID).")
    id_pedido: str = Field(description="Identificador del pedido.")
    tipo_division: TipoDivision = Field(description="Tipo de división.")
    cantidad_personas: int = Field(description="Número de personas.")
    created_at: Optional[datetime] = Field(description="Fecha de creación.")


class DivisionCuentaList(BaseModel):
    """Schema para respuestas paginadas que contienen una lista de divisiones de cuenta."""
    items: List[DivisionCuentaSummary] = Field(description="Lista de divisiones en la página actual.")
    total: int = Field(description="Número total de divisiones que coinciden con la consulta.")
