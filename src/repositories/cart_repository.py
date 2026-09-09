from src.extensions import db
from src.models.cart import CartORM, CartItemORM


class CartRepository:
    def get_by_id(self, cart_id, for_update: bool = False) -> CartORM | None:
        query = db.select(CartORM).filter_by(id=cart_id)
        if for_update:
            query = query.with_for_update()
        return db.session.execute(query).scalar_one_or_none()

    def get_items(self, cart_id) -> list[CartItemORM]:
        return db.session.execute(
            db.select(CartItemORM).filter_by(cart_id=cart_id)
        ).scalars().all()

    def mark_checked_out(self, cart: CartORM) -> None:
        cart.status = "checked_out"
