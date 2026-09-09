import random
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ChargeResult:
    success: bool
    provider_reference: str


class PaymentGateway(ABC):
    """Contract any payment provider integration must follow. Swapping the
    provider later means writing a new class here, nothing else has to change."""

    @abstractmethod
    def charge(self, provider_token: str, amount: Decimal) -> ChargeResult:
        ...


class PaymentProvider(PaymentGateway):
    """Mock of the external payment provider. Charges are simulated locally,
    no real card token or amount is sent anywhere."""

    def charge(self, provider_token: str, amount: Decimal) -> ChargeResult:
        success = random.random() > 0.1
        return ChargeResult(success=success, provider_reference=f"prov_{uuid.uuid4().hex}")
