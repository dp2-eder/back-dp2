"""
Schemas extendidos para respuestas detalladas de pedidos con productos y opciones completos.
"""

from typing import List, Optional, ClassVar
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from src.core.enums.pedido_enums import EstadoPedido


class ProductoDetalleResponse(BaseModel):
    """Schema para información completa del producto en un pedido."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="ID del producto (ULID)")
    nombre: str = Field(description="Nombre del producto")
    descripcion: Optional[str] = Field(default=None, description="Descripción del producto")
    precio_base: Decimal = Field(description="Precio base del producto")
    disponible: bool = Field(description="Indica si el producto está disponible")
    id_categoria: str = Field(description="ID de la categoría")


class OpcionDetalleResponse(BaseModel):
    """Schema para información completa de una opción de producto."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="ID de la opción (ULID)")
    id_pedido_producto: str = Field(description="ID del producto del pedido")
    id_producto_opcion: str = Field(description="ID de la opción de producto")
    precio_adicional: Decimal = Field(description="Precio adicional de la opción")
    # Información adicional de la opción
    nombre_opcion: Optional[str] = Field(default=None, description="Nombre de la opción")
    descripcion_opcion: Optional[str] = Field(default=None, description="Descripción de la opción")


class PedidoProductoDetalladoResponse(BaseModel):
    """Schema para un producto dentro de un pedido con toda su información."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="ID del pedido producto (ULID)")
    id_pedido: str = Field(description="ID del pedido")
    id_producto: str = Field(description="ID del producto")
    cantidad: int = Field(description="Cantidad solicitada")
    precio_unitario: Decimal = Field(description="Precio unitario del producto")
    precio_opciones: Decimal = Field(description="Precio total de las opciones")
    subtotal: Decimal = Field(description="Subtotal del item")
    notas_personalizacion: Optional[str] = Field(default=None, description="Notas de personalización")

    # Datos completos del producto
    producto: Optional[ProductoDetalleResponse] = Field(default=None, description="Información completa del producto")

    # Opciones del producto con sus detalles
    opciones: List[OpcionDetalleResponse] = Field(default=[], description="Lista de opciones seleccionadas con su información")


class PedidoDetalladoResponse(BaseModel):
    """Schema para respuesta detallada de pedido con productos y opciones completos."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    # Datos básicos del pedido
    id: str = Field(description="Pedido ID (ULID)")
    id_mesa: str = Field(description="Mesa ID")
    id_usuario: str = Field(description="Usuario ID")
    numero_pedido: str = Field(description="Número único del pedido")
    estado: EstadoPedido = Field(description="Estado actual del pedido")
    subtotal: Decimal = Field(description="Subtotal del pedido")
    impuestos: Optional[Decimal] = Field(default=None, description="Impuestos aplicados")
    descuentos: Optional[Decimal] = Field(default=None, description="Descuentos aplicados")
    total: Decimal = Field(description="Total del pedido")
    notas_cliente: Optional[str] = Field(default=None, description="Notas del cliente")
    notas_cocina: Optional[str] = Field(default=None, description="Notas para la cocina")

    # Timestamps
    fecha_creacion: Optional[datetime] = Field(default=None, description="Fecha de creación")
    fecha_modificacion: Optional[datetime] = Field(default=None, description="Última modificación")
    fecha_confirmado: Optional[datetime] = Field(default=None, description="Fecha de confirmación")
    fecha_en_preparacion: Optional[datetime] = Field(default=None, description="Fecha en preparación")
    fecha_listo: Optional[datetime] = Field(default=None, description="Fecha listo")
    fecha_entregado: Optional[datetime] = Field(default=None, description="Fecha entregado")
    fecha_cancelado: Optional[datetime] = Field(default=None, description="Fecha cancelado")

    # Lista de productos con toda su información
    productos: List[PedidoProductoDetalladoResponse] = Field(default=[], description="Lista completa de productos del pedido")


class PedidoDetalladoList(BaseModel):
    """Schema para lista paginada de pedidos detallados."""

    items: List[PedidoDetalladoResponse] = Field(description="Lista de pedidos detallados")
    total: int = Field(description="Número total de pedidos")
