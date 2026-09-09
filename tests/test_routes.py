from datetime import datetime, timezone
from types import SimpleNamespace
from decimal import Decimal
import uuid

import pytest

from src import create_app
from src.enums.status import Status
from src.services.payment_exceptions import (
    CartNotActiveError,
    CartNotFoundError,
    EmptyCartError,
    IdempotencyKeyConflictError,
    InvalidPaymentAmountError,
    PaymentMethodNotFoundError,
    PaymentProviderError,
)


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _stub_start_payment(monkeypatch, side_effect=None, return_value=None):
    """Replaces the payment service used by the route with a stub, so route tests
    don't need a real database."""
    from src.routes import main as main_module

    class StubPaymentService:
        def start_payment(self, cart_id, idempotency_key):
            if side_effect is not None:
                raise side_effect
            return return_value

    monkeypatch.setattr(main_module, "create_payment_service", lambda: StubPaymentService())


def _fake_payment_orm(status=Status.SUCCEEDED):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        cart_id=uuid.uuid4(),
        amount=Decimal("20.00"),
        status=status,
        provider_token="tok_test",
        provider_reference="ref_123",
        idempotency_key="key-1",
        created_at=now,
        updated_at=now,
    )


def test_start_payment_without_idempotency_key_returns_400(client):
    resp = client.post(f"/carts/{uuid.uuid4()}/payments")
    assert resp.status_code == 400


def test_start_payment_success_returns_201(client, monkeypatch):
    _stub_start_payment(monkeypatch, return_value=_fake_payment_orm())
    resp = client.post(f"/carts/{uuid.uuid4()}/payments", headers={"Idempotency-Key": "key-1"})
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "succeeded"


@pytest.mark.parametrize(
    "exception, expected_status",
    [
        (CartNotFoundError("not found"), 404),
        (CartNotActiveError("not active"), 409),
        (PaymentMethodNotFoundError("no method"), 422),
        (EmptyCartError("empty"), 422),
        (InvalidPaymentAmountError("zero total"), 422),
        (IdempotencyKeyConflictError("conflict"), 409),
        (PaymentProviderError("provider down"), 502),
    ],
)
def test_start_payment_maps_service_errors_to_http_status(client, monkeypatch, exception, expected_status):
    _stub_start_payment(monkeypatch, side_effect=exception)
    resp = client.post(f"/carts/{uuid.uuid4()}/payments", headers={"Idempotency-Key": "key-1"})
    assert resp.status_code == expected_status
    body = resp.get_json()
    assert body["error"] == str(exception)
    assert body["status"] == expected_status


class _FakeSession:
    def __init__(self, result):
        self._result = result

    def get(self, model, ident):
        return self._result


class _FakeDb:
    def __init__(self, result):
        self.session = _FakeSession(result)


def test_get_payment_not_found_returns_404(client, monkeypatch):
    from src.routes import main as main_module
    monkeypatch.setattr(main_module, "db", _FakeDb(None))
    resp = client.get(f"/payments/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_payment_found_returns_200(client, monkeypatch):
    from src.routes import main as main_module
    monkeypatch.setattr(main_module, "db", _FakeDb(_fake_payment_orm(status=Status.PENDING)))
    resp = client.get(f"/payments/{uuid.uuid4()}")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "pending"
