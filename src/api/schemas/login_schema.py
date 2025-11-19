"""
Schemas para el sistema de login simplificado (temporal).
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """Schema para solicitud de login simplificado."""

    email: str = Field(
        description="Email o correo del usuario",
        min_length=1,
        max_length=255
    )
    nombre: str = Field(
        description="Nombre del usuario",
        min_length=1,
        max_length=255
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validar que el email contenga 'correo', 'mail' o '@'."""
        email_lower = v.lower()
        if not ('correo' in email_lower or 'mail' in email_lower or '@' in email_lower):
            raise ValueError(
                "El email debe contener 'correo', 'mail' o '@' en su formato"
            )
        return v


class LoginResponse(BaseModel):
    """Schema para respuesta de login simplificado."""

    status: int = Field(default=200, description="Código de estado HTTP")
    code: str = Field(default="SUCCESS", description="Código de respuesta")
    id_usuario: str = Field(description="ID del usuario")
    id_sesion_mesa: str = Field(description="ID de la sesión de mesa temporal")
    token_sesion: str = Field(description="Token único de la sesión")
    message: str = Field(
        default="Login exitoso",
        description="Mensaje descriptivo"
    )
    fecha_expiracion: Optional[datetime] = Field(
        default=None,
        description="Fecha de expiración de la sesión"
    )
