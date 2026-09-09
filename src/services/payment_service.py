import uuid

from src.extensions import db
from src.enums.status import Status
from src.models.payment import PaymentORM
from src.repositories.payment_repository import PaymentRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.user_payment_method_repository import UserPaymentMethodRepository
from src.services.payment_provider import PaymentProvider
from src.services.payment_calculator import calculate_cart_total


class CartNotFoundError(Exception):
    def __init__(self, message="Cart not found"):
        super().__init__(message)


class PaymentMethodNotFoundError(Exception):
    def __init__(self, message="Payment method not found"):
        super().__init__(message)


class IdempotencyKeyConflictError(Exception):
    def __init__(self, message="Idempotency key was already used for a different cart"):
        super().__init__(message)


class PaymentService:
    """Business logic for starting a payment for a cart."""

    def __init__(
        self,
        payment_repository: PaymentRepository | None = None,
        cart_repository: CartRepository | None = None,
        payment_method_repository: UserPaymentMethodRepository | None = None,
        payment_provider: PaymentProvider | None = None,
    ):
        self._payments = payment_repository or PaymentRepository()
        self._carts = cart_repository or CartRepository()
        self._payment_methods = payment_method_repository or UserPaymentMethodRepository()
        self._payment_provider = payment_provider or PaymentProvider()

    def start_payment(self, cart_id: uuid.UUID, idempotency_key: str) -> PaymentORM:
        existing_payment = self._payments.get_by_idempotency_key(idempotency_key)
        if existing_payment is not None:
            if existing_payment.cart_id != cart_id:
                raise IdempotencyKeyConflictError(
                    f"Idempotency key {idempotency_key} was already used for a different cart"
                )
            # Same key + same cart: return the original result instead of charging again.
            return existing_payment

        cart = self._carts.get_by_id(cart_id)
        if cart is None:
            raise CartNotFoundError(f"Cart {cart_id} not found")

        payment_method = self._payment_methods.get_default_for_user(cart.user_id)
        if payment_method is None:
            raise PaymentMethodNotFoundError(f"No default payment method for user {cart.user_id}")

        cart_items = self._carts.get_items(cart_id)
        amount = calculate_cart_total(cart_items)

        payment = self._payments.create(
            PaymentORM(
                cart_id=cart.id,
                user_id=cart.user_id,
                amount=amount,
                status=Status.PENDING,
                provider_token=payment_method.provider_token,
                idempotency_key=idempotency_key,
            )
        )
        db.session.flush()

        result = self._payment_provider.charge(payment_method.provider_token, amount)
        payment.status = Status.SUCCEEDED if result.success else Status.FAILED
        payment.provider_reference = result.provider_reference
        if result.success:
            self._carts.mark_checked_out(cart)

        db.session.commit()
        return payment
