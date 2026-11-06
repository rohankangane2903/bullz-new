import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.database import db_manager

def create_notification(notif_data: Dict[str, Any]) -> Dict[str, Any]:
    new_notif = {
        "_id": f"notif_{uuid.uuid4().hex[:12]}",
        "type": notif_data.get("type", "GENERAL"),
        "title": notif_data.get("title", "Notification"),
        "message": notif_data.get("message", ""),
        "userName": notif_data.get("userName", "User"),
        "userEmail": notif_data.get("userEmail", ""),
        "amount": notif_data.get("amount"),
        "rate": notif_data.get("rate"),
        "isRead": False,
        "createdAt": datetime.utcnow().isoformat()
    }

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.notifications.insert_one(dict(new_notif))
        except Exception:
            pass

    db_manager.mem_store["notifications"].insert(0, new_notif)
    if len(db_manager.mem_store["notifications"]) > 100:
        db_manager.mem_store["notifications"].pop()
    db_manager.save_disk_store()
    return new_notif

def get_notifications(limit: int = 50) -> Dict[str, Any]:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            docs = list(db_manager.db.notifications.find().sort("createdAt", -1).limit(limit))
            for d in docs:
                d["_id"] = str(d["_id"])
            unread = db_manager.db.notifications.count_documents({"isRead": False})
            if docs:
                return {"list": docs, "unreadCount": unread}
        except Exception:
            pass

    notifs = db_manager.mem_store["notifications"][:limit]
    unread = sum(1 for n in db_manager.mem_store["notifications"] if not n.get("isRead"))
    return {"list": notifs, "unreadCount": unread}

def mark_notification_read(notif_id: str) -> bool:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.notifications.update_one({"_id": notif_id}, {"$set": {"isRead": True}})
        except Exception:
            pass

    for n in db_manager.mem_store["notifications"]:
        if str(n.get("_id")) == str(notif_id):
            n["isRead"] = True
            break
    db_manager.save_disk_store()
    return True

def mark_all_notifications_read() -> bool:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.notifications.update_many({"isRead": False}, {"$set": {"isRead": True}})
        except Exception:
            pass

    for n in db_manager.mem_store["notifications"]:
        n["isRead"] = True
    db_manager.save_disk_store()
    return True

def clear_all_notifications() -> bool:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.notifications.delete_many({})
        except Exception:
            pass

    db_manager.mem_store["notifications"] = []
    db_manager.save_disk_store()
    return True
