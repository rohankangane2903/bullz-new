import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of bullz new
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Detect Vercel serverless environment
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0" if IS_VERCEL else "127.0.0.1")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# MongoDB Settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/bullz")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "bullz")

# Admin Settings
ADMIN_NAME = os.getenv("ADMIN_NAME", "ADMIN")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@gmail.com").lower().strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Security
JWT_SECRET = os.getenv("JWT_SECRET", "bullz_super_secret_jwt_key_2026_python_mongodb")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 72))

# Razorpay / Payment
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Data Directory for disk persistence & fallback
# On Vercel, only /tmp is writable; locally use project-level data/
if IS_VERCEL:
    DATA_DIR = Path("/tmp/bullz_data")
else:
    DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "bullz_store.json"
