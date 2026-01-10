# Booking Service

Handles reservations and availability checks for the CourtMate platform.

## 📋 Features

- Create and manage court bookings
- Check court availability
- Cancel bookings
- Retrieve user booking history
- Integration with Supabase for data persistence

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

