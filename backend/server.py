from fastapi import FastAPI, APIRouter, Request, Response, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
import requests
from datetime import datetime, timezone, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class LiveSession(BaseModel):
    id: str
    title: str
    subtitle: str
    astrologer: str
    watchers: str
    status: str
    image: str

class Astrologer(BaseModel):
    id: str
    name: str
    specialty: str
    rating: str
    status: str
    image: str

class SavedReadingCreate(BaseModel):
    title: str
    sign: str
    content: str
    lucky_color: str
    lucky_number: str

class SavedReading(SavedReadingCreate):
    id: str
    created_at: datetime

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None

class AuthCallback(BaseModel):
    session_id: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

async def current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": token})
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user, token

@api_router.post("/auth/session")
async def exchange_session(input: AuthCallback, response: Response):
    result = requests.get("https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data", headers={"X-Session-ID": input.session_id}, timeout=15)
    if result.status_code != 200:
        raise HTTPException(status_code=401, detail="OAuth session could not be verified")
    data = result.json()
    user = await db.users.find_one({"email": data["email"]}, {"_id": 0})
    if not user:
        user = {"user_id": f"user_{uuid.uuid4().hex[:12]}", "email": data["email"], "name": data.get("name") or data["email"], "picture": data.get("picture")}
        await db.users.insert_one(user.copy())
    else:
        await db.users.update_one({"user_id": user["user_id"]}, {"$set": {"name": data.get("name") or user["name"], "picture": data.get("picture") or user.get("picture")}})
        user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
    expires = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=7)
    await db.user_sessions.insert_one({"user_id": user["user_id"], "session_token": data["session_token"], "expires_at": expires.isoformat(), "created_at": datetime.now(timezone.utc).isoformat()})
    response.set_cookie("session_token", data["session_token"], httponly=True, secure=True, samesite="none", path="/", max_age=604800)
    return user

@api_router.get("/auth/me", response_model=User)
async def auth_me(request: Request):
    user, _ = await current_user(request)
    return user

@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    _, token = await current_user(request)
    await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}

SESSIONS = [
    {"id": "mars-transit", "title": "MARS TRANSIT 2024", "subtitle": "What it means for you?", "astrologer": "Acharya Dev", "watchers": "1.2K", "status": "LIVE", "image": "https://images.unsplash.com/photo-1462332420958-a05d1e002413?q=85&fm=jpg&crop=entropy"},
    {"id": "full-moon", "title": "FULL MOON MEDITATION", "subtitle": "Align your energy", "astrologer": "Sunita Sharma", "watchers": "842", "status": "LIVE", "image": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=85&fm=jpg&crop=entropy"},
]
ASTROLOGERS = [
    {"id": "acharya-dev", "name": "Acharya Dev", "specialty": "Vedic Astrology", "rating": "4.9", "status": "Online", "image": "https://images.unsplash.com/photo-1762795297387-b0b88a635aa6?q=85&fm=jpg&crop=entropy"},
    {"id": "sunita-sharma", "name": "Sunita Sharma", "specialty": "Tarot Reader", "rating": "4.8", "status": "Online", "image": "https://images.unsplash.com/photo-1762838346474-b32aee122d23?q=85&fm=jpg&crop=entropy"},
    {"id": "dr-anirudh", "name": "Dr. Anirudh", "specialty": "KP Astrology", "rating": "5.0", "status": "Online", "image": "https://images.unsplash.com/photo-1686464907994-3a9789d27178?q=85&fm=jpg&crop=entropy"},
]

@api_router.get("/sessions", response_model=List[LiveSession])
async def get_sessions():
    return SESSIONS

@api_router.get("/astrologers", response_model=List[Astrologer])
async def get_astrologers():
    return ASTROLOGERS

@api_router.post("/saved-readings", response_model=SavedReading)
async def save_reading(input: SavedReadingCreate, request: Request):
    user, _ = await current_user(request)
    reading = SavedReading(id=str(uuid.uuid4()), created_at=datetime.now(timezone.utc), **input.model_dump())
    doc = reading.model_dump()
    doc["created_at"] = reading.created_at.isoformat()
    doc["user_id"] = user["user_id"]
    await db.saved_readings.insert_one(doc)
    return reading

@api_router.get("/saved-readings", response_model=List[SavedReading])
async def get_saved_readings(request: Request):
    user, _ = await current_user(request)
    readings = await db.saved_readings.find({"user_id": user["user_id"]}, {"_id": 0, "user_id": 0}).sort("created_at", -1).to_list(50)
    for reading in readings:
        if isinstance(reading.get("created_at"), str):
            reading["created_at"] = datetime.fromisoformat(reading["created_at"])
    return readings

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[] if os.environ.get('CORS_ORIGINS') == '*' else os.environ.get('CORS_ORIGINS', '').split(','),
    allow_origin_regex='.*' if os.environ.get('CORS_ORIGINS') == '*' else None,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()