from decimal import Decimal
import uuid

from src.models.cart import CartItemORM
from src.services.payment_calculator import calculate_cart_total


def _item(quantity, unit_price):
    return CartItemORM(
        id=uuid.uuid4(),
        cart_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        quantity=quantity,
        unit_price=Decimal(unit_price),
    )


def test_calculate_cart_total_sums_quantity_times_unit_price():
    items = [_item(1, "45.00"), _item(2, "12.50")]
    assert calculate_cart_total(items) == Decimal("70.00")


def test_calculate_cart_total_empty_cart_is_zero():
    assert calculate_cart_total([]) == Decimal("0")
