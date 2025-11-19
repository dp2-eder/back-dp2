"""
Modelo de relación entre Local y TipoOpcion.

Implementa la tabla intermedia que determina qué tipos de opciones están activos
en cada local, permitiendo la personalización del catálogo de opciones por local.
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index, UniqueConstraint, Boolean
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin


class LocalesTiposOpcionesModel(BaseModel, AuditMixin):
    """Modelo para la relación entre Local y TipoOpcion.

    Esta tabla intermedia permite activar/desactivar tipos de opciones por local,
    controlando qué opciones (e.g., tamaños, ingredientes) están disponibles
    en cada local.

    Attributes
    ----------
    id : str
        Identificador único ULID (heredado de BaseModel).
    id_local : str
        Identificador del local (FK).
    id_tipo_opcion : str
        Identificador del tipo de opción (FK).
    activo : bool
        Indica si este tipo de opción está activo para este local.
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "locales_tipos_opciones"

    # Claves foráneas
    id_local: Mapped[str] = mapped_column(
        ForeignKey("locales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del local"
    )
    id_tipo_opcion: Mapped[str] = mapped_column(
        ForeignKey("tipos_opciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del tipo de opción"
    )

    # Campos de configuración
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Indica si el tipo de opción está activo en este local"
    )

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('id_local', 'id_tipo_opcion', name='uq_locales_tipos_opciones'),
        Index('idx_locales_tipos_opciones_activo', 'id_local', 'activo'),
        Index('idx_locales_tipos_opciones_tipo', 'id_tipo_opcion'),
    )

    def __repr__(self) -> str:
        """Representación string del modelo para debugging."""
        return (
            f"<LocalesTiposOpcionesModel(id={self.id}, "
            f"id_local={self.id_local}, "
            f"id_tipo_opcion={self.id_tipo_opcion}, "
            f"activo={self.activo})>"
        )
