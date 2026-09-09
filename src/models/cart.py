from sqlalchemy.dialects.postgresql import UUID

from src.extensions import db


class CartORM(db.Model):
    """Read-only mapping to the carts table owned by the cart part of the system."""

    __tablename__ = "carts"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.Text, nullable=False)


class CartItemORM(db.Model):
    """Read-only mapping to the cart_items table owned by the cart part of the system."""

    __tablename__ = "cart_items"

    id = db.Column(UUID(as_uuid=True), primary_key=True)
    cart_id = db.Column(UUID(as_uuid=True), db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(precision=12, scale=2), nullable=False)
