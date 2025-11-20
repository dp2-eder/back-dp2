"""
Modelo de sesiones de mesa del restaurante.

Implementa la estructura de datos para las sesiones temporales que asocian
usuarios con mesas, permitiendo trackear los pedidos realizados durante la visita.
"""

from typing import Any, Dict, Type, TypeVar, List, TYPE_CHECKING, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, TIMESTAMP, Enum as SQLEnum, ForeignKey, CheckConstraint, Index, inspect, Integer
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa

if TYPE_CHECKING:
    from src.models.auth.usuario_model import UsuarioModel
    from src.models.mesas.mesa_model import MesaModel
    from src.models.pedidos.pedido_model import PedidoModel
    from src.models.mesas.usuario_sesion_mesa_model import UsuarioSesionMesaModel

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="SesionMesaModel")


class SesionMesaModel(BaseModel, AuditMixin):
    """Modelo para representar sesiones de mesa en el sistema.

    Una sesión de mesa es una asociación temporal entre una mesa y múltiples usuarios
    que se crea cuando el primer usuario se loguea/registra. Permite agrupar todos
    los pedidos que los usuarios realizan durante su visita a esa mesa.
    Varios usuarios pueden compartir la misma sesión y token.

    Attributes
    ----------
    id : str
        Identificador único ULID de la sesión (heredado de BaseModel).
    id_mesa : str
        Identificador ULID de la mesa donde se realiza la sesión.
    id_usuario_creador : str
        Identificador ULID del usuario que creó la sesión.
    token_sesion : str
        Token único generado para identificar la sesión (compartido por todos los usuarios).
    estado : EstadoSesionMesa
        Estado actual de la sesión (activa, finalizada).
    fecha_inicio : datetime
        Fecha y hora de inicio de la sesión.
    fecha_fin : datetime, optional
        Fecha y hora de finalización de la sesión.
    duracion_minutos : int
        Duración de la sesión en minutos (por defecto 120 minutos = 2 horas).
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditMixin).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditMixin).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditMixin).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditMixin).
    """

    __tablename__ = "sesiones_mesas"

    # Foreign Keys
    id_mesa: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mesas.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Mesa donde se realiza la sesión"
    )

    id_usuario_creador: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Usuario que creó la sesión de mesa"
    )

    # Campos específicos del modelo de sesión mesa
    token_sesion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Token único para identificar la sesión"
    )

    estado: Mapped[EstadoSesionMesa] = mapped_column(
        SQLEnum(EstadoSesionMesa),
        nullable=False,
        default=EstadoSesionMesa.ACTIVA,
        index=True
    )

    fecha_inicio: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        default=datetime.now,
        comment="Fecha y hora de inicio de la sesión"
    )

    fecha_fin: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="Fecha y hora de finalización de la sesión"
    )

    duracion_minutos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=120,
        comment="Duración de la sesión en minutos (por defecto 120 minutos = 2 horas)"
    )

    # Relaciones
    mesa: Mapped["MesaModel"] = relationship(
        "MesaModel",
        lazy="selectin"
    )

    usuario_creador: Mapped["UsuarioModel"] = relationship(
        "UsuarioModel",
        foreign_keys=[id_usuario_creador],
        lazy="selectin"
    )

    # Relación many-to-many con usuarios a través de la tabla intermedia
    usuarios_sesiones: Mapped[List["UsuarioSesionMesaModel"]] = relationship(
        "UsuarioSesionMesaModel",
        back_populates="sesion_mesa",
        cascade="all, delete-orphan",
        lazy="select"
    )

    # Relación con pedidos (sin cascade delete para preservar historial)
    pedidos: Mapped[List["PedidoModel"]] = relationship(
        "PedidoModel",
        back_populates="sesion_mesa",
        cascade="",  # Sin cascade: los pedidos son registros históricos
        lazy="select"
    )

    # Constraints e índices
    __table_args__ = (
        CheckConstraint(
            "fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
            name="chk_sesion_mesa_fecha_fin_valida"
        ),
        Index("idx_sesion_mesa_mesa", "id_mesa"),
    )

    # Métodos de utilidad
    def calcular_fecha_expiracion(self) -> datetime:
        """
        Calcula la fecha de expiración de la sesión basándose en fecha_inicio y duracion_minutos.

        Returns
        -------
        datetime
            Fecha y hora de expiración de la sesión.
        """
        # Si no hay duración configurada, usar 120 minutos por defecto
        duracion = self.duracion_minutos if self.duracion_minutos is not None else 120
        return self.fecha_inicio + timedelta(minutes=duracion)

    def esta_expirada(self) -> bool:
        """
        Verifica si la sesión ha expirado.

        Returns
        -------
        bool
            True si la sesión ha expirado, False en caso contrario.
        """
        if self.estado == EstadoSesionMesa.FINALIZADA:
            return True

        # Si no hay fecha de inicio, no puede estar expirada
        if not self.fecha_inicio:
            return False

        return datetime.now() > self.calcular_fecha_expiracion()

    def es_valida(self) -> bool:
        """
        Verifica si la sesión es válida (activa y no expirada).

        Returns
        -------
        bool
            True si la sesión es válida, False en caso contrario.
        """
        return self.estado == EstadoSesionMesa.ACTIVA and not self.esta_expirada()

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
            # Convertir Enum a string
            if isinstance(value, EstadoSesionMesa):
                value = value.value
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

    def __repr__(self):
        return f"<SesionMesa(id={self.id}, token={self.token_sesion}, mesa={self.id_mesa}, estado={self.estado.value})>"
