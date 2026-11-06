import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import bcrypt
import jwt
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from app.database import db_manager

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_or_plain: str) -> bool:
    if not hashed_or_plain:
        return False
    if hashed_or_plain.startswith("$2"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_or_plain.encode("utf-8"))
        except Exception:
            return False
    return plain_password == hashed_or_plain

def create_jwt_token(payload: Dict[str, Any]) -> str:
    data = payload.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    data.update({"exp": expire})
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    clean = str(email or "").lower().strip()
    if db_manager.is_connected and db_manager.db is not None:
        try:
            u = db_manager.db.users.find_one({"email": clean})
            if u:
                u["_id"] = str(u["_id"])
                return u
        except Exception:
            pass
    for u in db_manager.mem_store["users"]:
        if u.get("email", "").lower() == clean:
            return dict(u)
    return None

def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    uid = str(user_id)
    if db_manager.is_connected and db_manager.db is not None:
        try:
            from bson import ObjectId
            q = {"$or": [{"_id": uid}]}
            if len(uid) == 24:
                try:
                    q["$or"].append({"_id": ObjectId(uid)})
                except Exception:
                    pass
            u = db_manager.db.users.find_one(q)
            if u:
                u["_id"] = str(u["_id"])
                return u
        except Exception:
            pass
    for u in db_manager.mem_store["users"]:
        if str(u.get("_id", "")) == uid or str(u.get("id", "")) == uid:
            return dict(u)
    return None

def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    clean_email = str(data.get("email", "")).lower().strip()
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "_id": user_id,
        "name": data.get("name", "").strip(),
        "email": clean_email,
        "password": data.get("password"),
        "phone": data.get("phone", "").strip(),
        "role": data.get("role", "user"),
        "totalInvestments": data.get("totalInvestments", 0),
        "totalAmount": data.get("totalAmount", 0),
        "term": data.get("term", "Compound Monthly"),
        "tenure": data.get("tenure", "Monthly Ledger"),
        "rate": data.get("rate", "10% monthly"),
        "startDate": data.get("startDate", datetime.utcnow().strftime("%Y-%m-%d")),
        "notes": data.get("notes", ""),
        "createdAt": datetime.utcnow().isoformat(),
        "lastLogin": datetime.utcnow().isoformat()
    }

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.users.replace_one({"email": clean_email}, user_doc, upsert=True)
        except Exception:
            pass

    # Update in memory & save to disk
    idx = next((i for i, u in enumerate(db_manager.mem_store["users"]) if u.get("email", "").lower() == clean_email), -1)
    if idx >= 0:
        db_manager.mem_store["users"][idx] = user_doc
    else:
        db_manager.mem_store["users"].append(user_doc)
    db_manager.save_disk_store()
    return user_doc

def update_user(user_id_or_email: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    clean = str(user_id_or_email).lower().strip()
    user = find_user_by_email(clean) or find_user_by_id(user_id_or_email)
    if not user:
        return None

    email = user["email"].lower()
    uid = user["_id"]

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.users.update_one({"email": email}, {"$set": update_fields})
        except Exception:
            pass

    for u in db_manager.mem_store["users"]:
        if u.get("email", "").lower() == email or str(u.get("_id", "")) == str(uid):
            u.update(update_fields)
            user = dict(u)
            break
    db_manager.save_disk_store()
    return user

def get_all_clients() -> List[Dict[str, Any]]:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            users = list(db_manager.db.users.find({"role": {"$ne": "admin"}}).sort("createdAt", -1))
            for u in users:
                u["_id"] = str(u["_id"])
            if users:
                return users
        except Exception:
            pass
    return [dict(u) for u in db_manager.mem_store["users"] if u.get("role") != "admin"]

def delete_user(user_id: str) -> bool:
    user = find_user_by_id(user_id)
    if not user:
        return False
    email = user["email"].lower()

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.users.delete_one({"email": email})
            db_manager.db.investments.delete_many({"userEmail": email})
            db_manager.db.monthly_ledgers.delete_many({"userEmail": email})
        except Exception:
            pass

    db_manager.mem_store["users"] = [u for u in db_manager.mem_store["users"] if u.get("email", "").lower() != email and str(u.get("_id")) != user_id]
    db_manager.mem_store["investments"] = [i for i in db_manager.mem_store["investments"] if i.get("userEmail", "").lower() != email]
    db_manager.mem_store["monthly_ledgers"] = [l for l in db_manager.mem_store["monthly_ledgers"] if l.get("userEmail", "").lower() != email]
    db_manager.save_disk_store()
    return True
