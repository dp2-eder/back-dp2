"""
Modelo de relación entre Local y ProductoOpcion.

Implementa la tabla intermedia que determina qué opciones de producto están activas
en cada local, permitiendo override del precio adicional por local.
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index, UniqueConstraint, Boolean, Numeric
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin


class LocalesProductosOpcionesModel(BaseModel, AuditMixin):
    """Modelo para la relación entre Local y ProductoOpcion con override de precio.

    Esta tabla intermedia permite activar/desactivar opciones de producto por local
    y personalizar el precio adicional de cada opción.

    El campo precio_adicional_override es opcional: NULL = usar precio adicional original,
    NOT NULL = usar el precio personalizado para este local.

    Attributes
    ----------
    id : str
        Identificador único ULID (heredado de BaseModel).
    id_local : str
        Identificador del local (FK).
    id_producto_opcion : str
        Identificador de la opción de producto (FK).
    activo : bool
        Indica si esta opción está activa para este local.
    precio_adicional_override : Decimal, optional
        Precio adicional personalizado (NULL = usar precio adicional original).
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "locales_productos_opciones"

    # Claves foráneas
    id_local: Mapped[str] = mapped_column(
        ForeignKey("locales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del local"
    )
    id_producto_opcion: Mapped[str] = mapped_column(
        ForeignKey("productos_opciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador de la opción de producto"
    )

    # Campos de configuración
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Indica si la opción de producto está activa en este local"
    )

    # Campo de override (NULL = usar valor original)
    precio_adicional_override: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Precio adicional personalizado para este local (NULL = usar precio adicional original)"
    )

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('id_local', 'id_producto_opcion', name='uq_locales_productos_opciones'),
        Index('idx_locales_productos_opciones_activo', 'id_local', 'activo'),
        Index('idx_locales_productos_opciones_opcion', 'id_producto_opcion'),
    )

    def get_precio_adicional_efectivo(self, precio_adicional_original: Decimal) -> Decimal:
        """Obtiene el precio adicional efectivo (override o original).

        Parameters
        ----------
        precio_adicional_original : Decimal
            Precio adicional original de la opción.

        Returns
        -------
        Decimal
            Precio adicional efectivo a usar (override si existe, sino original).
        """
        return self.precio_adicional_override if self.precio_adicional_override is not None else precio_adicional_original

    def __repr__(self) -> str:
        """Representación string del modelo para debugging."""
        return (
            f"<LocalesProductosOpcionesModel(id={self.id}, "
            f"id_local={self.id_local}, "
            f"id_producto_opcion={self.id_producto_opcion}, "
            f"activo={self.activo}, "
            f"precio_adicional_override={self.precio_adicional_override})>"
        )
