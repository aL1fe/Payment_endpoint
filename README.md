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
POSTGRES_DB=payment_service
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

### 3. Initialize the Database

Start the services using Docker Compose:

```bash
docker compose up -d
```

