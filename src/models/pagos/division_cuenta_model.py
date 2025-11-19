"""
Modelo de SQLAlchemy para la entidad DivisionCuenta.

Este módulo define el modelo de datos para la configuración de división
de cuenta entre múltiples personas.
"""

from sqlalchemy import String, Integer, Text, Enum as SQLEnum, ForeignKey, CheckConstraint, TIMESTAMP
from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.models.base_model import BaseModel
from src.core.enums.pedido_enums import TipoDivision

if TYPE_CHECKING:
    from src.models.pedidos.pedido_model import PedidoModel
    from src.models.pagos.division_cuenta_detalle_model import DivisionCuentaDetalleModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="DivisionCuentaModel")


class DivisionCuentaModel(BaseModel):
    """
    Modelo para representar la configuración de división de cuenta.

    Registra cómo se divide una cuenta entre múltiples personas,
    ya sea de forma equitativa, por items o manual.

    Attributes
    ----------
    id : str
        Identificador único de la división de cuenta (ULID), heredado de BaseModel.
    id_pedido : str
        Identificador del pedido asociado (Foreign Key).
    tipo_division : TipoDivision
        Tipo de división (equitativa, por_items, manual).
    cantidad_personas : int
        Número de personas entre las que se divide la cuenta.
    notas : str, optional
        Notas adicionales sobre la división.
    created_at : datetime
        Fecha y hora de creación del registro.
    updated_at : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "divisiones_cuentas"

    # Columnas específicas del modelo DivisionCuenta
    id_pedido: Mapped[str] = mapped_column(
        String(36), ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_division: Mapped[TipoDivision] = mapped_column(
        SQLEnum(TipoDivision), nullable=False
    )
    cantidad_personas: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    notas: Mapped[str] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=True, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relaciones
    pedido: Mapped["PedidoModel"] = relationship(
        "PedidoModel",
        back_populates="divisiones_cuenta",
        lazy="selectin"
    )

    detalles: Mapped[List["DivisionCuentaDetalleModel"]] = relationship(
        "DivisionCuentaDetalleModel",
        back_populates="division_cuenta",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("cantidad_personas > 0", name="chk_cantidad_personas"),
        {"comment": "Configuración de división de cuenta"}
    )

    def __repr__(self):
        return f"<DivisionCuenta(id={self.id}, id_pedido={self.id_pedido}, tipo={self.tipo_division}, personas={self.cantidad_personas})>"
