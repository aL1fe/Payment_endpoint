import uuid
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db
from src.enums.status import Status


class PaymentORM(db.Model):
    __tablename__ = "payments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey("carts.id"), nullable=False)
    amount = db.Column(db.Numeric(precision=12, scale=2), nullable=False)
    status = db.Column(db.Enum(Status, name="payment_status"), nullable=False, default=Status.PENDING)
    provider_token = db.Column(db.String(64), nullable=False)
    # ID of the charge transaction returned by the payment provider; unknown until charge() responds.
    provider_reference = db.Column(db.String(64), nullable=True)
    idempotency_key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        db.CheckConstraint("amount > 0", name="check_amount_positive"),
    )

    def __repr__(self):
        return f"<PaymentORM id={self.id} status={self.status}>"
