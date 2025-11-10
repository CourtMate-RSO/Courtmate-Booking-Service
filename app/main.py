from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import (
    ReservationCreate, Reservation
)
from app.supabase_client import (
    user_supabase_client
)
import os
from dotenv import load_dotenv
import httpx
from fastapi.middleware.cors import CORSMiddleware
from postgrest.exceptions import APIError  # comes with supabase-py

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
async def root():
    return {"message": "Hello World"}

@app.get(f"{RESERVATION_PREFIX}/health")
async def health_check():
    return {"status": "ok"}


# Create reservation
@app.post(f"{RESERVATION_PREFIX}/", response_model=Reservation, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    reservation: ReservationCreate = None,
):
    token = credentials.credentials
    supabase = user_supabase_client(token)

    try:
        # ⚠️ Make sure these keys match your SQL function argument names
        response = supabase.rpc(
            "create_reservation",
            {
                # if your function is (p_court_id, p_starts_at, p_ends_at):
                "p_court_id": str(reservation.court_id),
                "p_starts_at": reservation.starts_at.isoformat(),
                "p_ends_at": reservation.ends_at.isoformat(),
            },
        ).execute()

    # Errors thrown from PostgREST / your function (RAISE EXCEPTION, RLS, etc.)
    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message or str(e),
        )

    # Network / config / anything else
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )

    # response is a SingleAPIResponse or APIResponse
    data = response.data
    if not data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No reservation returned from create_reservation",
        )

    # If it’s a list, take the first element. If it’s a dict, use it directly.
    if isinstance(data, list):
        reservation_data = data[0]
    else:
        reservation_data = data

    return Reservation(**reservation_data)



# Get reservation by ID
@app.get(f"{RESERVATION_PREFIX}/{{reservation_id}}")
async def get_reservation(reservation_id: str):
    pass

# Cancel reservation
@app.put(f"{RESERVATION_PREFIX}/{{reservation_id}}")
async def cancel_reservation(reservation_id: str, reason: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    supabase = user_supabase_client(token)
    try:
        # update row in reservations table to set cancelled_at and cancel_reason
        response = supabase.table("reservations").update({
            "cancelled_at": "now()",
            "cancel_reason": reason
        }).eq("id", reservation_id).execute()
        data = response.data
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )
        return data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
    