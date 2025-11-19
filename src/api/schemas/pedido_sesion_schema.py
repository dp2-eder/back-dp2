"""
Schemas para pedidos con token de sesión de mesa.

Este módulo define los schemas para crear pedidos usando el token de sesión
compartido de una mesa, sin necesidad de enviar precios desde el frontend.
Los precios se obtienen automáticamente desde la base de datos.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from src.core.enums.pedido_enums import EstadoPedido


class OpcionProductoSesion(BaseModel):
    """
    Opción seleccionada para un producto (solo ID).

    El precio adicional se obtiene automáticamente desde la BD.
    """

    id_producto_opcion: str = Field(
        description="ID de la opción seleccionada (ULID)",
        min_length=26,
        max_length=26
    )

    @field_validator('id_producto_opcion')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Valida que el ID sea un ULID válido."""
        if not v.isalnum():
            raise ValueError("ID debe ser alfanumérico (ULID)")
        return v.upper()


class PedidoItemSesion(BaseModel):
    """
    Item de pedido para envío con token de sesión.

    Solo incluye IDs y cantidades. Los precios se calculan desde la BD.
    """

    id_producto: str = Field(
        description="ID del producto (ULID)",
        min_length=26,
        max_length=26
    )

    cantidad: int = Field(
        default=1,
        ge=1,
        le=99,
        description="Cantidad del producto (1-99)"
    )

    opciones: List[OpcionProductoSesion] = Field(
        default_factory=list,
        description="Lista de opciones seleccionadas para este producto"
    )

    notas_personalizacion: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Notas de personalización del producto (ej: sin cebolla, término medio)"
    )

    @field_validator('id_producto')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Valida que el ID sea un ULID válido."""
        if not v.isalnum():
            raise ValueError("ID debe ser alfanumérico (ULID)")
        return v.upper()

    @field_validator('notas_personalizacion')
    @classmethod
    def validate_notas(cls, v: Optional[str]) -> Optional[str]:
        """Limpia notas vacías."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class PedidoEnviarRequest(BaseModel):
    """
    Schema para crear un pedido con token de sesión.

    El sistema calculará automáticamente los precios desde la BD.
    No se requiere enviar precios desde el frontend.

    Attributes
    ----------
    token_sesion : str
        Token de sesión de mesa compartido (ULID de 26 caracteres)
    items : List[PedidoItemSesion]
        Lista de productos a pedir (mínimo 1)
    notas_cliente : Optional[str]
        Notas del cliente (alergias, preferencias especiales)
    notas_cocina : Optional[str]
        Instrucciones para la cocina (urgente, sin sal, etc.)
    """

    token_sesion: str = Field(
        min_length=26,
        max_length=26,
        description="Token de sesión de mesa compartido (ULID)"
    )

    items: List[PedidoItemSesion] = Field(
        min_length=1,
        description="Items del pedido (mínimo 1 producto)"
    )

    notas_cliente: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notas del cliente (alergias, preferencias especiales, dietas)"
    )

    notas_cocina: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Instrucciones para la cocina (urgente, sin sal, temperatura, etc.)"
    )

    @field_validator('token_sesion')
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Valida que el token sea un ULID válido."""
        if not v.isalnum():
            raise ValueError("Token debe ser alfanumérico (ULID)")
        return v.upper()

    @field_validator('notas_cliente', 'notas_cocina')
    @classmethod
    def validate_notas(cls, v: Optional[str]) -> Optional[str]:
        """Limpia notas vacías."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ProductoOpcionDetalle(BaseModel):
    """
    Detalle de una opción en el historial de pedidos.

    Incluye el precio adicional calculado desde la BD.
    """

    id: str = Field(description="ID de la asociación pedido-opción")
    id_producto_opcion: str = Field(description="ID de la opción")
    nombre_opcion: str = Field(description="Nombre de la opción")
    precio_adicional: Decimal = Field(
        description="Precio adicional de la opción",
        decimal_places=2
    )


class ProductoPedidoDetalle(BaseModel):
    """
    Detalle de un producto en el historial de pedidos.

    Incluye todos los precios calculados desde la BD.
    """

    id: str = Field(description="ID del pedido-producto")
    id_producto: str = Field(description="ID del producto")
    nombre_producto: str = Field(description="Nombre del producto")
    cantidad: int = Field(description="Cantidad pedida")
    precio_unitario: Decimal = Field(
        description="Precio unitario base del producto",
        decimal_places=2
    )
    precio_opciones: Decimal = Field(
        description="Suma de precios adicionales de opciones",
        decimal_places=2
    )
    subtotal: Decimal = Field(
        description="Subtotal del item (cantidad * (precio_unitario + precio_opciones))",
        decimal_places=2
    )
    notas_personalizacion: Optional[str] = Field(
        default=None,
        description="Notas de personalización del producto"
    )
    opciones: List[ProductoOpcionDetalle] = Field(
        description="Lista de opciones seleccionadas"
    )


class PedidoHistorialDetalle(BaseModel):
    """
    Detalle completo de un pedido en el historial.

    Incluye todos los datos del pedido y sus productos.
    """

    id: str = Field(description="ID del pedido")
    numero_pedido: str = Field(description="Número de pedido (formato: YYYYMMDD-M#-SEQ)")
    estado: EstadoPedido = Field(description="Estado actual del pedido")

    # Montos
    subtotal: Decimal = Field(description="Subtotal antes de impuestos/descuentos", decimal_places=2)
    impuestos: Decimal = Field(description="Monto de impuestos", decimal_places=2)
    descuentos: Decimal = Field(description="Monto de descuentos", decimal_places=2)
    total: Decimal = Field(description="Total final del pedido", decimal_places=2)

    # Notas
    notas_cliente: Optional[str] = Field(default=None, description="Notas del cliente")
    notas_cocina: Optional[str] = Field(default=None, description="Notas para cocina")

    # Timestamps
    fecha_creacion: datetime = Field(description="Fecha de creación del pedido")
    fecha_confirmado: Optional[datetime] = Field(default=None, description="Fecha de confirmación")
    fecha_en_preparacion: Optional[datetime] = Field(default=None, description="Fecha que entró en preparación")
    fecha_listo: Optional[datetime] = Field(default=None, description="Fecha que estuvo listo")
    fecha_entregado: Optional[datetime] = Field(default=None, description="Fecha de entrega")

    # Productos
    productos: List[ProductoPedidoDetalle] = Field(description="Lista de productos del pedido")


class PedidoHistorialResponse(BaseModel):
    """
    Respuesta del historial de pedidos por token de sesión.

    Incluye metadatos de la sesión y lista de pedidos.
    """

    token_sesion: str = Field(description="Token de sesión de mesa")
    id_mesa: str = Field(description="ID de la mesa")
    total_pedidos: int = Field(description="Total de pedidos en la sesión")
    pedidos: List[PedidoHistorialDetalle] = Field(description="Lista de pedidos")


class PedidoEnviarResponse(BaseModel):
    """
    Respuesta exitosa al enviar un pedido con token de sesión.

    Incluye el pedido creado con todos los cálculos.
    """

    status: int = Field(default=201, description="HTTP status code")
    message: str = Field(default="Pedido creado exitosamente", description="Mensaje")
    pedido: PedidoHistorialDetalle = Field(description="Detalle del pedido creado")
