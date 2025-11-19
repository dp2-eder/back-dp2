"""
Modelo de categorías para la gestión del menú del restaurante.

Implementa la estructura de datos para las categorías de productos en el sistema,
adaptado para coincidir con el esquema de MySQL restaurant_dp2.categoria.
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Text
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from src.models.menu.producto_model import ProductoModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="CategoriaModel")


class CategoriaModel(BaseModel, AuditMixin):
    """Modelo para representar categorías de productos en el sistema.

    Define las categorías que organizan los productos del menú del restaurante
    para facilitar la navegación y gestión de la carta digital.

    Attributes
    ----------
    nombre : str
        Nombre de la categoría, debe ser único en el sistema.
    descripcion : str, optional
        Descripción detallada de la categoría y sus productos.
    imagen_path : str, optional
        Ruta de la imagen representativa de la categoría.
    activo : bool
        Indica si la categoría está activa en el sistema.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "categorias"

    # Columnas específicas del modelo de categoría
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imagen_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1", index=True
    )

    # Relación con Productos (one-to-many)
    productos: Mapped[List["ProductoModel"]] = relationship(
        "ProductoModel",
        back_populates="categoria",
        lazy="selectin",
        cascade="all, delete-orphan"
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
        # Filtrar solo columnas válidas, ignorar relaciones
        valid_columns = [c.name for c in cls.__table__.columns]
        filtered_data = {
            k: v for k, v in data.items() 
            if k in valid_columns
        }
        return cls(**filtered_data)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Actualiza la instancia con datos de un diccionario.

        Parameters
        ----------
        data : Dict[str, Any]
            Diccionario con los datos para actualizar la instancia.
        """
        for key, value in data.items():
            # Ignorar relaciones, solo actualizar columnas directas
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Representación en string del modelo Categoría."""
        return f"<CategoriaModel(id={self.id}, nombre='{self.nombre}', activo={self.activo})>"
