"""Test doubles for the repositories and payment provider used by PaymentService.

Kept simple and in-memory so PaymentService tests don't need a real database
or network calls, and behavior is fully controlled by each test.
"""

from src.services.payment_provider import PaymentGateway


class FakeCartRepository:
    def __init__(self, cart=None, items=None):
        self.cart = cart
        self.items = items or []
        self.for_update_flags = []

    def get_by_id(self, cart_id, for_update=False):
        self.for_update_flags.append(for_update)
        if self.cart is not None and self.cart.id == cart_id:
            return self.cart
        return None

    def get_items(self, cart_id):
        return self.items

    def mark_checked_out(self, cart):
        cart.status = "checked_out"


class FakePaymentMethodRepository:
    def __init__(self, method=None):
        self.method = method

    def get_default_for_user(self, user_id):
        return self.method


class FakePaymentRepository:
    def __init__(self):
        self.created = []
        self._by_key = {}

    def create(self, payment):
        self.created.append(payment)
        self._by_key[payment.idempotency_key] = payment
        return payment

    def get_by_idempotency_key(self, idempotency_key):
        return self._by_key.get(idempotency_key)


class ScriptedPaymentProvider(PaymentGateway):
    """Plays back a fixed script of results/exceptions, one per charge() call.
    The last scripted item repeats if charge() is called more times than the script length."""

    def __init__(self, script):
        self._script = list(script)
        self.calls = 0

    def charge(self, provider_token, amount):
        self.calls += 1
        outcome = self._script[min(self.calls, len(self._script)) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
