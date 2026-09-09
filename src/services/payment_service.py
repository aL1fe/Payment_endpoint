import uuid
import time

from src.extensions import db
from src.enums.status import Status
from src.models.payment import PaymentORM
from src.repositories.payment_repository import PaymentRepository
from src.repositories.cart_repository import CartRepository
from src.repositories.user_payment_method_repository import UserPaymentMethodRepository
from src.services.payment_provider import PaymentGateway, PaymentProvider
from src.services.payment_calculator import calculate_cart_total
from src.services.payment_exceptions import (
    CartNotFoundError,
    PaymentMethodNotFoundError,
    IdempotencyKeyConflictError,
    CartNotActiveError,
    PaymentProviderError,
    EmptyCartError,
)


class PaymentService:
    """Business logic for starting a payment for a cart."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        cart_repository: CartRepository,
        payment_method_repository: UserPaymentMethodRepository,
        payment_provider: PaymentGateway,
        max_charge_attempts: int = 3,
        retry_backoff_seconds: float = 0.2,
    ):
        self._payments = payment_repository
        self._carts = cart_repository
        self._payment_methods = payment_method_repository
        self._payment_provider = payment_provider
        self._max_charge_attempts = max_charge_attempts
        self._retry_backoff_seconds = retry_backoff_seconds

    def _charge_with_retry(self, provider_token: str, amount):
        """Retries only on transient errors (exceptions). A declined charge
        (result.success == False) is a definitive answer and is not retried."""
        last_error: Exception | None = None
        for attempt in range(1, self._max_charge_attempts + 1):
            try:
                return self._payment_provider.charge(provider_token, amount)
            except Exception as exc:
                last_error = exc
                if attempt < self._max_charge_attempts:
                    time.sleep(self._retry_backoff_seconds * attempt)
        raise last_error

    def start_payment(self, cart_id: uuid.UUID, idempotency_key: str) -> PaymentORM:
        existing_payment = self._payments.get_by_idempotency_key(idempotency_key)
        if existing_payment is not None:
            if existing_payment.cart_id != cart_id:
                raise IdempotencyKeyConflictError(
                    f"Idempotency key {idempotency_key} was already used for a different cart"
                )
            # Same key + same cart: return the original result instead of charging again.
            return existing_payment

        cart = self._carts.get_by_id(cart_id, for_update=True)
        if cart is None:
            raise CartNotFoundError(f"Cart {cart_id} not found")
        if cart.status != "active":
            raise CartNotActiveError(f"Cart {cart_id} is {cart.status}, not active")

        payment_method = self._payment_methods.get_default_for_user(cart.user_id)
        if payment_method is None:
            raise PaymentMethodNotFoundError(f"No default payment method for user {cart.user_id}")

        cart_items = self._carts.get_items(cart_id)
        if not cart_items:
            raise EmptyCartError(f"Cart {cart_id} has no items")
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

        try:
            result = self._charge_with_retry(payment_method.provider_token, amount)
        except Exception as exc:
            payment.status = Status.FAILED
            db.session.commit()
            raise PaymentProviderError(f"Payment provider call failed: {exc}") from exc

        payment.status = Status.SUCCEEDED if result.success else Status.FAILED
        payment.provider_reference = result.provider_reference
        if result.success:
            self._carts.mark_checked_out(cart)

        db.session.commit()
        return payment


def create_payment_service() -> PaymentService:
    """Composition root: wires PaymentService with its real (non-test) dependencies."""
    return PaymentService(
        payment_repository=PaymentRepository(),
        cart_repository=CartRepository(),
        payment_method_repository=UserPaymentMethodRepository(),
        payment_provider=PaymentProvider(),
    )
