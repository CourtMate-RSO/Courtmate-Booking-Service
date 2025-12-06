# Booking Service

Handles reservations and availability checks for the CourtMate platform.

## 📋 Features

- Create and manage court bookings
- Check court availability
- Cancel bookings
- Retrieve user booking history
- Integration with Supabase for data persistence

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Supabase account and credentials

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .example.env .env
   ```

2. Update `.env` with your Supabase credentials:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_JWT_SECRET=your-jwt-secret-here
   ENV=dev
   API_VERSION=v1
   ```

### Local Development (Python)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the service:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Access the API:
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🐳 Docker Deployment

### Development (with docker-compose)

The easiest way to test the service locally:

```bash
# Start the service
docker-compose up

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

The service will be available at http://localhost:8000

### Production

#### Build the image:
```bash
docker build -t booking-service:latest .
```

#### Run with environment variables:

**⚠️ DO NOT use .env file in production - pass environment variables directly**

```bash
docker run -d \
  -p 8000:8000 \
  -e SUPABASE_URL=$SUPABASE_URL \
  -e SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY \
  -e SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  -e SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET \
  -e ENV=prod \
  -e API_VERSION=v1 \
  --name booking-service \
  booking-service:latest
```

#### Using a secrets file (more secure):
```bash
# Create a secrets file (not in version control)
cat > booking-secrets.env << EOF
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
ENV=prod
API_VERSION=v1
EOF

# Run with env file
docker run -d \
  -p 8000:8000 \
  --env-file booking-secrets.env \
  --name booking-service \
  booking-service:latest
```

### Docker Commands

```bash
# View logs
docker logs -f booking-service

# Stop container
docker stop booking-service

# Remove container
docker rm booking-service

# Restart container
docker restart booking-service

# Execute commands inside container
docker exec -it booking-service bash
```

## 🧪 Testing the Service

### Health Check
```bash
curl http://localhost:8000/reservation/health
```

Expected response:
```json
{"status":"ok"}
```

### Access API Documentation
- Swagger UI: http://localhost:8000/reservation/docs
- ReDoc: http://localhost:8000/reservation/redoc

### Create a Booking
```bash
curl -X POST http://localhost:8000/reservation/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "court_id": "uuid-here",
    "starts_at": "2025-12-10T14:00:00Z",
    "ends_at": "2025-12-10T16:00:00Z"
  }'
```

### Get User Reservations
```bash
curl http://localhost:8000/reservation/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Cancel a Reservation
```bash
curl -X PUT "http://localhost:8000/reservation/{reservation_id}?reason=Changed%20plans" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📁 Project Structure

```
Courtmate-Booking-Service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   └── supabase_client.py   # Supabase integration
├── .env                     # Environment variables (gitignored)
├── .example.env             # Example environment file
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 API Endpoints

All endpoints are prefixed with `/reservation`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reservation/health` | Health check |
| GET | `/reservation/docs` | Swagger API documentation |
| POST | `/reservation/` | Create a new reservation |
| GET | `/reservation/` | Get user's reservations |
| GET | `/reservation/{reservation_id}` | Get reservation details |
| PUT | `/reservation/{reservation_id}` | Cancel a reservation |

## 🔐 Authentication

All endpoints (except `/health`) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

Tokens are issued by the User Service and validated using the Supabase JWT secret.

## 🌍 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for admin operations | Yes |
| `SUPABASE_ANON_KEY` | Anonymous key for client operations | Yes |
| `SUPABASE_JWT_SECRET` | JWT secret for token validation | Yes |
| `ENV` | Environment (dev/staging/prod) | No (default: dev) |
| `API_VERSION` | API version | No (default: v1) |

## 🐛 Troubleshooting

### Container won't start
- Check logs: `docker logs booking-service`
- Verify environment variables are set correctly
- Ensure port 8000 is not already in use

### Database connection errors
- Verify Supabase credentials are correct
- Check network connectivity to Supabase
- Ensure Supabase project is active

### Authentication failures
- Verify JWT secret matches User Service
- Check token expiration
- Ensure token format is correct

## 📝 License

Copyright © 2025 CourtMate. All rights reserved.
