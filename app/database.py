import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import pymongo
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import bcrypt

from app.config import (
    MONGODB_URI,
    MONGODB_DB_NAME,
    ADMIN_NAME,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DATA_FILE,
)

logger = logging.getLogger("bullz.database")
logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    def __init__(self):
        self.client: Optional[pymongo.MongoClient] = None
        self.db = None
        self.is_connected = False
        
        # In-memory and local disk store for zero-downtime fallback
        self.mem_store: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "investments": [],
            "monthly_ledgers": [],
            "notifications": [
                {
                    "_id": "notif_sys_1",
                    "type": "USER_LOGIN",
                    "title": "System Active",
                    "message": "Bullz Python Application started with MongoDB support.",
                    "userName": "System",
                    "isRead": False,
                    "createdAt": datetime.utcnow().isoformat(),
                }
            ],
            "payments": []
        }
        
        self.load_disk_store()
        self.ensure_default_admin()
        self.connect()

    def load_disk_store(self):
        try:
            if DATA_FILE.exists():
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key in ["users", "investments", "monthly_ledgers", "notifications", "payments"]:
                        if key in data and isinstance(data[key], list):
                            self.mem_store[key] = data[key]
                logger.info(f"Loaded disk store: {len(self.mem_store['users'])} users, {len(self.mem_store['monthly_ledgers'])} ledger rows.")
        except Exception as e:
            logger.warning(f"Could not load disk fallback store: {e}")

    def save_disk_store(self):
        try:
            DATA_FILE.parent.mkdir(exist_ok=True, parents=True)
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.mem_store, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save to disk fallback store: {e}")

    def ensure_default_admin(self):
        admin_email = ADMIN_EMAIL.lower().strip()
        admin_exists = any(u.get("email", "").lower() == admin_email for u in self.mem_store["users"])
        if not admin_exists:
            hashed_pw = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin_user = {
                "_id": "user_admin_01",
                "name": ADMIN_NAME,
                "email": admin_email,
                "password": hashed_pw,
                "phone": "+91 8108000167",
                "role": "admin",
                "totalInvestments": 0,
                "totalAmount": 0,
                "term": "Long Term",
                "tenure": "1 year",
                "rate": "10% monthly",
                "startDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "notes": "Head Administrator",
                "createdAt": datetime.utcnow().isoformat(),
                "lastLogin": datetime.utcnow().isoformat(),
            }
            self.mem_store["users"].insert(0, admin_user)
            self.save_disk_store()

    def connect(self) -> bool:
        try:
            self.client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.client.server_info() # verify connection
            self.db = self.client[MONGODB_DB_NAME]
            self.is_connected = True
            logger.info("MongoDB successfully connected to: " + MONGODB_URI)
            self.sync_seed_to_mongodb()
            return True
        except (ServerSelectionTimeoutError, PyMongoError, Exception) as e:
            self.is_connected = False
            logger.info(f"MongoDB not connected yet ({e}). Seamless local persistent store is active.")
            return False

    def sync_seed_to_mongodb(self):
        if not self.is_connected or self.db is None:
            return
        try:
            # Create indexes
            self.db.users.create_index("email", unique=True)
            self.db.monthly_ledgers.create_index([("userEmail", 1), ("sortKey", 1)])
            self.db.investments.create_index("userEmail")
            self.db.notifications.create_index("createdAt")

            # Check if users collection is empty
            if self.db.users.count_documents({}) == 0:
                logger.info("Syncing local store seed into MongoDB collections...")
                for user in self.mem_store["users"]:
                    doc = dict(user)
                    self.db.users.replace_one({"email": doc["email"]}, doc, upsert=True)
                for led in self.mem_store["monthly_ledgers"]:
                    doc = dict(led)
                    self.db.monthly_ledgers.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                for inv in self.mem_store["investments"]:
                    doc = dict(inv)
                    self.db.investments.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                for notif in self.mem_store["notifications"]:
                    doc = dict(notif)
                    self.db.notifications.replace_one({"_id": doc["_id"]}, doc, upsert=True)
                logger.info("MongoDB seed synchronization complete!")
        except Exception as e:
            logger.warning(f"MongoDB sync notice: {e}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "online",
            "mongodb_connected": self.is_connected,
            "database_name": MONGODB_DB_NAME if self.is_connected else "Local Persistent Store (MongoDB Ready)",
            "mongo_uri": MONGODB_URI,
            "timestamp": datetime.utcnow().isoformat()
        }

db_manager = DatabaseManager()
