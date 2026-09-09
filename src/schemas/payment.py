import uuid
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional

from src.enums.status import Status


@dataclass
class Payment:
    id: uuid.UUID
    user_id: uuid.UUID
    cart_id: uuid.UUID
    amount: Decimal
    status: Status
    provider_token: str
    provider_reference: Optional[str]
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, orm_obj) -> "Payment":
        return cls(
            id=orm_obj.id,
            user_id=orm_obj.user_id,
            cart_id=orm_obj.cart_id,
            amount=orm_obj.amount,
            status=orm_obj.status,
            provider_token=orm_obj.provider_token,
            provider_reference=orm_obj.provider_reference,
            idempotency_key=orm_obj.idempotency_key,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )
