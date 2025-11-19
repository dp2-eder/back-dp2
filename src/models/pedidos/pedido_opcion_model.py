"""
Modelo de pedido_opcion para registrar opciones aplicadas a items de pedidos.

Implementa la estructura de datos para las opciones/personalizaciones aplicadas
a cada item del pedido, adaptado para coincidir con el esquema de MySQL restaurant_dp2.pedido_opcion.
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DECIMAL, TIMESTAMP, ForeignKey
from datetime import datetime
from src.models.base_model import BaseModel

if TYPE_CHECKING:
    from src.models.pedidos.pedido_producto_model import PedidoProductoModel
    from src.models.pedidos.producto_opcion_model import ProductoOpcionModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="PedidoOpcionModel")


class PedidoOpcionModel(BaseModel):
    """Modelo para representar opciones aplicadas a items de pedidos.

    Define las opciones/personalizaciones que fueron seleccionadas para cada
    item del pedido, registrando qué producto_opcion específica se aplicó
    y su precio al momento del pedido.

    Attributes
    ----------
    id_pedido_producto : str
        Identificador del item de pedido al que se aplica esta opción (ULID).
    id_producto_opcion : str
        Identificador de la opción de producto seleccionada (ULID).
    precio_adicional : Decimal
        Precio adicional de la opción al momento del pedido.
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    creado_por : str, optional
        Usuario que creó el registro (ULID).
    modificado_por : str, optional
        Usuario que realizó la última modificación (ULID).
    """

    __tablename__ = "pedidos_opciones"

    # Foreign Keys
    id_pedido_producto: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pedidos_productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    id_producto_opcion: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("productos_opciones.id"),
        nullable=False,
        index=True
    )

    # Campos de negocio
    precio_adicional: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Precio al momento del pedido"
    )

    # Timestamps
    fecha_creacion: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.now
    )

    creado_por: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True
    )

    modificado_por: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True
    )

    # Relaciones
    pedido_producto: Mapped["PedidoProductoModel"] = relationship(
        "PedidoProductoModel",
        back_populates="pedidos_opciones",
        lazy="selectin"
    )

    producto_opcion: Mapped["ProductoOpcionModel"] = relationship(
        "ProductoOpcionModel",
        lazy="selectin"
    )

    # Métodos comunes para todos los modelos
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia del modelo a un diccionario.

        Transforma todos los atributos del modelo en un diccionario para
        facilitar su serialización y uso en APIs.

        Returns
        -------
        Dict[str, Any]
            Diccionario con los nombres de columnas como claves y sus valores correspondientes.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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
        from sqlalchemy import inspect
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
