"""
Modelo de locales/restaurantes para el sistema.

Implementa la estructura de datos para los locales de la cadena de restaurantes,
adaptado para coincidir con el esquema existente de MySQL restaurant_db.local.
"""

from typing import Any, Dict, Optional, Type, TypeVar, List, TYPE_CHECKING
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Integer, Date, Enum as SQLEnum, Index, inspect
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin
from src.core.enums.local_enums import TipoLocal

if TYPE_CHECKING:
    from src.models.mesas.zona_model import ZonaModel
    from src.models.auth.sesion_model import SesionModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="LocalModel")


class LocalModel(BaseModel, AuditMixin):
    """Modelo para representar locales/restaurantes en el sistema.

    Define los locales que forman parte de la cadena de restaurantes,
    incluyendo información de ubicación, contacto y capacidad.

    Attributes
    ----------
    codigo : str
        Código único del local (ej: CEV-001), debe ser único en el sistema.
    nombre : str
        Nombre del local (ej: La Cevichería del Centro).
    direccion : str
        Dirección física del local.
    distrito : str, optional
        Distrito donde se ubica el local.
    ciudad : str, optional
        Ciudad donde se ubica el local.
    telefono : str, optional
        Número de teléfono del local.
    email : str, optional
        Correo electrónico del local.
    tipo_local : TipoLocal
        Tipo de local (CENTRAL o SUCURSAL).
    capacidad_total : int, optional
        Capacidad total de personas del local.
    activo : bool
        Indica si el local está activo en el sistema.
    fecha_apertura : date, optional
        Fecha de apertura del local.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "locales"

    # Columnas específicas del modelo de local
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    distrito: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo_local: Mapped[TipoLocal] = mapped_column(
        SQLEnum(TipoLocal, native_enum=False, length=10),
        nullable=False
    )
    capacidad_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_apertura: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relaciones
    zonas: Mapped[List["ZonaModel"]] = relationship(
        "ZonaModel",
        back_populates="local",
        cascade="all, delete-orphan",
        lazy="select"
    )

    sesiones: Mapped[List["SesionModel"]] = relationship(
        "SesionModel",
        back_populates="local",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Definición de índices
    __table_args__ = (
        Index("idx_local_activo", "activo"),
        Index("idx_local_tipo", "tipo_local"),
        Index("idx_local_codigo", "codigo"),
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
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            # Convertir enums a su valor string
            if isinstance(value, TipoLocal):
                value = value.value
            # Convertir date a string ISO format
            elif isinstance(value, date):
                value = value.isoformat()
            result[c.name] = value
        return result

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
