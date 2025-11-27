"""
Core dependencies and middleware for the application.
Includes database session management and error handling.
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# Error handling middleware
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle application errors and return proper HTTP responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Import here to avoid circular dependencies
            from src.business_logic.exceptions import (
                BusinessError,
                ValidationError,
                NotFoundError,
                ConflictError,
                UnauthorizedError,
                ForbiddenError,
            )

            if isinstance(e, BusinessError):
                return await self._handle_business_error(e, request)
            else:
                return await self._handle_unexpected_error(e, request)

    async def _handle_business_error(self, error, request: Request) -> JSONResponse:
        """
        Handle business logic errors.

        Args:
            error: Business error
            request: HTTP request

        Returns:
            JSON error response
        """
        # Import here to avoid circular dependencies
        from src.business_logic.exceptions import (
            ValidationError,
            NotFoundError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
        )

        if isinstance(error, UnauthorizedError):
            status_code = 401
        elif isinstance(error, ForbiddenError):
            status_code = 403
        elif isinstance(error, NotFoundError):
            status_code = 404
        elif isinstance(error, ConflictError):
            status_code = 409
        elif isinstance(error, ValidationError):
            status_code = 400
        else:
            status_code = 400

        error_response = {
            "error": {
                "type": type(error).__name__,
                "message": error.message,
                "code": getattr(error, "error_code", None),
            },
            "path": str(request.url.path),
            "method": request.method,
        }

        # Log the error
        logging.warning(
            f"Business error: {type(error).__name__} - {error.message}",
            extra={
                "error_type": type(error).__name__,
                "error_message": error.message,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(status_code=status_code, content=error_response)

    async def _handle_unexpected_error(
        self, error: Exception, request: Request
    ) -> JSONResponse:
        """
        Handle unexpected errors.

        Args:
            error: Unexpected error
            request: HTTP request

        Returns:
            JSON error response
        """
        error_response = {
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
            "path": str(request.url.path),
            "method": request.method,
        }

        # Log the error with full details
        logging.error(
            f"Unexpected error: {type(error).__name__} - {str(error)}",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(status_code=500, content=error_response)
