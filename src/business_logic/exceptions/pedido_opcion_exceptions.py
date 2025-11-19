"""
Excepciones específicas para la gestión de opciones de pedidos.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class PedidoOpcionValidationError(ValidationError):
    """Excepción lanzada cuando la validación de una opción de pedido falla."""

    def __init__(self, message: str, error_code: str = "PEDIDO_OPCION_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de opción de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoOpcionNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra una opción de pedido."""

    def __init__(self, message: str = "Opción de pedido no encontrada", error_code: str = "PEDIDO_OPCION_NOT_FOUND"):
        """
        Inicializa la excepción de opción de pedido no encontrada.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoOpcionConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con una opción de pedido."""

    def __init__(self, message: str, error_code: str = "PEDIDO_OPCION_CONFLICT"):
        """
        Inicializa la excepción de conflicto de opción de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
