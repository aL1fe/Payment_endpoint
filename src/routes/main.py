from flask import Blueprint, jsonify, abort
from src.extensions import db

from src.models.payment_entity import PaymentORM
from src.schemas.payment import Payment


main_bp = Blueprint("main", __name__)

@main_bp.route("/payments/<int:payment_id>")
def get_payment(payment_id):
    payment_orm = db.session.get(PaymentORM, payment_id)
    if payment_orm is None:
        abort(404, description="Payment not found")

    payment = Payment.from_orm(payment_orm)
    return jsonify({
        "id": payment.id,
        "user_id": payment.user_id,
        "amount": str(payment.amount),
        "status": payment.status.value,
        "transaction_id": payment.transaction_id,
        "idempotency_key": payment.idempotency_key,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
    })
