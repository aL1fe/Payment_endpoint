class CartNotFoundError(Exception):
    def __init__(self, message="Cart not found"):
        super().__init__(message)


class PaymentMethodNotFoundError(Exception):
    def __init__(self, message="Payment method not found"):
        super().__init__(message)


class IdempotencyKeyConflictError(Exception):
    def __init__(self, message="Idempotency key was already used for a different cart"):
        super().__init__(message)


class CartNotActiveError(Exception):
    def __init__(self, message="Cart is not active"):
        super().__init__(message)


class PaymentProviderError(Exception):
    def __init__(self, message="Payment provider call failed"):
        super().__init__(message)


class EmptyCartError(Exception):
    def __init__(self, message="Cart has no items"):
        super().__init__(message)
