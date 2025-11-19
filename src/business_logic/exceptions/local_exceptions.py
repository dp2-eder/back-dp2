"""
Excepciones específicas para la gestión de locales.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class LocalValidationError(ValidationError):
    """Excepción lanzada cuando la validación de un local falla."""

    def __init__(self, message: str, error_code: str = "LOCAL_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de local.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class LocalNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra un local."""

    def __init__(self, message: str = "Local no encontrado", error_code: str = "LOCAL_NOT_FOUND"):
        """
        Inicializa la excepción de local no encontrado.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class LocalConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con un local (por ejemplo, código duplicado)."""

    def __init__(self, message: str, error_code: str = "LOCAL_CONFLICT"):
        """
        Inicializa la excepción de conflicto de local.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
