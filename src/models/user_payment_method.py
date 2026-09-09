from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db


class UserPaymentMethodORM(db.Model):
    """Read-only mapping to the user_payment_methods table owned by the accounts part of the system."""

    __tablename__ = "user_payment_methods"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    provider_token = db.Column(db.Text, nullable=False)
    last_four = db.Column(db.CHAR(4))
    is_default = db.Column(db.Boolean, nullable=False, default=False)
