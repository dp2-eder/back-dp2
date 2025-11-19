"""
Excepciones personalizadas para el módulo de sesiones.

Define las excepciones específicas que pueden ocurrir durante las operaciones
relacionadas con sesiones.
"""


from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)

class SesionValidationError(ValidationError):
    """Excepción lanzada cuando la validación de una sesión falla."""
    def __init__(self, message: str, error_code: str = "SESION_VALIDATION_ERROR"):
        super().__init__(message, error_code)

class SesionNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra una sesión."""
    def __init__(self, message: str = "Sesión no encontrada", error_code: str = "SESION_NOT_FOUND"):
        super().__init__(message, error_code)

class SesionConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con una sesión."""
    def __init__(self, message: str, error_code: str = "SESION_CONFLICT"):
        super().__init__(message, error_code)
