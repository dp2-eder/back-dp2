"""
Schemas para el sistema de login simplificado (temporal).

Este módulo define los schemas de entrada y salida para el endpoint de login
de usuarios temporales del restaurante.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LoginRequest(BaseModel):
    """
    Schema para solicitud de login simplificado.
    
    Representa los datos necesarios para que un usuario temporal
    inicie sesión en una mesa del restaurante.
    
    Attributes
    ----------
    email : str
        Email o identificador del usuario. Debe contener 'correo', 'mail' o '@'.
    nombre : str
        Nombre visible del usuario para identificación en pedidos.
    
    Examples
    --------
    >>> request = LoginRequest(email="juan@correo.com", nombre="Juan Pérez")
    >>> request = LoginRequest(email="cliente_correo_1", nombre="Cliente 1")
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan@correo.com",
                "nombre": "Juan Pérez"
            }
        }
    )

    email: str = Field(
        description="Email o correo del usuario. Debe contener 'correo', 'mail' o '@' para ser válido.",
        min_length=1,
        max_length=255,
        examples=["juan@correo.com", "cliente_correo_1", "usuario@mail.com"]
    )
    nombre: str = Field(
        description="Nombre del usuario que se mostrará en pedidos y sesiones.",
        min_length=1,
        max_length=255,
        examples=["Juan Pérez", "María García"]
    )

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """
        Validar que el email contenga 'correo', 'mail' o '@'.
        
        Parameters
        ----------
        v : str
            Valor del email a validar.
            
        Returns
        -------
        str
            Email validado.
            
        Raises
        ------
        ValueError
            Si el email no contiene ninguno de los patrones válidos.
        """
        email_lower = v.lower()
        if not ('correo' in email_lower or 'mail' in email_lower or '@' in email_lower):
            raise ValueError(
                "El email debe contener 'correo', 'mail' o '@' en su formato"
            )
        return v


class LoginResponse(BaseModel):
    """
    Schema para respuesta de login simplificado.
    
    Contiene las credenciales de sesión del usuario después de un login exitoso.
    Múltiples usuarios en la misma mesa compartirán el mismo `token_sesion` e 
    `id_sesion_mesa`, pero tendrán diferentes `id_usuario`.
    
    Attributes
    ----------
    status : int
        Código de estado HTTP (siempre 200 para respuestas exitosas).
    code : str
        Código de respuesta ("SUCCESS" para login exitoso).
    id_usuario : str
        ID único ULID del usuario autenticado.
    id_sesion_mesa : str
        ID único ULID de la sesión de mesa (compartido entre usuarios de la misma mesa).
    token_sesion : str
        Token único de la sesión para autenticación en pedidos (compartido).
    message : str
        Mensaje descriptivo del resultado.
    fecha_expiracion : datetime, optional
        Fecha y hora en que la sesión expirará automáticamente.
    
    Notes
    -----
    - El `token_sesion` se usa para autenticar pedidos y acciones del usuario.
    - La sesión expira después de `duracion_minutos` (por defecto 120 min = 2 horas).
    - Usuarios de la misma mesa comparten `token_sesion` e `id_sesion_mesa`.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "code": "SUCCESS",
                "id_usuario": "01HABC123456789DEFGHIJK",
                "id_sesion_mesa": "01HDEF123456789GHIJKLM",
                "token_sesion": "01HGHI123456789JKLMNOP",
                "message": "Login exitoso",
                "fecha_expiracion": "2025-11-26T16:30:00"
            }
        }
    )

    status: int = Field(
        default=200, 
        description="Código de estado HTTP de la respuesta"
    )
    code: str = Field(
        default="SUCCESS", 
        description="Código de respuesta. 'SUCCESS' indica login exitoso"
    )
    id_usuario: str = Field(
        description="ID único ULID del usuario autenticado"
    )
    id_sesion_mesa: str = Field(
        description="ID único ULID de la sesión de mesa. Compartido entre usuarios de la misma mesa"
    )
    token_sesion: str = Field(
        description="Token único de la sesión para autenticación en pedidos. Compartido entre usuarios de la misma mesa"
    )
    message: str = Field(
        default="Login exitoso",
        description="Mensaje descriptivo del resultado del login"
    )
    fecha_expiracion: Optional[datetime] = Field(
        default=None,
        description="Fecha y hora en que la sesión expirará automáticamente (por defecto 2 horas desde el inicio)"
    )


class LoginErrorResponse(BaseModel):
    """
    Schema para respuestas de error del login.
    
    Se usa para errores 404 (mesa no encontrada/inactiva).
    
    Attributes
    ----------
    message : str
        Mensaje descriptivo del error.
    code : str
        Código de error para identificación programática.
        - MESA_NOT_FOUND: La mesa no existe en la base de datos.
        - MESA_INACTIVE: La mesa existe pero está desactivada.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "No se encontró la mesa con ID '01HXXX...'",
                    "code": "MESA_NOT_FOUND"
                },
                {
                    "message": "La mesa '5' no está activa",
                    "code": "MESA_INACTIVE"
                }
            ]
        }
    )
    
    message: str = Field(
        description="Mensaje descriptivo del error"
    )
    code: str = Field(
        description="Código de error: MESA_NOT_FOUND o MESA_INACTIVE"
    )
