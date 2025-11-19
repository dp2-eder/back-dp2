"""
Enumeraciones para el sistema de sesiones de mesa.
"""

from enum import Enum


class EstadoSesionMesa(str, Enum):
    """
    Estados posibles de una sesión de mesa.

    Attributes
    ----------
    ACTIVA : str
        La sesión está activa y se pueden crear pedidos.
    INACTIVA : str
        La sesión está inactiva temporalmente.
    CERRADA : str
        La sesión ha sido cerrada definitivamente, no se pueden crear más pedidos.
    FINALIZADA : str
        La sesión ha sido finalizada (sinónimo de CERRADA para compatibilidad).
    """

    ACTIVA = "activa"
    INACTIVA = "inactiva"
    CERRADA = "cerrada"
    FINALIZADA = "finalizada"
