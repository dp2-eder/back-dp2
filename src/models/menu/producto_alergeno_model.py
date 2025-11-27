"""
Modelo de relación entre productos y alérgenos.

Implementa la tabla de asociación muchos-a-muchos entre productos y alérgenos,
con campos adicionales para detallar el nivel de presencia del alérgeno en cada producto.
Adaptado para coincidir con el esquema de MySQL restaurant_dp2.producto_alergeno.
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Enum, ForeignKey, Index, UniqueConstraint, inspect
from datetime import datetime
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin
from src.core.enums.alergeno_enums import NivelPresencia

if TYPE_CHECKING:
    from src.models.menu.producto_model import ProductoModel
    from src.models.menu.alergeno_model import AlergenoModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="ProductoAlergenoModel")


class ProductoAlergenoModel(BaseModel, AuditMixin):
    """Modelo para representar la relación entre productos y alérgenos.

    Tabla de asociación muchos-a-muchos que detalla qué alérgenos están presentes
    en cada producto del menú, con información adicional sobre el nivel de presencia
    (contiene, trazas, puede contener).

    Esta tabla ahora usa clave primaria simple (id) heredada de BaseModel,
    con UniqueConstraint en (id_producto, id_alergeno) para evitar duplicados.

    Attributes
    ----------
    id : str
        Identificador único ULID (heredado de BaseModel).
    id_producto : str
        Identificador del producto (FK).
    id_alergeno : str
        Identificador del alérgeno (FK).
    nivel_presencia : NivelPresencia
        Nivel de presencia del alérgeno: contiene, trazas, puede_contener.
    notas : str, optional
        Información adicional sobre el alérgeno en este producto.
    activo : bool
        Indica si esta relación está activa.
    fecha_creacion : datetime
        Fecha y hora de creación del registro.
    fecha_modificacion : datetime
        Fecha y hora de última modificación.
    """

    __tablename__ = "productos_alergenos"

    # Claves foráneas (ya NO son primary keys)
    id_producto: Mapped[str] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    id_alergeno: Mapped[str] = mapped_column(
        ForeignKey("alergenos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Columnas específicas del modelo
    nivel_presencia: Mapped[NivelPresencia] = mapped_column(
        Enum(NivelPresencia),
        nullable=False,
        default=NivelPresencia.CONTIENE,
        server_default="contiene"
    )
    notas: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Información adicional sobre el alérgeno en este producto"
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1"
    )

    # Los campos de auditoría se heredan de AuditMixin

    # Relaciones hacia Producto y Alergeno
    producto: Mapped["ProductoModel"] = relationship(
        "ProductoModel",
        back_populates="productos_alergenos",
        lazy="selectin"
    )
    
    alergeno: Mapped["AlergenoModel"] = relationship(
        "AlergenoModel",
        back_populates="productos_alergenos",
        lazy="selectin"
    )

    # UniqueConstraint para evitar duplicados + Índices para mejorar búsquedas
    __table_args__ = (
        UniqueConstraint('id_producto', 'id_alergeno', name='uq_producto_alergeno'),
        Index('idx_producto', 'id_producto'),
        Index('idx_alergeno', 'id_alergeno'),
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
            if hasattr(self, key) and key not in ('id', 'id_producto', 'id_alergeno'):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Representación string del modelo para debugging.

        Returns
        -------
        str
            Representación string del objeto ProductoAlergenoModel.
        """
        return (
            f"<ProductoAlergenoModel(id={self.id}, "
            f"id_producto={self.id_producto}, "
            f"id_alergeno={self.id_alergeno}, "
            f"nivel_presencia='{self.nivel_presencia.value}', activo={self.activo})>"
        )
