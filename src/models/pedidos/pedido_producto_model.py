"""
Modelo de items/productos de pedidos del restaurante.

Implementa la estructura de datos para los productos incluidos en cada pedido,
adaptado para coincidir con el esquema existente de MySQL restaurant_dp2.pedido_producto.
"""

from typing import Any, Dict, Optional, Type, TypeVar, List, TYPE_CHECKING
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from sqlalchemy import String, Text, Numeric, TIMESTAMP, Integer, ForeignKey, CheckConstraint, inspect, func
from src.models.base_model import BaseModel

if TYPE_CHECKING:
    from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel
    from src.models.pedidos.pedido_model import PedidoModel
    from src.models.menu.producto_model import ProductoModel
    from src.models.pedidos.pedido_opcion_model import PedidoOpcionModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="PedidoProductoModel")


class PedidoProductoModel(BaseModel):
    """Modelo para representar items/productos en pedidos del sistema.

    Define los productos individuales que forman parte de un pedido,
    incluyendo cantidad, precios y personalizaciones.

    Attributes
    ----------
    id : str
        Identificador único ULID del item (heredado de BaseModel).
    id_pedido : str
        Identificador ULID del pedido al que pertenece el item.
    id_producto : str
        Identificador ULID del producto ordenado.
    cantidad : int
        Cantidad de unidades del producto (default 1, >= 1).
    precio_unitario : Decimal
        Precio base del producto al momento de la orden.
    precio_opciones : Decimal
        Suma de opciones adicionales seleccionadas.
    subtotal : Decimal
        Subtotal calculado: cantidad * (precio_unitario + precio_opciones).
    notas_personalizacion : str, optional
        Notas libres del cliente sobre personalizaciones.
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "pedidos_productos"

    # Foreign Keys
    id_pedido: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    id_producto: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Campos específicos del modelo
    cantidad: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )

    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Precio base del producto"
    )

    precio_opciones: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Suma de opciones adicionales"
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="cantidad * (precio_unitario + precio_opciones)"
    )

    notas_personalizacion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas libres del cliente"
    )

    # Timestamps (sin creado_por/modificado_por)
    @declared_attr
    def fecha_creacion(cls) -> Mapped[datetime]:
        return mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    @declared_attr
    def fecha_modificacion(cls) -> Mapped[datetime]:
        return mapped_column(
            TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
        )

    # Relaciones
    pedido: Mapped["PedidoModel"] = relationship(
        "PedidoModel",
        back_populates="pedidos_productos",
        lazy="selectin"
    )

    producto: Mapped["ProductoModel"] = relationship(
        "ProductoModel",
        lazy="selectin"
    )

    pedidos_opciones: Mapped[List["PedidoOpcionModel"]] = relationship(
        "PedidoOpcionModel",
        back_populates="pedido_producto",
        cascade="all, delete-orphan",
        lazy="select"
    )

    divisiones_detalle: Mapped[List["DivisionCuentaDetalleModel"]] = relationship(
        "DivisionCuentaDetalleModel",
        back_populates="pedido_producto",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("cantidad >= 1", name="chk_pedidos_producto_cantidad_minima"),
        CheckConstraint("precio_unitario > 0", name="chk_pedidos_producto_precio_unitario_positivo"),
        CheckConstraint("precio_opciones >= 0", name="chk_pedidos_producto_precio_opciones_positivo"),
        CheckConstraint("subtotal >= 0", name="chk_pedidos_producto_subtotal_positivo"),
    )

    # Métodos
    def calcular_subtotal(self) -> Decimal:
        """
        Calcula el subtotal del item.

        Returns
        -------
        Decimal
            Subtotal calculado como cantidad * (precio_unitario + precio_opciones).
        """
        return Decimal(str(self.cantidad)) * (self.precio_unitario + self.precio_opciones)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia del modelo a un diccionario.

        Transforma todos los atributos del modelo en un diccionario para
        facilitar su serialización y uso en APIs.

        Returns
        -------
        Dict[str, Any]
            Diccionario con los nombres de columnas como claves y sus valores correspondientes.
        """
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            # Convertir Decimal a float para serialización JSON
            if isinstance(value, Decimal):
                value = float(value)
            result[c.name] = value
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Crea una instancia del modelo a partir de un diccionario.

        Parameters
        ----------
        data : Dict[str, Any]
            Diccionario con los datos para crear la instancia.

        Returns
        -------
        T
            Nueva instancia del modelo con los datos proporcionados.
        """
        return cls(
            **{k: v for k, v in data.items() if k in inspect(cls).columns.keys()}
        )

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza la instancia con datos de un diccionario.

        Parameters
        ----------
        data : Dict[str, Any]
            Diccionario con los datos para actualizar la instancia.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return f"<PedidoProducto(id={self.id}, id_pedido={self.id_pedido}, id_producto={self.id_producto}, cantidad={self.cantidad}, subtotal={self.subtotal})>"
