"""
Excepciones específicas para la gestión de zonas.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class ZonaValidationError(ValidationError):
    """Excepción lanzada cuando la validación de una zona falla."""

    def __init__(self, message: str, error_code: str = "ZONA_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de zona.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class ZonaNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra una zona."""

    def __init__(self, message: str = "Zona no encontrada", error_code: str = "ZONA_NOT_FOUND"):
        """
        Inicializa la excepción de zona no encontrada.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class ZonaConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con una zona."""

    def __init__(self, message: str, error_code: str = "ZONA_CONFLICT"):
        """
        Inicializa la excepción de conflicto de zona.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
