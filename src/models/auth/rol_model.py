"""
Modelo de roles para autenticación y autorización de usuarios.

Implementa la estructura de datos para los roles de usuario en el sistema,
adaptado para coincidir con el esquema existente de MySQL restaurant_dp2.rol.
"""

from typing import Any, Dict, Optional, Type, TypeVar
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, inspect
from src.models.base_model import BaseModel
from src.models.mixins.audit_mixin import AuditMixin

# Definimos un TypeVar para el tipado genérico
T = TypeVar("T", bound="RolModel")


class RolModel(BaseModel, AuditMixin):
    """Modelo para representar roles de usuario en el sistema.

    Define los roles que pueden ser asignados a los usuarios para
    controlar permisos y acceso a funcionalidades específicas.

    Attributes
    ----------
    nombre : str
        Nombre del rol, debe ser único en el sistema.
    descripcion : str, optional
        Descripción detallada del propósito y alcance del rol.
    activo : bool
        Indica si el rol está activo en el sistema.
    fecha_creacion : datetime
        Fecha y hora de creación del registro (heredado de AuditableModel).
    fecha_modificacion : datetime
        Fecha y hora de última modificación (heredado de AuditableModel).
    creado_por : str, optional
        Usuario que creó el registro (heredado de AuditableModel).
    modificado_por : str, optional
        Usuario que realizó la última modificación (heredado de AuditableModel).
    """

    __tablename__ = "roles"

    # Columnas específicas del modelo de rol
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
