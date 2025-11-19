"""
Local/Restaurant-related enumerations.
"""

from enum import Enum


class TipoLocal(str, Enum):
    """Local/Restaurant type enum."""
    CENTRAL = "CENTRAL"
    SUCURSAL = "SUCURSAL"

    def __str__(self) -> str:
        """Return the enum value as string."""
        return self.value
