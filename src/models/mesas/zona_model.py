"""
Modelo de zonas para organización de mesas por local.

Implementa la estructura de datos para las zonas jerárquicas que organizan
las mesas dentro de cada local, adaptado para coincidir con el esquema
existente de MySQL restaurant_db.zona.
"""

from typing import Any, Dict, Optional, Type, TypeVar, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, ForeignKey, Index, inspect
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from src.models.mesas.local_model import LocalModel
    from src.models.mesas.mesa_model import MesaModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="ZonaModel")


class ZonaModel(BaseModel, AuditMixin):
    """Modelo para representar zonas en el sistema.

    Define las zonas jerárquicas que organizan las mesas dentro de cada local,
    permitiendo una estructura de hasta 3 niveles (principal, sub-zona, sub-sub-zona).

    Attributes
    ----------
    id_local : str
        ID del local al que pertenece la zona (Foreign Key).
    nombre : str
        Nombre de la zona (ej: Terraza, Interior, Primer Piso, VIP).
    descripcion : str, optional
        Descripción detallada de la zona.
    nivel : int, optional
        Nivel jerárquico de la zona (0=principal, 1=sub-zona, 2=sub-sub-zona).
    capacidad_maxima : int, optional
        Capacidad máxima de personas en la zona.
    activo : bool
        Indica si la zona está activa en el sistema.
    local : LocalModel
        Relación con el modelo de local.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "zonas"

    # Foreign Key hacia Local
    id_local: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("locales.id", ondelete="CASCADE"),
        nullable=False
    )

    # Columnas específicas del modelo de zona
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capacidad_maxima: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relaciones
    local: Mapped["LocalModel"] = relationship(
        "LocalModel",
        back_populates="zonas",
        lazy="joined"  # Eager loading para obtener datos del local
    )

    mesas: Mapped[list["MesaModel"]] = relationship(
        "MesaModel",
        back_populates="zona",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    # Definición de índices
    __table_args__ = (
        Index("idx_zona_local", "id_local"),
        Index("idx_zona_activo", "activo"),
        Index("idx_zona_nivel", "nivel"),
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
            if hasattr(self, key):
                setattr(self, key, value)
