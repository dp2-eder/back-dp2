from typing import Any, Dict, Optional, Type, TypeVar
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Index, TIMESTAMP
from datetime import datetime
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

T = TypeVar("T", bound="UsuarioModel")

class UsuarioModel(BaseModel, AuditMixin):
    """
    Modelo simplificado de usuario para clientes temporales del restaurante.
    Solo almacena información básica: ID, nombre, correo y último acceso.
    """

    __tablename__ = "usuarios"
    __table_args__ = (
        Index("idx_email", "email"),
        {'comment': 'Usuarios temporales del restaurante'}
    )

    # Campos específicos del usuario
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Email o correo del usuario"
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre del usuario"
    )
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        default=None,
        comment="Última vez que el usuario accedió al sistema"
    )

    @staticmethod
    def validar_formato_email(email: str) -> bool:
        """
        Valida que el email contenga 'correo' o 'mail' o '@' en su formato.

        Parameters
        ----------
        email : str
            Email a validar

        Returns
        -------
        bool
            True si el email es válido
        """
        email_lower = email.lower()
        return 'correo' in email_lower or 'mail' in email_lower or '@' in email_lower

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        # Puedes agregar campos adicionales si lo necesitas
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return super().from_dict(data)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        super().update_from_dict(data)

    def __repr__(self):
        return f"<Usuario(id={self.id}, email={self.email}, nombre={self.nombre})>"