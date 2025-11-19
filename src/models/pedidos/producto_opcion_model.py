"""
Modelo de opciones de productos.

Implementa la tabla intermedia entre productos y tipos de opciones,
permitiendo definir las opciones específicas disponibles para cada producto
(ej: nivel de ají, temperatura, acompañamientos).
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, DECIMAL, ForeignKey, Index
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from src.models.menu.producto_model import ProductoModel
    from src.models.pedidos.tipo_opciones_model import TipoOpcionModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="ProductoOpcionModel")


class ProductoOpcionModel(BaseModel, AuditMixin):
    """Modelo para representar las opciones específicas de cada producto.

    Define las opciones concretas disponibles para cada producto en el menú,
    relacionando productos con tipos de opciones y especificando valores como
    nivel de ají, temperatura, acompañamientos, etc.

    Attributes
    ----------
    id_producto : str
        Identificador del producto al que pertenece la opción.
    id_tipo_opcion : str
        Identificador del tipo de opción (categoría de la opción).
    nombre : str
        Nombre de la opción específica (ej: "Sin ají", "Ají suave", "Con choclo", "Helada").
    precio_adicional : Decimal, optional
        Precio adicional que se cobra por seleccionar esta opción.
    activo : bool
        Indica si la opción está activa y disponible.
    orden : int, optional
        Orden de visualización de la opción.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "productos_opciones"

    # Foreign Keys - Relaciones con producto y tipo de opción
    id_producto: Mapped[str] = mapped_column(
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    id_tipo_opcion: Mapped[str] = mapped_column(
        ForeignKey("tipos_opciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Columnas específicas del modelo
    nombre: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Sin ají, Ají suave, Con choclo, Helada"
    )
    
    precio_adicional: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=Decimal("0.00"),
        server_default="0.00"
    )
    
    activo: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True, 
        server_default="1"
    )
    
    orden: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        default=0,
        server_default="0"
    )

    # Relaciones
    producto: Mapped["ProductoModel"] = relationship(
        "ProductoModel",
        back_populates="opciones",
        lazy="selectin"
    )
    
    tipo_opcion: Mapped["TipoOpcionModel"] = relationship(
        "TipoOpcionModel",
        back_populates="producto_opciones",
        lazy="selectin"
    )

    # Índices compuestos
    __table_args__ = (
        Index('idx_producto_tipo', 'id_producto', 'id_tipo_opcion'),
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
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    def __repr__(self) -> str:
        """Representación en string del modelo ProductoOpcion."""
        return (
            f"<ProductoOpcionModel(id={self.id}, nombre='{self.nombre}', "
            f"precio_adicional={self.precio_adicional}, activo={self.activo})>"
        )
