from decimal import Decimal
from typing import Iterable

from src.models.cart import CartItemORM


def calculate_cart_total(cart_items: Iterable[CartItemORM]) -> Decimal:
    """Calculate the total cost of the given cart items."""
    return sum((item.unit_price * item.quantity for item in cart_items), Decimal("0"))
