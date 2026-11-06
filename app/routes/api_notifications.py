from fastapi import APIRouter
from app.services.notification_service import (
    get_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    clear_all_notifications
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("")
def list_notifications(limit: int = 50):
    return get_notifications(limit)

@router.put("/{notif_id}/read")
def read_notif(notif_id: str):
    mark_notification_read(notif_id)
    return {"success": True}

@router.put("/read-all")
def read_all():
    mark_all_notifications_read()
    return {"success": True, "message": "All notifications marked as read"}

@router.delete("")
def clear_all():
    clear_all_notifications()
    return {"success": True, "message": "Notifications cleared"}
