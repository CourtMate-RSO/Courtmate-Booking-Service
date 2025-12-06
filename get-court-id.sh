#!/bin/bash

# Helper script to get a valid court_id from the Court Service

echo "🔍 Fetching available courts from Court Service..."
echo ""

# Try to get courts from the Court Service
COURTS_RESPONSE=$(curl -s "http://localhost:8002/courts/nearby?latitude=46.0569&longitude=14.5058&radius_km=10" 2>/dev/null)

if [ $? -eq 0 ] && echo "$COURTS_RESPONSE" | jq -e '.' >/dev/null 2>&1; then
    echo "✅ Found courts in database:"
    echo ""
    
    # Extract court IDs and names
    echo "$COURTS_RESPONSE" | jq -r '.[] | "Court ID: \(.id)\nName: \(.name)\nAddress: \(.address)\n"'
    
    echo "=============================================="
    echo "💡 Copy one of the Court IDs above and use it in your test script"
    echo ""
    
    # Get the first court ID
    FIRST_COURT_ID=$(echo "$COURTS_RESPONSE" | jq -r '.[0].id' 2>/dev/null)
    
    if [ "$FIRST_COURT_ID" != "null" ] && [ -n "$FIRST_COURT_ID" ]; then
        echo "📝 First court ID: $FIRST_COURT_ID"
        echo ""
        echo "To use this in your test script, update line 64:"
        echo "COURT_ID=\"$FIRST_COURT_ID\""
    fi
else
    echo "⚠️  Could not fetch courts from Court Service"
    echo ""
    echo "Make sure the Court Service is running:"
    echo "  docker ps | grep court-service"
    echo ""
    echo "Or check if there are courts in your database via Supabase dashboard"
fi
