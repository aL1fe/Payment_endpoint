from src.extensions import db
from src.models.user_payment_method import UserPaymentMethodORM


class UserPaymentMethodRepository:
    def get_default_for_user(self, user_id) -> UserPaymentMethodORM | None:
        return db.session.execute(
            db.select(UserPaymentMethodORM).filter_by(user_id=user_id, is_default=True)
        ).scalar_one_or_none()
