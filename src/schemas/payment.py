from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

from src.enums.status import Status


@dataclass
class Payment:
    id: int
    user_id: int
    amount: Decimal
    status: Status
    transaction_id: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm(cls, orm_obj) -> "Payment":
        return cls(
            id=orm_obj.id,
            user_id=orm_obj.user_id,
            amount=orm_obj.amount,
            status=orm_obj.status,
            transaction_id=orm_obj.transaction_id,
            idempotency_key=orm_obj.idempotency_key,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )
