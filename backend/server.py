from fastapi import FastAPI, APIRouter, Request, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import base64
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
import requests
from datetime import datetime, timezone, date


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')
_google_key_check = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
print(f"[startup] Google/Gemini API key detected: {bool(_google_key_check)} (length: {len(_google_key_check) if _google_key_check else 0})")

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

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

SESSIONS = [
    {"id": "mars-transit", "title": "MARS TRANSIT 2024", "subtitle": "What it means for you?", "astrologer": "Acharya Dev", "watchers": "1.2K", "status": "LIVE", "image": "https://images.unsplash.com/photo-1462332420958-a05d1e002413?q=85&fm=jpg&crop=entropy"},
    {"id": "full-moon", "title": "FULL MOON MEDITATION", "subtitle": "Align your energy", "astrologer": "Sunita Sharma", "watchers": "842", "status": "LIVE", "image": "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?q=85&fm=jpg&crop=entropy"},
]
ASTROLOGERS = [
    {"id": "acharya-dev", "name": "Acharya Dev", "specialty": "Vedic Astrology", "rating": "4.9", "status": "Online", "image": "https://images.unsplash.com/photo-1762795297387-b0b88a635aa6?q=85&fm=jpg&crop=entropy"},
    {"id": "sunita-sharma", "name": "Sunita Sharma", "specialty": "Tarot Reader", "rating": "4.8", "status": "Online", "image": "https://images.unsplash.com/photo-1762838346474-b32aee122d23?q=85&fm=jpg&crop=entropy"},
    {"id": "dr-anirudh", "name": "Dr. Anirudh", "specialty": "KP Astrology", "rating": "5.0", "status": "Online", "image": "https://images.unsplash.com/photo-1686464907994-3a9789d27178?q=85&fm=jpg&crop=entropy"},
]

ART_DIR = ROOT_DIR / "generated_art"
ART_DIR.mkdir(exist_ok=True)

class ArtRequest(BaseModel):
    sign: str
    prompt: str

async def _generate_art_with_pollinations(prompt: str) -> bytes:
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt[:800])
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    params = {"width": 1024, "height": 1024, "nologo": "true", "model": "flux"}
    resp = requests.get(url, params=params, timeout=90)
    if not resp.ok:
        logging.error(f"Pollinations API error (status {resp.status_code}): {resp.text[:500]}")
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "")
    if "image" not in content_type or len(resp.content) < 1000:
        raise HTTPException(status_code=502, detail="Pollinations did not return a valid image")
    return resp.content

async def _generate_art_with_google_key(api_key: str, prompt: str) -> bytes:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload, timeout=60)
    if not resp.ok:
        logging.error(f"Gemini API error (status {resp.status_code}): {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    parts = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            return base64.b64decode(inline["data"])
    raise HTTPException(status_code=502, detail="No image returned from the art generator")

@api_router.post("/horoscope/art")
async def generate_horoscope_art(input: ArtRequest):
    cache_key = hashlib.sha256(f"{date.today().isoformat()}|{input.sign}|{input.prompt}".encode()).hexdigest()[:20]
    file_path = ART_DIR / f"{cache_key}.png"
    if file_path.exists():
        return {"image_url": f"/api/horoscope/art/{cache_key}.png", "cached": True}

    full_prompt = (
        f"{input.prompt} Cinematic 3D render, hyper-detailed, premium futuristic astrology aesthetic, "
        "deep space dark background, no text, no watermark, no logos, no UI elements, no people faces, "
        "centered composition, elegant cosmic glow."
    )
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    image_bytes = None
    try:
        image_bytes = await _generate_art_with_pollinations(full_prompt)
    except Exception:
        logging.exception("Pollinations generation failed, trying fallback")
        try:
            if google_key:
                image_bytes = await _generate_art_with_google_key(google_key, full_prompt)
        except HTTPException:
            raise
        except Exception:
            logging.exception("Horoscope art generation failed")

    if not image_bytes:
        raise HTTPException(status_code=502, detail="Could not generate cosmic art right now")

    file_path.write_bytes(image_bytes)
    return {"image_url": f"/api/horoscope/art/{cache_key}.png", "cached": False}

@api_router.get("/horoscope/art/{filename}")
async def get_horoscope_art(filename: str):
    file_path = ART_DIR / filename
    if not file_path.exists() or not filename.endswith(".png"):
        raise HTTPException(status_code=404, detail="Art not found")
    return Response(content=file_path.read_bytes(), media_type="image/png")


@api_router.get("/sessions", response_model=List[LiveSession])
async def get_sessions():
    return SESSIONS

@api_router.get("/astrologers", response_model=List[Astrologer])
async def get_astrologers():
    return ASTROLOGERS

@api_router.post("/saved-readings", response_model=SavedReading)
async def save_reading(input: SavedReadingCreate):
    reading = SavedReading(id=str(uuid.uuid4()), created_at=datetime.now(timezone.utc), **input.model_dump())
    doc = reading.model_dump()
    doc["created_at"] = reading.created_at.isoformat()
    await db.saved_readings.insert_one(doc)
    return reading

@api_router.get("/saved-readings", response_model=List[SavedReading])
async def get_saved_readings():
    readings = await db.saved_readings.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for reading in readings:
        if isinstance(reading.get("created_at"), str):
            reading["created_at"] = datetime.fromisoformat(reading["created_at"])
    return readings

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
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