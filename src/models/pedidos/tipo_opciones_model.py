"""
Modelo de tipo de opciones disponibles para productos o configuraciones.

Define las categorías o tipos de opciones (por ejemplo: nivel de ají, acompañamiento,
temperatura) que agrupan las opciones disponibles en el sistema.
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, inspect
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from src.models.pedidos.producto_opcion_model import ProductoOpcionModel

# Definimos un TypeVar para tipado genérico
T = TypeVar("T", bound="TipoOpcionModel")


class TipoOpcionModel(BaseModel, AuditMixin):
    """Modelo para representar los tipos de opciones de productos o configuraciones.

    Attributes
    ----------
    codigo : str
        Código interno o identificador corto del tipo de opción (e.g. 'nivel_aji').
    nombre : str
        Nombre descriptivo del tipo de opción (e.g. 'Nivel de Ají').
    descripcion : str, optional
        Descripción más detallada del propósito o aplicación de este tipo de opción.
    activo : bool
        Indica si el tipo de opción está activo o no.
    orden : int
        Orden de visualización o prioridad para mostrar este tipo.
    fecha_creacion : datetime
        Fecha y hora de creación (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    """

    __tablename__ = "tipos_opciones"

    # Columnas específicas del modelo
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    orden: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Restricciones de selección
    seleccion_minima: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Cantidad mínima de opciones a seleccionar (0 = opcional)"
    )
    seleccion_maxima: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=None,
        comment="Cantidad máxima de opciones (NULL = sin límite)"
    )

    # Relación con ProductoOpcion
    producto_opciones: Mapped[List["ProductoOpcionModel"]] = relationship(
        "ProductoOpcionModel",
        back_populates="tipo_opcion",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Métodos utilitarios
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia del modelo a un diccionario."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Crea una instancia del modelo a partir de un diccionario."""
        return cls(
            **{k: v for k, v in data.items() if k in inspect(cls).columns.keys()}
        )

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza la instancia con datos de un diccionario."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)