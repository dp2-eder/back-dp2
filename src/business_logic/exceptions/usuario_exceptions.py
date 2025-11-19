"""
Excepciones específicas para la gestión de usuarios.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError, UnauthorizedError
)


class UsuarioValidationError(ValidationError):
    """Excepción lanzada cuando la validación de un usuario falla."""

    def __init__(self, message: str, error_code: str = "USUARIO_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de usuario.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class UsuarioNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra un usuario."""

    def __init__(self, message: str = "Usuario no encontrado", error_code: str = "USUARIO_NOT_FOUND"):
        """
        Inicializa la excepción de usuario no encontrado.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class UsuarioConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con un usuario (por ejemplo, email duplicado)."""

    def __init__(self, message: str, error_code: str = "USUARIO_CONFLICT"):
        """
        Inicializa la excepción de conflicto de usuario.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class InvalidCredentialsError(UnauthorizedError):
    """Excepción lanzada cuando las credenciales de login son inválidas."""

    def __init__(self, message: str = "Credenciales inválidas", error_code: str = "INVALID_CREDENTIALS"):
        """
        Inicializa la excepción de credenciales inválidas.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class InactiveUserError(UnauthorizedError):
    """Excepción lanzada cuando el usuario intenta acceder pero está inactivo."""

    def __init__(self, message: str = "Usuario inactivo", error_code: str = "INACTIVE_USER"):
        """
        Inicializa la excepción de usuario inactivo.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)

