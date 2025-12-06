# Testing the Booking Service - Complete Guide

## Understanding the "Not authenticated" Error

The error you received:
```json
{
  "detail": "Not authenticated"
}
```

This means the Booking Service **requires a valid JWT token** to create or view reservations. This is a security feature - only authenticated users can make bookings.

---

## How Authentication Works

1. **User Service** (`/auth/login` or `/auth/signup`) → Returns JWT token
2. **Booking Service** uses that token to:
   - Verify the user's identity
   - Automatically associate reservations with the user
   - Enforce Row Level Security (RLS) policies in Supabase

---

## ✅ Implemented Features

Based on the code analysis, the Booking Service has these endpoints:

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/reservation/health` | GET | Health check | ❌ No |
| `/reservation/` | POST | Create a reservation | ✅ Yes |
| `/reservation/` | GET | Get user's reservations | ✅ Yes |
| `/reservation/{id}` | PUT | Cancel a reservation | ✅ Yes |

**Note:** The GET `/reservation/` endpoint automatically returns only the authenticated user's reservations (filtered by RLS).

---

## 🧪 How to Test - Step by Step

### Option 1: Using the UI (Easiest)

The UI at http://localhost:3000 handles authentication automatically:

1. **Sign up or login** at http://localhost:3000/login
2. **Navigate to a court** and make a booking
3. **View your bookings** at http://localhost:3000/bookings

The UI automatically includes the JWT token in all requests.

---

### Option 2: Using curl/Postman (Manual Testing)

#### Step 1: Start the User Service

The User Service must be running to get authentication tokens:

```bash
# Option A: Using docker-compose (if available)
cd /Users/aljazjustin/soal-programi/MAGI/ROS/Courtmate-User-Service
docker-compose up -d

# Option B: Using k3d (if deployed)
# User service should be at http://localhost:30000/auth
```

#### Step 2: Create a Test User (if needed)

```bash
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "test@example.com"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "..."
}
```

**Save the `access_token`** - you'll need it for all booking requests!

#### Step 3: Login (if user already exists)

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

#### Step 4: Create a Reservation

Replace `YOUR_TOKEN_HERE` with the actual access_token from step 2 or 3:

```bash
curl -X POST http://localhost:8000/reservation/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "court_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "starts_at": "2025-12-10T14:00:00Z",
    "ends_at": "2025-12-10T16:00:00Z"
  }'
```

**Expected Success Response (201):**
```json
{
  "id": "reservation-uuid",
  "court_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "your-user-uuid",
  "starts_at": "2025-12-10T14:00:00Z",
  "ends_at": "2025-12-10T16:00:00Z",
  "total_price": 50.00,
  "created_at": "2025-12-06T11:00:00Z",
  "cancelled_at": null,
  "cancel_reason": null
}
```

#### Step 5: Get Your Reservations

```bash
curl http://localhost:8000/reservation/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:**
```json
[
  {
    "id": "reservation-uuid",
    "court_id": "court-uuid",
    "user_id": "your-user-uuid",
    "starts_at": "2025-12-10T14:00:00Z",
    "ends_at": "2025-12-10T16:00:00Z",
    "total_price": 50.00,
    "created_at": "2025-12-06T11:00:00Z",
    "cancelled_at": null,
    "cancel_reason": null
  }
]
```

#### Step 6: Cancel a Reservation

```bash
curl -X PUT "http://localhost:8000/reservation/RESERVATION_ID?reason=Changed%20plans" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### Option 3: Using Swagger UI (Interactive)

1. **Start User Service** (to get a token)
2. **Open Booking Service Swagger:** http://localhost:8000/reservation/docs
3. **Click "Authorize" button** (top right, lock icon)
4. **Enter:** `Bearer YOUR_TOKEN_HERE` (include the word "Bearer")
5. **Click "Authorize"**
6. **Now you can test all endpoints** using the "Try it out" buttons

---

## 🔍 Troubleshooting

### "Not authenticated" error
- ✅ Make sure you're including the `Authorization: Bearer <token>` header
- ✅ Verify the token is valid (not expired)
- ✅ Check the token format: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### "Invalid credentials" when logging in
- ✅ Check email and password are correct
- ✅ Ensure user exists (try signup first)
- ✅ Verify Supabase credentials in `.env` are correct

### "Court not found" or database errors
- ✅ Use a valid `court_id` from your database
- ✅ Check Supabase connection is working
- ✅ Verify RLS policies allow the operation

### User Service not running
```bash
# Check if it's running
docker ps | grep user-service

# If not, start it
cd /Users/aljazjustin/soal-programi/MAGI/ROS/Courtmate-User-Service
docker-compose up -d
```

---

## 📝 Quick Reference

### Get a Token
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123"}' \
  | jq -r '.access_token')

echo $TOKEN
```

### Use the Token
```bash
# Create reservation
curl -X POST http://localhost:8000/reservation/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "court_id": "your-court-id",
    "starts_at": "2025-12-10T14:00:00Z",
    "ends_at": "2025-12-10T16:00:00Z"
  }'

# Get reservations
curl http://localhost:8000/reservation/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Summary

**To test reservations, you need:**
1. ✅ User Service running (for authentication)
2. ✅ Booking Service running (already running via docker-compose)
3. ✅ A valid JWT token (from login/signup)
4. ✅ Include token in `Authorization: Bearer <token>` header

**The features ARE implemented:**
- ✅ Create reservation (POST /reservation/)
- ✅ Get user's reservations (GET /reservation/)
- ✅ Cancel reservation (PUT /reservation/{id})
