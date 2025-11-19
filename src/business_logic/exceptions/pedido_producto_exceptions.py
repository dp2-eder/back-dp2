"""
Excepciones específicas para la gestión de items de pedidos (pedido_producto).
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError, NotFoundError, ConflictError
)


class PedidoProductoValidationError(ValidationError):
    """Excepción lanzada cuando la validación de un item de pedido falla."""

    def __init__(self, message: str, error_code: str = "PEDIDO_PRODUCTO_VALIDATION_ERROR"):
        """
        Inicializa la excepción de validación de item de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de validación.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoProductoNotFoundError(NotFoundError):
    """Excepción lanzada cuando no se encuentra un item de pedido."""

    def __init__(self, message: str = "Item de pedido no encontrado", error_code: str = "PEDIDO_PRODUCTO_NOT_FOUND"):
        """
        Inicializa la excepción de item de pedido no encontrado.

        Parameters
        ----------
        message : str, optional
            Mensaje descriptivo del error.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)


class PedidoProductoConflictError(ConflictError):
    """Excepción lanzada cuando hay un conflicto con un item de pedido."""

    def __init__(self, message: str, error_code: str = "PEDIDO_PRODUCTO_CONFLICT"):
        """
        Inicializa la excepción de conflicto de item de pedido.

        Parameters
        ----------
        message : str
            Mensaje descriptivo del error de conflicto.
        error_code : str, optional
            Código de error para identificar el tipo específico de error.
        """
        super().__init__(message, error_code)
