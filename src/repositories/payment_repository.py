from src.extensions import db
from src.models.payment import PaymentORM


class PaymentRepository:
    def get_by_id(self, payment_id) -> PaymentORM | None:
        return db.session.get(PaymentORM, payment_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> PaymentORM | None:
        return db.session.execute(
            db.select(PaymentORM).filter_by(idempotency_key=idempotency_key)
        ).scalar_one_or_none()

    def create(self, payment: PaymentORM) -> PaymentORM:
        db.session.add(payment)
        return payment
