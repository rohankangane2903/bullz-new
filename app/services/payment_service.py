import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.config import RAZORPAY_KEY_ID
from app.database import db_manager
from app.services.auth_service import find_user_by_email
from app.services.investment_service import create_investment
from app.services.ledger_service import add_ledger_entry
from app.services.notification_service import create_notification

def create_payment_order(data: Dict[str, Any]) -> Dict[str, Any]:
    amount = float(data.get("amount", 0))
    user_email = str(data.get("userEmail", "")).lower().strip()
    user_name = data.get("userName") or "Investor"
    plan_details = data.get("planDetails") or {}

    order_id = f"ORD_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:4]}"
    pay_doc = {
        "_id": f"pay_{uuid.uuid4().hex[:12]}",
        "orderId": order_id,
        "userId": data.get("userId"),
        "userEmail": user_email,
        "userName": user_name,
        "amount": amount,
        "currency": "INR",
        "status": "created",
        "planDetails": plan_details,
        "createdAt": datetime.utcnow().isoformat()
    }

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.payments.insert_one(dict(pay_doc))
        except Exception:
            pass

    db_manager.mem_store["payments"].insert(0, pay_doc)
    db_manager.save_disk_store()

    return {
        "success": True,
        "orderId": order_id,
        "amount": amount,
        "currency": "INR",
        "keyId": RAZORPAY_KEY_ID or "rzp_test_bullz_mock",
        "isLiveConfigured": bool(RAZORPAY_KEY_ID)
    }

def complete_payment(order_id: str, payment_id: Optional[str], method: str, user_email: str, plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    clean_email = str(user_email or "").lower().strip()
    actual_payment_id = payment_id or f"PAY_{int(datetime.utcnow().timestamp())}"

    # Find the created order
    pay_order = next((p for p in db_manager.mem_store["payments"] if p.get("orderId") == order_id), None)
    if pay_order:
        pay_order["status"] = "success"
        pay_order["paymentId"] = actual_payment_id
        pay_order["method"] = method or "UPI"
        pay_order["completedAt"] = datetime.utcnow().isoformat()
        db_manager.save_disk_store()

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.payments.update_one(
                {"orderId": order_id},
                {"$set": {
                    "status": "success",
                    "paymentId": actual_payment_id,
                    "method": method or "UPI",
                    "completedAt": datetime.utcnow().isoformat()
                }}
            )
        except Exception:
            pass

    amount = float(plan.get("amount") or (pay_order.get("amount") if pay_order else 500))
    if amount < 500:
        amount = 500.0
    rate_percent = float(plan.get("ratePercent", 5.0) or 5.0)
    tenure = plan.get("tenure", "4 Month")

    user = find_user_by_email(clean_email)
    user_name = user.get("name") if user else clean_email

    # Automatically create investment
    inv = create_investment({
        "userId": user.get("_id") if user else None,
        "userEmail": clean_email,
        "userName": user_name,
        "amount": amount,
        "tenure": tenure,
        "term": plan.get("term"),
        "ratePercent": rate_percent,
        "paymentId": actual_payment_id
    })

    # Automatically add to monthly compound ledger
    today_norm = datetime.utcnow().strftime("%d-%m-%Y")
    add_ledger_entry({
        "userEmail": clean_email,
        "entryDate": today_norm,
        "investmentAdded": amount,
        "rate": rate_percent,
        "note": f"Online Payment: {actual_payment_id} ({method} - {tenure})"
    })

    create_notification({
        "type": "PAYMENT_RECEIVED",
        "title": "💳 Payment Received & Investment Activated!",
        "message": f"Received ₹{amount:,.0f} via {method} from {user_name}. Ref: {actual_payment_id}",
        "userName": user_name,
        "userEmail": clean_email,
        "amount": amount,
        "rate": f"{rate_percent}% monthly"
    })

    return {
        "success": True,
        "message": "Payment verified and investment activated!",
        "transactionId": actual_payment_id,
        "investment": inv
    }
