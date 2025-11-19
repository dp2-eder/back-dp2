"""
Product validation logic.
"""

from typing import Dict, Any, List
from decimal import Decimal

from src.business_logic.exceptions.menu_exceptions import InvalidProductDataError, InvalidPriceError


class ProductoValidator:
    """Validator for product-related operations."""

    @staticmethod
    def validate_product_data(product_data: Dict[str, Any]) -> None:
        """
        Validate product creation/update data.

        Args:
            product_data: Product data to validate

        Raises:
            InvalidProductDataError: If data is invalid
            InvalidPriceError: If price is invalid
        """
        # Required fields for creation
        required_fields = ["nombre", "id_categoria", "precio_base"]

        for field in required_fields:
            if field not in product_data or product_data[field] is None:
                raise InvalidProductDataError(f"Field '{field}' is required")

        # Validate name
        nombre = product_data.get("nombre", "").strip()
        if not nombre or len(nombre) < 2:
            raise InvalidProductDataError("Product name must be at least 2 characters long")

        if len(nombre) > 200:
            raise InvalidProductDataError("Product name cannot exceed 200 characters")

        # Validate price
        precio_base = product_data.get("precio_base")
        ProductoValidator._validate_price(precio_base)

        # Validate description if provided
        descripcion = product_data.get("descripcion")
        if descripcion and len(descripcion) > 1000:
            raise InvalidProductDataError("Product description cannot exceed 1000 characters")

        # Validate image alt text if provided
        imagen_alt_text = product_data.get("imagen_alt_text")
        if imagen_alt_text and len(imagen_alt_text) > 255:
            raise InvalidProductDataError("Image alt text cannot exceed 255 characters")

    @staticmethod
    def validate_product_update(update_data: Dict[str, Any]) -> None:
        """
        Validate product update data.

        Args:
            update_data: Update data to validate

        Raises:
            InvalidProductDataError: If data is invalid
            InvalidPriceError: If price is invalid
        """
        # Validate name if being updated
        if "nombre" in update_data:
            nombre = update_data["nombre"].strip()
            if not nombre or len(nombre) < 2:
                raise InvalidProductDataError("Product name must be at least 2 characters long")

            if len(nombre) > 200:
                raise InvalidProductDataError("Product name cannot exceed 200 characters")

        # Validate price if being updated
        if "precio_base" in update_data:
            ProductoValidator._validate_price(update_data["precio_base"])

        # Validate description if being updated
        if "descripcion" in update_data:
            descripcion = update_data["descripcion"]
            if descripcion and len(descripcion) > 1000:
                raise InvalidProductDataError("Product description cannot exceed 1000 characters")

        # Validate boolean fields
        boolean_fields = ["disponible", "destacado"]
        for field in boolean_fields:
            if field in update_data and not isinstance(update_data[field], bool):
                raise InvalidProductDataError(f"Field '{field}' must be a boolean value")

    @staticmethod
    def _validate_price(price: Any) -> None:
        """
        Validate price value.

        Args:
            price: Price to validate

        Raises:
            InvalidPriceError: If price is invalid
        """
        if price is None:
            raise InvalidPriceError("Price cannot be null")

        try:
            decimal_price = Decimal(str(price))
        except (ValueError, TypeError):
            raise InvalidPriceError("Price must be a valid number")

        if decimal_price < 0:
            raise InvalidPriceError("Price cannot be negative")

        if decimal_price > Decimal("999999.99"):
            raise InvalidPriceError("Price cannot exceed 999999.99")

        # Check decimal places (max 2)
        if int(decimal_price.as_tuple().exponent) < -2:
            raise InvalidPriceError("Price cannot have more than 2 decimal places")

    @staticmethod
    def validate_option_selection(
        available_options: List[Dict[str, Any]],
        selected_options: List[int]
    ) -> None:
        """
        Validate option selection for a product.

        Args:
            available_options: List of available options
            selected_options: List of selected option IDs

        Raises:
            InvalidProductDataError: If selection is invalid
        """
        if not selected_options:
            return  # No options selected is valid

        available_option_ids = [opt["id"] for opt in available_options if opt.get("activo", True)]

        for option_id in selected_options:
            if option_id not in available_option_ids:
                raise InvalidProductDataError(f"Option with ID {option_id} is not available")

        # Check for duplicate selections
        if len(selected_options) != len(set(selected_options)):
            raise InvalidProductDataError("Duplicate option selections are not allowed")

    @staticmethod
    def validate_bulk_price_update(price_updates: List[Dict[str, Any]]) -> None:
        """
        Validate bulk price updates.

        Args:
            price_updates: List of price update data

        Raises:
            InvalidProductDataError: If data is invalid
        """
        if not price_updates:
            raise InvalidProductDataError("Price updates list cannot be empty")

        seen_ids = set()
        for update in price_updates:
            if "id" not in update or "precio_base" not in update:
                raise InvalidProductDataError("Each update must have 'id' and 'precio_base'")

            product_id = update["id"]
            if product_id in seen_ids:
                raise InvalidProductDataError(f"Duplicate product ID in updates: {product_id}")
            seen_ids.add(product_id)

            ProductoValidator._validate_price(update["precio_base"])