"""
Schemas para las operaciones administrativas de sesiones de mesa.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SesionDetalleSchema(BaseModel):
    """Schema para detalles de una sesión."""
    id_sesion: str = Field(..., description="ID de la sesión")
    token_sesion: str = Field(..., description="Token de la sesión")
    fecha_inicio: str = Field(..., description="Fecha de inicio de la sesión")


class SesionFinalizadaDetalleSchema(SesionDetalleSchema):
    """Schema para detalles de una sesión finalizada."""
    id_mesa: Optional[str] = Field(None, description="ID de la mesa")
    fecha_expiracion: Optional[str] = Field(None, description="Fecha de expiración")


class MesaProcesamientoDetalleSchema(BaseModel):
    """Schema para detalles del procesamiento de una mesa."""
    id_mesa: str = Field(..., description="ID de la mesa procesada")
    sesiones_encontradas: int = Field(..., description="Número de sesiones encontradas")
    sesion_mantenida: SesionDetalleSchema = Field(..., description="Sesión que se mantuvo activa")
    sesiones_finalizadas: List[SesionDetalleSchema] = Field(..., description="Sesiones que fueron finalizadas")


class MesaDuplicadosSchema(BaseModel):
    """Schema para información de mesas con duplicados."""
    id_mesa: str = Field(..., description="ID de la mesa")
    sesiones_activas: int = Field(..., description="Número de sesiones activas")


class SesionPorMesaSchema(BaseModel):
    """Schema para información de sesiones por mesa."""
    id_mesa: str = Field(..., description="ID de la mesa")
    sesiones_activas: int = Field(..., description="Número de sesiones activas")
    tiene_duplicados: bool = Field(..., description="Indica si tiene sesiones duplicadas")


class EstadoSesionesResponse(BaseModel):
    """Schema para la respuesta del estado de sesiones."""
    status: int = Field(200, description="Código de estado HTTP")
    total_sesiones_activas: int = Field(..., description="Total de sesiones activas en el sistema")
    total_mesas: int = Field(..., description="Total de mesas con sesiones activas")
    mesas_con_duplicados: int = Field(..., description="Número de mesas con sesiones duplicadas")
    detalles_duplicados: List[MesaDuplicadosSchema] = Field(..., description="Detalles de mesas con duplicados")
    sesiones_por_mesa: List[SesionPorMesaSchema] = Field(..., description="Lista de sesiones por mesa")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "total_sesiones_activas": 5,
                "total_mesas": 3,
                "mesas_con_duplicados": 1,
                "detalles_duplicados": [
                    {
                        "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                        "sesiones_activas": 3
                    }
                ],
                "sesiones_por_mesa": [
                    {
                        "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                        "sesiones_activas": 3,
                        "tiene_duplicados": True
                    }
                ]
            }
        }
    )


class FixDuplicatesResponse(BaseModel):
    """Schema para la respuesta de corrección de duplicados."""
    status: int = Field(200, description="Código de estado HTTP")
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    mesas_procesadas: int = Field(..., description="Número de mesas procesadas")
    sesiones_finalizadas: int = Field(..., description="Número de sesiones finalizadas")
    sesiones_mantenidas: int = Field(..., description="Número de sesiones mantenidas")
    detalles: List[MesaProcesamientoDetalleSchema] = Field(..., description="Detalles del procesamiento")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "success": True,
                "message": "Se corrigieron 1 mesas con sesiones duplicadas",
                "mesas_procesadas": 1,
                "sesiones_finalizadas": 2,
                "sesiones_mantenidas": 1,
                "detalles": [
                    {
                        "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                        "sesiones_encontradas": 3,
                        "sesion_mantenida": {
                            "id_sesion": "01HYYY...",
                            "token_sesion": "01HZZZ...",
                            "fecha_inicio": "2025-11-12T10:30:00"
                        },
                        "sesiones_finalizadas": [
                            {
                                "id_sesion": "01HXXX...",
                                "token_sesion": "01HWWW...",
                                "fecha_inicio": "2025-11-12T08:00:00"
                            }
                        ]
                    }
                ]
            }
        }
    )


class FinalizarExpiradasResponse(BaseModel):
    """Schema para la respuesta de finalización de sesiones expiradas."""
    status: int = Field(200, description="Código de estado HTTP")
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    sesiones_finalizadas: int = Field(..., description="Número de sesiones finalizadas")
    detalles: List[SesionFinalizadaDetalleSchema] = Field(..., description="Detalles de las sesiones finalizadas")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "success": True,
                "message": "Se finalizaron 2 sesiones expiradas",
                "sesiones_finalizadas": 2,
                "detalles": [
                    {
                        "id_sesion": "01HXXX...",
                        "id_mesa": "01K9TM...",
                        "token_sesion": "01HWWW...",
                        "fecha_inicio": "2025-11-12T06:00:00",
                        "fecha_expiracion": "2025-11-12T08:00:00"
                    }
                ]
            }
        }
    )
