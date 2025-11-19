"""
Modelo de relación entre Local y Producto.

Implementa la tabla intermedia que determina qué productos están activos
en cada local, permitiendo overrides de precio, nombre, descripción y disponibilidad.
"""

from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Index, UniqueConstraint, Boolean, String, Numeric
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin


class LocalesProductosModel(BaseModel, AuditMixin):
    """Modelo para la relación entre Local y Producto con campos de override.

    Esta tabla intermedia permite activar/desactivar productos por local
    y personalizar sus atributos (precio, nombre, descripción, disponibilidad).

    Los campos *_override son opcionales: NULL = usar valor original del producto,
    NOT NULL = usar el valor personalizado para este local.

    Attributes
    ----------
    id : str
        Identificador único ULID (heredado de BaseModel).
    id_local : str
        Identificador del local (FK).
    id_producto : str
        Identificador del producto (FK).
    activo : bool
        Indica si este producto está activo para este local.
    precio_override : Decimal, optional
        Precio personalizado (NULL = usar precio original).
    disponible_override : bool, optional
        Disponibilidad personalizada (NULL = usar disponibilidad original).
    nombre_override : str, optional
        Nombre personalizado (NULL = usar nombre original).
    descripcion_override : str, optional
        Descripción personalizada (NULL = usar descripción original).
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "locales_productos"

    # Claves foráneas
    id_local: Mapped[str] = mapped_column(
        ForeignKey("locales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del local"
    )
    id_producto: Mapped[str] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Identificador del producto"
    )

    # Campos de configuración
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="Indica si el producto está activo en este local"
    )

    # Campos de override (NULL = usar valor original)
    precio_override: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Precio personalizado para este local (NULL = usar precio original)"
    )
    disponible_override: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        comment="Disponibilidad personalizada (NULL = usar disponibilidad original)"
    )
    nombre_override: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nombre personalizado para este local (NULL = usar nombre original)"
    )
    descripcion_override: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Descripción personalizada para este local (NULL = usar descripción original)"
    )

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('id_local', 'id_producto', name='uq_locales_productos'),
        Index('idx_locales_productos_activo', 'id_local', 'activo'),
        Index('idx_locales_productos_producto', 'id_producto'),
    )

    def get_precio_efectivo(self, precio_original: Decimal) -> Decimal:
        """Obtiene el precio efectivo (override o original).

        Parameters
        ----------
        precio_original : Decimal
            Precio original del producto.

        Returns
        -------
        Decimal
            Precio efectivo a usar (override si existe, sino original).
        """
        return self.precio_override if self.precio_override is not None else precio_original

    def get_disponible_efectivo(self, disponible_original: bool) -> bool:
        """Obtiene la disponibilidad efectiva (override o original).

        Parameters
        ----------
        disponible_original : bool
            Disponibilidad original del producto.

        Returns
        -------
        bool
            Disponibilidad efectiva a usar.
        """
        return self.disponible_override if self.disponible_override is not None else disponible_original

    def get_nombre_efectivo(self, nombre_original: str) -> str:
        """Obtiene el nombre efectivo (override o original).

        Parameters
        ----------
        nombre_original : str
            Nombre original del producto.

        Returns
        -------
        str
            Nombre efectivo a usar.
        """
        return self.nombre_override if self.nombre_override is not None else nombre_original

    def get_descripcion_efectiva(self, descripcion_original: Optional[str]) -> Optional[str]:
        """Obtiene la descripción efectiva (override o original).

        Parameters
        ----------
        descripcion_original : str, optional
            Descripción original del producto.

        Returns
        -------
        str, optional
            Descripción efectiva a usar.
        """
        return self.descripcion_override if self.descripcion_override is not None else descripcion_original

    def __repr__(self) -> str:
        """Representación string del modelo para debugging."""
        return (
            f"<LocalesProductosModel(id={self.id}, "
            f"id_local={self.id_local}, "
            f"id_producto={self.id_producto}, "
            f"activo={self.activo}, "
            f"precio_override={self.precio_override})>"
        )
