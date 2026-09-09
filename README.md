# Payment Endpoint

## Getting Started

### 1. Create a Data Volume
Create a persistent data volume to prevent data loss when the container is removed:

```bash
docker volume create payment-service-data
```

### 2. Configure Environment Variables
Create a `.env` file using `.env.example` as a template:  
Example `.env` file:

```dotenv
DB_USER=your_username
DB_PASS=your_password
DB_HOST=127.0.0.1
DB_PORT=5444
DB_NAME=payment_service
```

### 3. Initialize the Database
Start the services using Docker Compose:

```bash
docker compose up -d
```

Load the base schema (tables owned by other parts of the system, plus sample data). This project does not manage these tables with Alembic, so they must be created once, directly with `psql`:

```bash
psql "postgresql://your_username:your_password@127.0.0.1:5444/payment_service" -f migrations/base_schema.sql
```

Then create the `payments` table with Alembic:

```bash
flask db upgrade
```

### 4. Set Up Virtual Environment and Install Dependencies
Run the setup script to configure the virtual environment and install all required dependencies:

```bash
. ./setup.sh
```

### 5. Run the Application
For development:

```bash
python run.py
```

For production:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Assumptions

The task description did not cover every detail. Here is what we assumed:

1. The `payments` table is new. The existing tables (`users`, `carts`, `cart_items`, `user_payment_methods`) are not changed. Our app only reads from them, except for one field: `carts.status`, which we update after a payment.
2. Each user has exactly one default payment method (`is_default = TRUE`). If there is none, the payment cannot start and the API returns `422`.
3. Only a cart with status `active` can be paid. Paying for a `checked_out` or `abandoned` cart is not allowed and returns `409`.
4. A cart with no items cannot be paid. This returns `422` instead of a database error.
5. **Idempotency is the client's responsibility.** The client must send an `Idempotency-Key` header with `POST /payments/<cart_id>`. Without it, the API returns `400`.
   - Same key + same cart: the API returns the result of the first attempt and does not charge the card again.
   - Same key + a different cart: the API returns `409`, because the key is being reused incorrectly.
6. **Only one payment can happen per cart at a time.** We lock the cart row in the database (`SELECT ... FOR UPDATE`) while a payment is running. This stops two parallel requests (for example, from a double click or a client retry) from charging the same cart twice.
7. **The payment provider is a mock** (`PaymentProvider`). It declines about 10% of charges at random. It can also simulate a transient failure (like a timeout), but this is turned off by default and is only used to test retries.
8. **We only retry transient errors**, such as a timeout from the provider. We do not retry a declined card, because a decline is a final answer, not a temporary problem.
9. If the provider never responds after all retries, we mark the payment as `FAILED` (not "unknown"). This keeps the payment from staying `PENDING` forever. The cart is not marked as `checked_out` in this case.
10. **Authentication and authorization are out of scope.** The API does not check that the caller is the real owner of the cart.
11. **Only one currency is supported.** The `payments` table does not store a currency column; we assume everything is in USD, matching the sample data.
