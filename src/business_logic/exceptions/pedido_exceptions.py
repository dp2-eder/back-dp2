"""
Excepciones específicas para la gestión de pedidos.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class PedidoValidationError(ValidationError):
    """Excepción lanzada cuando la validación de un pedido falla."""

    def __init__(self, message: str, error_code: str = "PEDIDO_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra un pedido."""

    def __init__(self, message: str = "Pedido no encontrado", error_code: str = "PEDIDO_NOT_FOUND"):
        """
        Inicializa la excepción de pedido no encontrado.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con un pedido (por ejemplo, numero_pedido duplicado)."""

    def __init__(self, message: str, error_code: str = "PEDIDO_CONFLICT"):
        """
        Inicializa la excepción de conflicto de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoStateTransitionError(ValidationError):
    """Excepción lanzada cuando se intenta una transición de estado inválida."""

    def __init__(self, message: str, error_code: str = "PEDIDO_INVALID_STATE_TRANSITION"):
        """
        Inicializa la excepción de transición de estado inválida.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de transición.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
