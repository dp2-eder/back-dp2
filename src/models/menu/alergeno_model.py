"""
Modelo de alérgenos para el catálogo de alérgenos alimentarios.

Implementa la estructura de datos para los alérgenos presentes en los productos
del menú, adaptado para coincidir con el esquema existente de MySQL restaurant_dp2.alergeno.
"""

from typing import Optional, TYPE_CHECKING, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, Enum
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin
from src.core.enums.alergeno_enums import NivelRiesgo

if TYPE_CHECKING:
    from src.models.menu.producto_model import ProductoModel
    from src.models.menu.producto_alergeno_model import ProductoAlergenoModel


class AlergenoModel(BaseModel, AuditMixin):
    """Modelo para representar alérgenos alimentarios en el sistema.

    Define los alérgenos que pueden estar presentes en los productos del menú
    para proporcionar información importante a los clientes sobre ingredientes
    que pueden causar reacciones alérgicas.

    Attributes
    ----------
    id : str
        Identificador único del alérgeno (clave primaria, heredado de BaseModel).
    nombre : str
        Nombre del alérgeno (ej: Gluten, Lactosa, Mariscos), debe ser único.
    descripcion : str, optional
        Descripción detallada del alérgeno y sus características.
    icono : str, optional
        Nombre del icono o emoji para representar el alérgeno en la UI.
    nivel_riesgo : NivelRiesgo
        Nivel de riesgo del alérgeno (bajo, medio, alto, crítico).
    activo : bool
        Indica si el alérgeno está activo en el sistema.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "alergenos"

    # Columnas específicas del modelo de alérgeno
    nombre: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        unique=True,
        comment="Gluten, Lactosa, Mariscos, etc"
    )
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icono: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment="Nombre del icono o emoji para UI"
    )
    nivel_riesgo: Mapped[NivelRiesgo] = mapped_column(
        Enum(NivelRiesgo),
        nullable=False, 
        default=NivelRiesgo.MEDIO
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
    )

    # Relación con la tabla intermedia
    productos_alergenos: Mapped[List["ProductoAlergenoModel"]] = relationship(
        "ProductoAlergenoModel",
        back_populates="alergeno",
        cascade="all, delete-orphan"
    )

    # Relación directa many-to-many con Productos
    productos: Mapped[List["ProductoModel"]] = relationship(
        "ProductoModel",
        secondary="productos_alergenos",
        back_populates="alergenos",
        viewonly=True
    )

    def __repr__(self) -> str:
        """Representación string del modelo para debugging.

        Returns
        -------
        str
            Representación string del objeto AlergenoModel.
        """
        return (
            f"<AlergenoModel(id={self.id}, "
            f"nombre='{self.nombre}', nivel_riesgo='{self.nivel_riesgo.value if self.nivel_riesgo else None}', "
            f"activo={self.activo})>"
        )
