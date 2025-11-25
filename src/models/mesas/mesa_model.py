from sqlalchemy import Integer, String, Boolean, inspect, Enum as SQLEnum, ForeignKey
from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base
from src.models.mixins.audit_mixin import AuditMixin
from src.models.base_model import BaseModel
from src.core.enums.mesa_enums import EstadoMesa

if TYPE_CHECKING:
    from src.models.mesas.zona_model import ZonaModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="MesaModel")


class MesaModel(BaseModel, AuditMixin):
    __tablename__ = 'mesas'

    """Modelo para representar mesas en el sistema.

    Define las mesas que pueden ser asignadas a los usuarios para
    controlar permisos y acceso a funcionalidades específicas.

    Attributes
    ----------
    numero : str
        Número de la mesa, debe ser único en el sistema.
    capacidad : int, optional
        Capacidad de la mesa.
    id_zona : str, optional
        ID de la zona donde se encuentra la mesa (Foreign Key).
    qr_code : str, optional
        Código QR asociado a la mesa para identificación rápida.
    activo : bool
        Indica si la mesa está activa en el sistema.
    estado : EstadoMesaEnum
        Estado actual de la mesa (libre, ocupada, reservada, fuera de servicio).
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditableModel).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditableModel).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditableModel).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditableModel).
    """

    # Columnas específicas del modelo Mesa
    numero: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=True)
    id_zona: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("zonas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nota: Mapped[str] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    estado: Mapped[EstadoMesa] = mapped_column(SQLEnum(EstadoMesa), nullable=False, default=EstadoMesa.DISPONIBLE)

    # Relación con Zona
    zona: Mapped[Optional["ZonaModel"]] = relationship(
        "ZonaModel",
        back_populates="mesas",
        lazy="selectin"
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

    def __repr__(self):
        return f"<Mesa(id={self.id}, numero={self.numero}, id_zona={self.id_zona}, capacidad={self.capacidad})>"