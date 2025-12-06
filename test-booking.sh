#!/bin/bash

# Test Booking Service - Practical Demo
# This script demonstrates how to authenticate and create a reservation

set -e

echo "🧪 Testing Booking Service with Authentication"
echo "=============================================="
echo ""

# Configuration
USER_SERVICE="http://localhost:8003"
BOOKING_SERVICE="http://localhost:8002"
TEST_EMAIL="aljaz.justin1+1@gmail.com"
TEST_PASSWORD="123456"

echo "📝 Step 1: Creating/Login test user..."
echo "Email: $TEST_EMAIL"
echo ""

# Try to login first, if it fails, signup
LOGIN_RESPONSE=$(curl -s -X POST "$USER_SERVICE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
  2>/dev/null || echo '{"error":"login_failed"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Login successful!"
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
else
    echo "⚠️  Login failed, trying signup..."
    SIGNUP_RESPONSE=$(curl -s -X POST "$USER_SERVICE/auth/signup" \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")
    
    if echo "$SIGNUP_RESPONSE" | grep -q "access_token"; then
        echo "✅ Signup successful!"
        TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.access_token')
    else
        echo "❌ Both login and signup failed!"
        echo "Response: $SIGNUP_RESPONSE"
        exit 1
    fi
fi

echo ""
echo "🔑 Access Token (first 50 chars): ${TOKEN:0:50}..."
echo ""

echo "📝 Step 2: Getting existing reservations..."
EXISTING_RESERVATIONS=$(curl -s "$BOOKING_SERVICE/reservation/" \
  -H "Authorization: Bearer $TOKEN")

echo "Current reservations:"
echo "$EXISTING_RESERVATIONS" | jq '.'
echo ""

echo "📝 Step 3: Creating a new reservation..."
echo "Note: This will fail if you don't have a valid court_id in your database"
echo ""

# You'll need to replace this with a real court_id from your database
COURT_ID="870ca3c5-713c-484f-84a5-646e5faa5c59"
STARTS_AT="2025-12-11T14:00:00Z"  # Different day
ENDS_AT="2025-12-11T16:00:00Z"

CREATE_RESPONSE=$(curl -s -X POST "$BOOKING_SERVICE/reservation/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"court_id\": \"$COURT_ID\",
    \"starts_at\": \"$STARTS_AT\",
    \"ends_at\": \"$ENDS_AT\"
  }")

echo "Create reservation response:"
echo "$CREATE_RESPONSE" | jq '.'
echo ""

if echo "$CREATE_RESPONSE" | grep -q '"id"'; then
    echo "✅ Reservation created successfully!"
    RESERVATION_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
    
    echo ""
    echo "📝 Step 4: Fetching updated reservations..."
    UPDATED_RESERVATIONS=$(curl -s "$BOOKING_SERVICE/reservation/" \
      -H "Authorization: Bearer $TOKEN")
    echo "$UPDATED_RESERVATIONS" | jq '.'
else
    echo "⚠️  Reservation creation failed (this is expected if court_id doesn't exist)"
    echo "To create a real reservation, you need a valid court_id from your database"
fi

echo ""
echo "=============================================="
echo "✅ Test complete!"
echo ""
echo "💡 Tips:"
echo "  - Your token: $TOKEN"
echo "  - Use this token in Swagger UI: http://localhost:8000/reservation/docs"
echo "  - Click 'Authorize' and enter: Bearer $TOKEN"
echo ""
