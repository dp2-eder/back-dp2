"""
Modelo de SQLAlchemy para la entidad Sesion.

Este módulo define el modelo de datos para las sesiones de sincronización
entre el sistema Domotica y los locales.
"""

from sqlalchemy import String, Enum as SQLEnum, ForeignKey, Index
from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.mixins.audit_mixin import AuditMixin
from src.models.base_model import BaseModel
from src.core.enums.sesion_enums import EstadoSesion

if TYPE_CHECKING:
    from src.models.mesas.local_model import LocalModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="SesionModel")


class SesionModel(BaseModel, AuditMixin):
    """
    Modelo para representar sesiones en el sistema.

    Registra las sesiones de sincronización o actividad entre el sistema
    Domotica y los locales.

    Attributes
    ----------
    id : str
        Identificador único de la sesión (ULID), heredado de BaseModel.
    id_domotica : str
        Identificador del sistema Domotica asociado a la sesión.
    id_local : str
        Identificador del local donde se registró la sesión (Foreign Key).
    estado : EstadoSesion
        Estado actual de la sesión (ACTIVO, INACTIVO, CERRADO).
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "sesiones"

    # Columnas específicas del modelo Sesion
    id_domotica: Mapped[str] = mapped_column(
        String(36), nullable=False, index=False, comment="Identificador del sistema Domotica asociado a la sesión"
    )
    id_local: Mapped[str] = mapped_column(
        String(36), ForeignKey("locales.id", ondelete="CASCADE"), nullable=False, index=True, comment="Identificador del local donde se registró la sesión"
    )
    orden: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        index=True,
        comment="Jerarquía de la sesión, 1 es la más alta"
    )
    estado: Mapped[EstadoSesion] = mapped_column(
        SQLEnum(EstadoSesion), nullable=False, default=EstadoSesion.ACTIVO, index=True, comment="Estado actual de la sesión"
    )

    # Relación con Local
    local: Mapped["LocalModel"] = relationship(
        "LocalModel",
        back_populates="sesiones",
        lazy="selectin"
    )

    # Índices adicionales (ya definidos en las columnas con index=True)
    __table_args__ = (
        Index("idx_sesion_local", "id_local"),
        Index("idx_sesion_estado", "estado"),
        {"comment": "Registra las sesiones de sincronización o actividad entre el sistema Domotica y los locales."}
    )

    def __repr__(self):
        return f"<Sesion(id={self.id}, id_domotica={self.id_domotica}, id_local={self.id_local}, estado={self.estado})>"
