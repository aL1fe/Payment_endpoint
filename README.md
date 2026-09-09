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
