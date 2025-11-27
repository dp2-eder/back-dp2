from typing import Any, Dict, Optional, Type, TypeVar
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Index, TIMESTAMP
from datetime import datetime
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

T = TypeVar("T", bound="AdminModel")

class AdminModel(BaseModel, AuditMixin):
    __tablename__ = "admins"
    __table_args__ = (
        Index("idx_admin_email", "email"),
        Index("idx_admin_usuario", "usuario"),
        {'comment': 'Administradores del sistema con acceso al panel de control'}
    )

    usuario: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Nombre de usuario único para login"
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Correo electrónico de contacto y recuperación"
    )

    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash de la contraseña del administrador"
    )

    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        default=None,
        comment="Última vez que el administrador inició sesión"
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario.
        """
        result = super().to_dict()
        if "password" in result:
            del result["password"]
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return super().from_dict(data)

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        super().update_from_dict(data)

    def __repr__(self):
        return f"<Admin(id={self.id}, usuario={self.usuario}, email={self.email})>"
