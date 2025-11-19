"""
Modelo de relación entre Local y Categoría.

Implementa la tabla intermedia que determina qué categorías están activas
en cada local, permitiendo la personalización del catálogo por local.
"""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index, UniqueConstraint, Integer, Boolean
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin


class LocalesCategoriasModel(BaseModel, AuditMixin):
    """Modelo para la relación entre Local y Categoría.

    Esta tabla intermedia permite activar/desactivar categorías por local
    y personalizar el orden de visualización en cada local.

    Attributes
    ----------
    id : str
        Identificador único ULID (heredado de BaseModel).
    id_local : str
        Identificador del local (FK).
    id_categoria : str
        Identificador de la categoría (FK).
    activo : bool
        Indica si esta categoría está activa para este local.
    orden_override : int, optional
        Orden personalizado para este local (NULL = usar orden original).
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "locales_categorias"

    # Claves foráneas
    id_local: Mapped[str] = mapped_column(
        ForeignKey("locales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del local"
    )
    id_categoria: Mapped[str] = mapped_column(
        ForeignKey("categorias.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador de la categoría"
    )

    # Campos de configuración
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Indica si la categoría está activa en este local"
    )
    orden_override: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Orden personalizado para este local (NULL = usar orden original)"
    )

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('id_local', 'id_categoria', name='uq_locales_categorias'),
        Index('idx_locales_categorias_activo', 'id_local', 'activo'),
        Index('idx_locales_categorias_categoria', 'id_categoria'),
    )

    def __repr__(self) -> str:
        """Representación string del modelo para debugging."""
        return (
            f"<LocalesCategoriasModel(id={self.id}, "
            f"id_local={self.id_local}, "
            f"id_categoria={self.id_categoria}, "
            f"activo={self.activo}, "
            f"orden_override={self.orden_override})>"
        )
