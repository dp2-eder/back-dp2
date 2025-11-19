"""
Pydantic schemas for Usuario (User) entities and authentication.
"""

from typing import Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class UsuarioBase(BaseModel):
    """Base schema for Usuario."""

    email: Optional[EmailStr] = Field(
        default=None, description="Email del usuario", max_length=255
    )
    nombre: Optional[str] = Field(
        default=None, description="Nombre del usuario", max_length=255
    )
    telefono: Optional[str] = Field(
        default=None, description="Teléfono del usuario", max_length=20
    )
    id_rol: Optional[str] = Field(default=None, description="ID del rol asignado al usuario")


class UsuarioCreate(UsuarioBase):
    """Schema for creating a new usuario."""

    password: str = Field(
        description="Contraseña del usuario", min_length=6, max_length=100
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validar que la contraseña tenga al menos 6 caracteres."""
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    """Schema for updating usuario."""

    email: Optional[EmailStr] = Field(
        default=None, description="Email del usuario", max_length=255
    )
    nombre: Optional[str] = Field(
        default=None, description="Nombre del usuario", max_length=255
    )
    telefono: Optional[str] = Field(
        default=None, description="Teléfono del usuario", max_length=20
    )
    password: Optional[str] = Field(
        default=None, description="Nueva contraseña", min_length=6, max_length=100
    )
    id_rol: Optional[str] = Field(default=None, description="ID del rol")
    activo: Optional[bool] = Field(default=None, description="Estado activo/inactivo")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validar que la contraseña tenga al menos 6 caracteres si se proporciona."""
        if v is not None and len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v


class UsuarioResponse(UsuarioBase):
    """Schema for usuario responses."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Usuario ID")
    activo: bool = Field(description="Indica si el usuario está activo")
    ultimo_acceso: Optional[datetime] = Field(
        default=None, description="Último acceso del usuario"
    )
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha de creación"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Última modificación"
    )


class UsuarioSummary(BaseModel):
    """Schema for summarized usuario information in lists."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Usuario ID")
    email: Optional[str] = Field(description="Email del usuario")
    nombre: Optional[str] = Field(description="Nombre del usuario")
    activo: bool = Field(description="Indica si el usuario está activo")


# Schemas de Autenticación

class LoginRequest(BaseModel):
    """Schema para solicitud de login."""

    email: EmailStr = Field(description="Email del usuario")
    password: str = Field(description="Contraseña del usuario", min_length=1)


class AdminLoginRequest(BaseModel):
    """Schema para solicitud de login de administrador."""

    usuario: str = Field(description="Usuario (email) del administrador", min_length=1)
    password: str = Field(description="Contraseña del administrador", min_length=1)


class LoginResponse(BaseModel):
    """Schema para respuesta de login."""

    status: int = Field(default=200, description="Código de estado HTTP")
    code: str = Field(default="SUCCESS", description="Código de respuesta")
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    usuario: UsuarioResponse = Field(description="Información del usuario autenticado")


class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh token."""

    refresh_token: str = Field(description="Refresh token para renovar acceso")


class RefreshTokenResponse(BaseModel):
    """Schema para respuesta de refresh token."""

    status: int = Field(default=200, description="Código de estado HTTP")
    code: str = Field(default="SUCCESS", description="Código de respuesta")
    access_token: str = Field(description="Nuevo JWT access token")
    token_type: str = Field(default="bearer", description="Tipo de token")


class RegisterRequest(UsuarioCreate):
    """Schema para registro de nuevo usuario."""

    pass


class RegisterResponse(BaseModel):
    """Schema para respuesta de registro."""

    status: int = Field(default=201, description="Código de estado HTTP")
    code: str = Field(default="SUCCESS", description="Código de respuesta")
    usuario: UsuarioResponse = Field(description="Usuario creado")
    message: str = Field(default="Usuario registrado exitosamente")


class TokenData(BaseModel):
    """Schema para datos del token JWT."""

    sub: str = Field(description="Subject (usuario ID)")
    email: Optional[str] = Field(default=None, description="Email del usuario")
    rol_id: Optional[str] = Field(default=None, description="ID del rol del usuario")

