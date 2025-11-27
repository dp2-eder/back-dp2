"""
Excepciones específicas para la gestión de administradores.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class AdminValidationError(ValidationError):
    """Excepción lanzada cuando la validación de un administrador falla."""

    def __init__(self, message: str, error_code: str = "ADMIN_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de administrador.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class AdminNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra un administrador."""

    def __init__(self, message: str = "Administrador no encontrado", error_code: str = "ADMIN_NOT_FOUND"):
        """
        Inicializa la excepción de administrador no encontrado.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class AdminConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con un administrador (por ejemplo, email duplicado)."""

    def __init__(self, message: str, error_code: str = "ADMIN_CONFLICT"):
        """
        Inicializa la excepción de conflicto de administrador.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
