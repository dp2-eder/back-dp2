from typing import Optional, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class AdminBase(BaseModel):
    """Esquema base con los campos comunes de un administrador."""

    usuario: str = Field(
        description="Nombre de usuario único",
        min_length=3,
        max_length=50
    )
    email: EmailStr = Field(
        description="Correo electrónico del administrador"
    )


class AdminCreate(AdminBase):
    """Esquema para la creación de un nuevo administrador."""

    password: str = Field(
        description="Contraseña del administrador",
        min_length=6,
        max_length=50
    )

class AdminResponse(AdminBase):
    """Esquema de respuesta para devolver datos de un administrador (sin password)."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: str = Field(description="Identificador único (ULID)")
    fecha_creacion: Optional[datetime] = Field(
        default=None, description="Fecha de creación del registro"
    )
    fecha_modificacion: Optional[datetime] = Field(
        default=None, description="Fecha de última modificación"
    )
    ultimo_acceso: Optional[datetime] = Field(
        default=None, description="Fecha del último inicio de sesión exitoso"
    )

class AdminLoginRequest(BaseModel):
    """Schema para la solicitud de login de administrador."""
    email: str = Field(
        description="Email del administrador",
        min_length=3
    )
    password: str = Field(
        description="Contraseña",
        min_length=1
    )


class TokenResponse(BaseModel):
    """Schema para la respuesta con el token de acceso."""
    access_token: str = Field(description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    admin_id: str = Field(description="ID del administrador")
    usuario: str = Field(description="Nombre de usuario")
