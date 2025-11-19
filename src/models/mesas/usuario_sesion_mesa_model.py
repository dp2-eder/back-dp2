"""
Modelo de asociación entre usuarios y sesiones de mesa.

Implementa la tabla intermedia para la relación many-to-many entre
usuarios y sesiones de mesa, permitiendo que múltiples usuarios compartan
una misma sesión de mesa y su token.
"""

from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, TIMESTAMP, ForeignKey, Index, UniqueConstraint
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

if TYPE_CHECKING:
    from src.models.auth.usuario_model import UsuarioModel
    from src.models.mesas.sesion_mesa_model import SesionMesaModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="UsuarioSesionMesaModel")


class UsuarioSesionMesaModel(BaseModel, AuditMixin):
    """Modelo para representar la asociación entre usuarios y sesiones de mesa.

    Esta tabla intermedia permite que múltiples usuarios puedan unirse a una
    misma sesión de mesa, compartiendo el token de sesión y permitiendo
    colaboración en los pedidos.

    Attributes
    ----------
    id : str
        Identificador único ULID de la asociación (heredado de BaseModel).
    id_usuario : str
        Identificador ULID del usuario asociado.
    id_sesion_mesa : str
        Identificador ULID de la sesión de mesa asociada.
    fecha_ingreso : datetime
        Fecha y hora en que el usuario se unió a la sesión.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "usuarios_sesiones_mesas"

    # Foreign Keys
    id_usuario: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        comment="Usuario asociado a la sesión"
    )

    id_sesion_mesa: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sesiones_mesas.id", ondelete="CASCADE"),
        nullable=False,
        comment="Sesión de mesa asociada"
    )

    # Campos específicos
    fecha_ingreso: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.now,
        comment="Fecha y hora en que el usuario se unió a la sesión"
    )

    # Relaciones
    usuario: Mapped["UsuarioModel"] = relationship(
        "UsuarioModel",
        lazy="selectin"
    )

    sesion_mesa: Mapped["SesionMesaModel"] = relationship(
        "SesionMesaModel",
        back_populates="usuarios_sesiones",
        lazy="selectin"
    )

    # Constraints e índices
    __table_args__ = (
        UniqueConstraint(
            "id_usuario",
            "id_sesion_mesa",
            name="uq_usuario_sesion_mesa"
        ),
        Index("idx_usuario_sesion_mesa_usuario", "id_usuario"),
        Index("idx_usuario_sesion_mesa_sesion", "id_sesion_mesa"),
    )

    # Métodos comunes para todos los modelos
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia del modelo a un diccionario.

        Returns
        -------
        Dict[str, Any]
            Diccionario con los nombres de columnas como claves y sus valores correspondientes.
        """
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
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
        from sqlalchemy import inspect
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
        return f"<UsuarioSesionMesa(id={self.id}, usuario={self.id_usuario}, sesion={self.id_sesion_mesa})>"
