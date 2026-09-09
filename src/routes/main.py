from flask import Blueprint, jsonify, abort
from src.extensions import db

from src.models.payment import PaymentORM
from src.schemas.payment import Payment
from src.services.payment_service import (
    PaymentService,
    CartNotFoundError,
    PaymentMethodNotFoundError,
)


main_bp = Blueprint("main", __name__)


def _serialize_payment(payment: Payment) -> dict:
    return {
        "id": str(payment.id),
        "user_id": str(payment.user_id),
        "cart_id": str(payment.cart_id),
        "amount": str(payment.amount),
        "status": payment.status.value,
        "provider_token": payment.provider_token,
        "provider_reference": payment.provider_reference,
        "idempotency_key": payment.idempotency_key,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
    }


@main_bp.route("/payments/<uuid:payment_id>")
def get_payment(payment_id):
    payment_orm = db.session.get(PaymentORM, payment_id)
    if payment_orm is None:
        abort(404, description="Payment not found")

    payment = Payment.from_orm(payment_orm)
    return jsonify(_serialize_payment(payment))


@main_bp.route("/carts/<uuid:cart_id>/payments", methods=["POST"])
def start_payment(cart_id):
    try:
        payment_orm = PaymentService().start_payment(cart_id)
    except CartNotFoundError as exc:
        abort(404, description=str(exc))
    except PaymentMethodNotFoundError as exc:
        abort(422, description=str(exc))

    payment = Payment.from_orm(payment_orm)
    return jsonify(_serialize_payment(payment)), 201

