from decimal import Decimal
import uuid

import pytest

from src.enums.status import Status
from src.models.cart import CartItemORM, CartORM
from src.models.user_payment_method import UserPaymentMethodORM
from src.services.payment_exceptions import (
    CartNotActiveError,
    CartNotFoundError,
    EmptyCartError,
    IdempotencyKeyConflictError,
    InvalidPaymentAmountError,
    PaymentMethodNotFoundError,
    PaymentProviderError,
)
from src.services.payment_provider import ChargeResult
from src.services.payment_service import PaymentService

from tests.fakes import (
    FakeCartRepository,
    FakePaymentMethodRepository,
    FakePaymentRepository,
    ScriptedPaymentProvider,
)

USER_ID = uuid.uuid4()
CART_ID = uuid.uuid4()


def make_cart(status="active"):
    return CartORM(id=CART_ID, user_id=USER_ID, status=status)


def make_items():
    return [
        CartItemORM(
            id=uuid.uuid4(), cart_id=CART_ID, product_id=uuid.uuid4(),
            quantity=2, unit_price=Decimal("10.00"),
        ),
    ]


def make_payment_method():
    return UserPaymentMethodORM(
        id=uuid.uuid4(), user_id=USER_ID, provider_token="tok_test",
        last_four="4242", is_default=True,
    )


def build_service(cart=None, items=None, method=None, provider=None, payment_repository=None, **kwargs):
    return PaymentService(
        payment_repository=payment_repository or FakePaymentRepository(),
        cart_repository=FakeCartRepository(cart=cart, items=items),
        payment_method_repository=FakePaymentMethodRepository(method=method),
        payment_provider=provider or ScriptedPaymentProvider(
            [ChargeResult(success=True, provider_reference="ref_default")]
        ),
        retry_backoff_seconds=0,
        **kwargs,
    )


def test_raises_when_cart_not_found(app_context):
    service = build_service(cart=None)
    with pytest.raises(CartNotFoundError):
        service.start_payment(CART_ID, "key-1")


def test_raises_when_cart_not_active(app_context):
    cart = make_cart(status="checked_out")
    service = build_service(cart=cart, items=make_items(), method=make_payment_method())
    with pytest.raises(CartNotActiveError):
        service.start_payment(cart.id, "key-1")


def test_raises_when_cart_has_no_items(app_context):
    cart = make_cart()
    service = build_service(cart=cart, items=[], method=make_payment_method())
    with pytest.raises(EmptyCartError):
        service.start_payment(cart.id, "key-1")


def test_raises_when_no_default_payment_method(app_context):
    cart = make_cart()
    service = build_service(cart=cart, items=make_items(), method=None)
    with pytest.raises(PaymentMethodNotFoundError):
        service.start_payment(cart.id, "key-1")


def test_raises_when_cart_total_is_zero(app_context):
    cart = make_cart()
    free_items = [
        CartItemORM(
            id=uuid.uuid4(), cart_id=CART_ID, product_id=uuid.uuid4(),
            quantity=1, unit_price=Decimal("0.00"),
        ),
    ]
    provider = ScriptedPaymentProvider([ChargeResult(success=True, provider_reference="ref_123")])
    service = build_service(cart=cart, items=free_items, method=make_payment_method(), provider=provider)

    with pytest.raises(InvalidPaymentAmountError):
        service.start_payment(cart.id, "key-1")
    assert provider.calls == 0
    assert cart.status == "active"


def test_successful_charge_marks_payment_succeeded_and_cart_checked_out(app_context):
    cart = make_cart()
    provider = ScriptedPaymentProvider([ChargeResult(success=True, provider_reference="ref_123")])
    service = build_service(cart=cart, items=make_items(), method=make_payment_method(), provider=provider)

    payment = service.start_payment(cart.id, "key-1")

    assert payment.status == Status.SUCCEEDED
    assert payment.provider_reference == "ref_123"
    assert payment.amount == Decimal("20.00")
    assert cart.status == "checked_out"
    assert provider.calls == 1


def test_declined_charge_marks_payment_failed_and_keeps_cart_active(app_context):
    cart = make_cart()
    provider = ScriptedPaymentProvider([ChargeResult(success=False, provider_reference="ref_declined")])
    service = build_service(cart=cart, items=make_items(), method=make_payment_method(), provider=provider)

    payment = service.start_payment(cart.id, "key-1")

    assert payment.status == Status.FAILED
    assert cart.status == "active"


def test_cart_is_locked_for_update_while_charging(app_context):
    cart = make_cart()
    cart_repo = FakeCartRepository(cart=cart, items=make_items())
    service = PaymentService(
        payment_repository=FakePaymentRepository(),
        cart_repository=cart_repo,
        payment_method_repository=FakePaymentMethodRepository(method=make_payment_method()),
        payment_provider=ScriptedPaymentProvider([ChargeResult(success=True, provider_reference="ref")]),
    )

    service.start_payment(cart.id, "key-1")

    assert cart_repo.for_update_flags == [True]


def test_replaying_same_idempotency_key_for_same_cart_does_not_charge_again(app_context):
    cart = make_cart()
    payment_repo = FakePaymentRepository()
    provider = ScriptedPaymentProvider([ChargeResult(success=True, provider_reference="ref_1")])
    service = build_service(
        cart=cart, items=make_items(), method=make_payment_method(),
        provider=provider, payment_repository=payment_repo,
    )

    first = service.start_payment(cart.id, "key-shared")
    second = service.start_payment(cart.id, "key-shared")

    assert first is second
    assert provider.calls == 1


def test_reusing_idempotency_key_for_a_different_cart_conflicts(app_context):
    cart = make_cart()
    other_cart_id = uuid.uuid4()
    payment_repo = FakePaymentRepository()
    service = build_service(
        cart=cart, items=make_items(), method=make_payment_method(), payment_repository=payment_repo,
    )

    service.start_payment(cart.id, "key-shared")
    with pytest.raises(IdempotencyKeyConflictError):
        service.start_payment(other_cart_id, "key-shared")


def test_retries_transient_provider_error_and_then_succeeds(app_context):
    cart = make_cart()
    provider = ScriptedPaymentProvider([
        ConnectionError("timeout"),
        ChargeResult(success=True, provider_reference="ref_after_retry"),
    ])
    service = build_service(cart=cart, items=make_items(), method=make_payment_method(), provider=provider)

    payment = service.start_payment(cart.id, "key-1")

    assert payment.status == Status.SUCCEEDED
    assert provider.calls == 2


def test_gives_up_after_max_attempts_and_marks_payment_failed(app_context):
    cart = make_cart()
    payment_repo = FakePaymentRepository()
    provider = ScriptedPaymentProvider([ConnectionError("timeout")])
    service = build_service(
        cart=cart, items=make_items(), method=make_payment_method(),
        provider=provider, payment_repository=payment_repo, max_charge_attempts=3,
    )

    with pytest.raises(PaymentProviderError):
        service.start_payment(cart.id, "key-1")

    assert provider.calls == 3
    assert payment_repo.created[0].status == Status.FAILED
    assert cart.status == "active"
