"""
Base business exceptions.
"""


class BusinessError(Exception):
    """Base exception for business logic errors."""

    def __init__(self, message: str, error_code: str | None = None):
        """
        Initialize business error.

        Args:
            message: Error message
            error_code: Optional error code
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(BusinessError):
    """Exception raised for validation errors."""
    pass


class NotFoundError(BusinessError):
    """Exception raised when a resource is not found."""
    pass


class ConflictError(BusinessError):
    """Exception raised for conflict errors."""
    pass


class UnauthorizedError(BusinessError):
    """Exception raised for unauthorized access."""
    pass


class ForbiddenError(BusinessError):
    """Exception raised for forbidden access."""
    pass


class ExternalServiceError(BusinessError):
    """Exception raised for external service errors."""
    pass