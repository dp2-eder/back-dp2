"""
Schemas para gestión de opciones de productos.
Permite listar y agregar secciones (tipos de opciones) con sus complementos (opciones).
"""

from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class OpcionComplementoInput(BaseModel):
    """Schema para crear un complemento (opción) dentro de una sección."""

    nombre: str = Field(
        description="Nombre del complemento (ej: 'Queso Extra', 'Sin Cebolla')",
        min_length=1,
        max_length=100
    )
    precio_adicional: Decimal = Field(
        default=Decimal("0.00"),
        description="Precio adicional del complemento",
        ge=0
    )
    orden: Optional[int] = Field(
        default=0,
        description="Orden de visualización"
    )


class SeccionOpcionesInput(BaseModel):
    """
    Schema para crear una sección (tipo de opción) con sus complementos.
    Una sección agrupa complementos relacionados (ej: 'Extras', 'Nivel de Ají').
    """

    nombre_seccion: str = Field(
        description="Nombre de la sección (ej: 'Extras', 'Nivel de Ají')",
        min_length=1,
        max_length=100
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripción de la sección",
        max_length=255
    )
    seleccion_minima: int = Field(
        default=0,
        description="Cantidad mínima de complementos a seleccionar (0 = opcional)",
        ge=0
    )
    seleccion_maxima: Optional[int] = Field(
        default=None,
        description="Cantidad máxima de complementos (None = sin límite)",
        ge=1
    )
    complementos: List[OpcionComplementoInput] = Field(
        description="Lista de complementos de esta sección",
        min_length=1
    )


class AgregarOpcionesProductoRequest(BaseModel):
    """
    Schema para agregar secciones de opciones a un producto.
    """

    secciones: List[SeccionOpcionesInput] = Field(
        description="Lista de secciones con sus complementos",
        min_length=1
    )


# Schemas de respuesta

class OpcionComplementoResponse(BaseModel):
    """Schema de respuesta para un complemento."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="ID del complemento")
    nombre: str = Field(description="Nombre del complemento")
    precio_adicional: Decimal = Field(description="Precio adicional")
    activo: bool = Field(description="Si el complemento está activo")
    orden: int = Field(description="Orden de visualización")


class SeccionOpcionesResponse(BaseModel):
    """Schema de respuesta para una sección con sus complementos."""

    model_config = ConfigDict(from_attributes=True)

    id_tipo_opcion: str = Field(description="ID del tipo de opción")
    nombre: str = Field(description="Nombre de la sección")
    codigo: Optional[str] = Field(default=None, description="Código interno de la sección")
    descripcion: Optional[str] = Field(default=None, description="Descripción")
    seleccion_minima: int = Field(description="Mínimo a seleccionar")
    seleccion_maxima: Optional[int] = Field(default=None, description="Máximo a seleccionar")
    orden: Optional[int] = Field(default=None, description="Orden de visualización")
    activo: bool = Field(description="Si la sección está activa")
    complementos: List[OpcionComplementoResponse] = Field(
        description="Lista de complementos de esta sección"
    )


class OpcionesProductoListResponse(BaseModel):
    """
    Schema de respuesta para listar todas las secciones de opciones de un producto.
    """

    id_producto: str = Field(description="ID del producto")
    nombre_producto: str = Field(description="Nombre del producto")
    total_secciones: int = Field(description="Total de secciones de opciones")
    secciones: List[SeccionOpcionesResponse] = Field(
        description="Lista de secciones con sus complementos"
    )


class AgregarOpcionesProductoResponse(BaseModel):
    """Schema de respuesta después de agregar opciones a un producto."""

    mensaje: str = Field(description="Mensaje de confirmación")
    secciones_creadas: int = Field(description="Número de secciones creadas")
    complementos_creados: int = Field(description="Número total de complementos creados")
    detalles: List[SeccionOpcionesResponse] = Field(
        description="Detalles de las secciones creadas"
    )
