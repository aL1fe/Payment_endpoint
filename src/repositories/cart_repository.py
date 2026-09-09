from src.extensions import db
from src.models.cart import CartORM, CartItemORM


class CartRepository:
    def get_by_id(self, cart_id) -> CartORM | None:
        return db.session.get(CartORM, cart_id)

    def get_items(self, cart_id) -> list[CartItemORM]:
        return db.session.execute(
            db.select(CartItemORM).filter_by(cart_id=cart_id)
        ).scalars().all()

    def mark_checked_out(self, cart: CartORM) -> None:
        cart.status = "checked_out"
