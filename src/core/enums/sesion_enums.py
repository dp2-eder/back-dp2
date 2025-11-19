"""
Enumeraciones relacionadas con el modelo Sesion.

Este módulo define los estados posibles de una sesión.
"""

from enum import Enum


class EstadoSesion(str, Enum):
    """
    Enumeración para los estados de una sesión.

    Attributes
    ----------
    ACTIVO : str
        La sesión está activa y en uso.
    INACTIVO : str
        La sesión está inactiva temporalmente.
    CERRADO : str
        La sesión ha sido cerrada definitivamente.
    """

    ACTIVO = "activo"
    INACTIVO = "inactivo"
    CERRADO = "cerrado"
