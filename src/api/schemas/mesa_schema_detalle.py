"""
Schema extendido para respuestas detalladas de mesas con zona y local.
"""

from typing import Optional
from pydantic import Field

from src.api.schemas.mesa_schema import MesaResponse


class MesaDetalleResponse(MesaResponse):
    """
    Schema para respuesta detallada de mesa con zona y local anidados.

    Incluye toda la información de la mesa más los datos de zona y local relacionados.
    """
    zona: Optional[dict] = Field(default=None, description="Información completa de la zona")
    local: Optional[dict] = Field(default=None, description="Información completa del local")
