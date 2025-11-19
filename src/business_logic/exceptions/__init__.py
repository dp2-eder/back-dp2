"""
Excepciones del módulo de business logic.
"""

from src.business_logic.exceptions.base_exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    BusinessError,
    UnauthorizedError,
    ForbiddenError,
)
from src.business_logic.exceptions.rol_exceptions import (
    RolValidationError,
    RolNotFoundError,
    RolConflictError,
)
from src.business_logic.exceptions.producto_opcion_exceptions import (
    ProductoOpcionValidationError,
    ProductoOpcionNotFoundError,
    ProductoOpcionConflictError,
)
from src.business_logic.exceptions.usuario_exceptions import (
    UsuarioValidationError,
    UsuarioNotFoundError,
    UsuarioConflictError,
    InvalidCredentialsError,
    InactiveUserError,
)

__all__ = [
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "BusinessError",
    "UnauthorizedError",
    "ForbiddenError",
    "RolValidationError",
    "RolNotFoundError",
    "RolConflictError",
    "UsuarioValidationError",
    "UsuarioNotFoundError",
    "UsuarioConflictError",
    "InvalidCredentialsError",
    "InactiveUserError",
    "ProductoOpcionValidationError",
    "ProductoOpcionNotFoundError",
    "ProductoOpcionConflictError",
]
