from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    ReservationCreate, Reservation
)
from app.supabase_client import (
    user_supabase_client,
    admin_supabase_client,
)
import os
import logging
import sys
from dotenv import load_dotenv
import httpx
from postgrest.exceptions import APIError  # comes with supabase-py

# Structured JSON logging setup
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("booking-service")
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s',
    rename_fields={"levelname": "level", "asctime": "timestamp"}
)
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Load environment variables from .env file
load_dotenv()

RESERVATION_PREFIX = "/reservation"
ENV = os.getenv("ENV", "dev")

# FastAPI app
if ENV == "prod":
    app = FastAPI(
        title="Authentication API",
        description="API for managing user authentication.",
        version="1.0.0",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
else:
    app = FastAPI(
        title="Authentication API",
        description="API for managing user authentication.",
        version="1.0.0",
        openapi_url=f"{RESERVATION_PREFIX}/openapi.json",
        docs_url=f"{RESERVATION_PREFIX}/docs",
        redoc_url=f"{RESERVATION_PREFIX}/redoc",
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics instrumentation
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Security and Supabase configurations
security = HTTPBearer()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "Missing SUPABASE_URL, SUPABASE_ANON_KEY, or SUPABASE_SERVICE_ROLE_KEY in environment variables")


# Endpoints
@app.get(f"{RESERVATION_PREFIX}/")
async def get_user_reservations(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all reservations for the authenticated user."""
    token = credentials.credentials
    supabase = user_supabase_client(token)
    admin_supabase = admin_supabase_client()
    
    try:
        # Fetch user's reservations from Supabase
        # The RLS policies will automatically filter by user_id
        logger.info("Fetching user reservations")
        response = supabase.table("reservations").select("*").order("starts_at", desc=True).execute()
        
        data = response.data
        if not data:
            logger.info("No reservations found")
            return []
        
        logger.info(f"Got {len(data)} reservations")
        
        # Enhance reservations with court information
        enriched_reservations = []
        for item in data:
            try:
                reservation = Reservation(**item)
                
                # Fetch court details using admin client (bypassing RLS)
                try:
                    court_response = admin_supabase.table("courts").select("id, name, sport, facility_id").eq("id", str(item["court_id"])).single().execute()
                    if court_response.data:
                        reservation.court = court_response.data
                        logger.info(f"Added court details to reservation {item['id']}")
                except Exception as court_error:
                    logger.warning(f"Failed to fetch court details for {item['court_id']}: {court_error}")
                    # Continue without court details if fetch fails
                
                enriched_reservations.append(reservation)
            except Exception as parse_error:
                logger.error(f"Failed to parse reservation {item.get('id', '?')}: {parse_error}")
                continue
        
        logger.info(f"Returning {len(enriched_reservations)} enriched reservations")
        return enriched_reservations
        
    except APIError as e:
        logger.error(f"Supabase API Error in get_user_reservations: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supabase error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_user_reservations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@app.get(f"{RESERVATION_PREFIX}/health")
async def health_check():
    return {"status": "ok"}


# Create reservation
@app.post(f"{RESERVATION_PREFIX}/", response_model=Reservation, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    reservation: ReservationCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Create a new reservation for the authenticated user."""
    token = credentials.credentials
    logger.info(f"create_reservation called with token starting: {token[:20]}...")
    
    try:
        supabase = user_supabase_client(token)
        logger.info("Supabase client created successfully")
    except Exception as e:
        logger.error(f"Failed to create supabase client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    # Resolve user id from the auth token so we can set user_id on the inserted row
    try:
        user_resp = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_ANON_KEY,
            },
            timeout=5.0
        )
        if user_resp.status_code == 200:
            user_json = user_resp.json()
            user_id = user_json.get("id")
            logger.info(f"Resolved user_id={user_id} from token")
        else:
            logger.warning(f"Could not resolve user from token: status={user_resp.status_code}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving user from token: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    logger.info(f"create_reservation: court_id={reservation.court_id}, starts_at={reservation.starts_at}, ends_at={reservation.ends_at}")

    try:
        # Insert reservation directly into table (RLS will enforce user_id)
        reservation_data = {
            "court_id": str(reservation.court_id),
            "user_id": str(user_id),
            "starts_at": reservation.starts_at.isoformat(),
            "ends_at": reservation.ends_at.isoformat(),
        }
        logger.info(f"Inserting reservation: {reservation_data}")

        response = supabase.table("reservations").insert(reservation_data).execute()
        logger.info(f"Insert response data: {response.data}")

        if not response.data or len(response.data) == 0:
            logger.error("No reservation returned from insert")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create reservation",
            )

        reservation_row = response.data[0]
        logger.info(f"Created reservation: {reservation_row}")
        return Reservation(**reservation_row)

    except APIError as e:
        logger.error(f"Supabase API Error: {e.message if hasattr(e, 'message') else str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message if hasattr(e, 'message') else str(e),
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating reservation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )



# Get reservation by ID
@app.get(f"{RESERVATION_PREFIX}/{{reservation_id}}")
async def get_reservation(reservation_id: str):
    pass

# Cancel reservation
@app.put(f"{RESERVATION_PREFIX}/{{reservation_id}}")
async def cancel_reservation(
    reservation_id: str,
    reason: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel an existing reservation."""
    token = credentials.credentials
    supabase = user_supabase_client(token)
    
    try:
        logger.info(f"Canceling reservation {reservation_id} with reason: {reason}")
        
        # Update row in reservations table to set cancelled_at and cancel_reason
        response = supabase.table("reservations").update({
            "cancelled_at": "now()",
            "cancel_reason": reason
        }).eq("id", reservation_id).execute()
        
        if not response.data:
            logger.warning(f"Reservation {reservation_id} not found for cancellation")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )
        
        logger.info(f"Successfully cancelled reservation {reservation_id}")
        return response.data[0]
        
    except APIError as e:
        logger.error(f"Supabase API Error canceling reservation: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error canceling reservation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    