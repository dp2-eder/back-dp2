"""
Modelo de SQLAlchemy para la entidad DivisionCuentaDetalle.

Este módulo define el modelo de datos para el detalle de qué items
paga cada persona en una división de cuenta.
"""

from sqlalchemy import String, Integer, DECIMAL, ForeignKey, CheckConstraint, TIMESTAMP
from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from datetime import datetime
from src.models.base_model import BaseModel

if TYPE_CHECKING:
    from src.models.pagos.division_cuenta_model import DivisionCuentaModel
    from src.models.pedidos.pedido_producto_model import PedidoProductoModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="DivisionCuentaDetalleModel")


class DivisionCuentaDetalleModel(BaseModel):
    """
    Modelo para representar el detalle de división de cuenta.

    Especifica qué monto de cada item del pedido paga cada persona.

    Attributes
    ----------
    id : str
        Identificador único del detalle (ULID), heredado de BaseModel.
    id_division_cuenta : str
        Identificador de la división de cuenta (Foreign Key).
    id_pedido_producto : str
        Identificador del producto del pedido (Foreign Key).
    persona_numero : int
        Identificador de persona (1, 2, 3, etc).
    monto_asignado : Decimal
        Monto que esta persona debe pagar por este item.
    created_at : datetime
        Fecha y hora de creación del registro.
    """

    __tablename__ = "divisiones_cuentas_detalles"

    # Columnas específicas del modelo DivisionCuentaDetalle
    id_division_cuenta: Mapped[str] = mapped_column(
        String(36), ForeignKey("divisiones_cuentas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_pedido_producto: Mapped[str] = mapped_column(
        String(36), ForeignKey("pedidos_productos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    persona_numero: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Identificador de persona (1, 2, 3, etc)"
    )
    monto_asignado: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, comment="Monto que esta persona debe pagar por este item"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=True, default=datetime.utcnow
    )

    # Relaciones
    division_cuenta: Mapped["DivisionCuentaModel"] = relationship(
        "DivisionCuentaModel",
        back_populates="detalles",
        lazy="selectin"
    )

    pedido_producto: Mapped["PedidoProductoModel"] = relationship(
        "PedidoProductoModel",
        back_populates="divisiones_detalle",
        lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("monto_asignado >= 0", name="chk_monto_asignado"),
        {"comment": "Detalle de qué items paga cada persona"}
    )

    def __repr__(self):
        return f"<DivisionCuentaDetalle(id={self.id}, persona={self.persona_numero}, monto={self.monto_asignado})>"
