from flask import Blueprint, jsonify, abort, request
from src.extensions import db

from src.models.payment import PaymentORM
from src.schemas.payment import Payment
from src.services.payment_service import (
    PaymentService,
    CartNotFoundError,
    CartNotActiveError,
    PaymentMethodNotFoundError,
    IdempotencyKeyConflictError,
    PaymentProviderError,
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


@main_bp.route("/payments/<uuid:cart_id>", methods=["POST"])
def start_payment(cart_id):
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        abort(400, description="Idempotency-Key header is required")

    try:
        payment_orm = PaymentService().start_payment(cart_id, idempotency_key)
    except CartNotFoundError as exc:
        abort(404, description=str(exc))
    except CartNotActiveError as exc:
        abort(409, description=str(exc))
    except PaymentMethodNotFoundError as exc:
        abort(422, description=str(exc))
    except IdempotencyKeyConflictError as exc:
        abort(409, description=str(exc))
    except PaymentProviderError as exc:
        abort(502, description=str(exc))

    payment = Payment.from_orm(payment_orm)
    return jsonify(_serialize_payment(payment)), 201
