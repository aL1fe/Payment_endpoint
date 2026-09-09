from decimal import Decimal

from src.services.payment_provider import PaymentGateway, PaymentProvider


def test_payment_provider_is_a_payment_gateway():
    assert isinstance(PaymentProvider(), PaymentGateway)


def test_charge_returns_a_result_with_a_provider_reference():
    provider = PaymentProvider()
    result = provider.charge("tok_test", Decimal("10.00"))
    assert isinstance(result.success, bool)
    assert result.provider_reference
