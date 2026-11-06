import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.database import db_manager
from app.services.notification_service import create_notification

def tenure_to_months(tenure_str: str) -> int:
    if not tenure_str:
        return 4
    m = re.search(r"(\d+)", str(tenure_str))
    num = int(m.group(1)) if m else 4
    if re.search(r"year", str(tenure_str), re.IGNORECASE):
        return num * 12
    return num

def create_investment(data: Dict[str, Any]) -> Dict[str, Any]:
    clean_email = str(data.get("userEmail", "")).lower().strip()
    user = next((u for u in db_manager.mem_store["users"] if u.get("email", "").lower() == clean_email), None)
    user_name = data.get("userName") or (user.get("name") if user else "Investor")
    user_id = data.get("userId") or (user.get("_id") if user else None)

    tenure = str(data.get("tenure", "4 Month"))
    months = tenure_to_months(tenure)
    amount = float(data.get("amount", 0.0))
    rate_percent = float(data.get("ratePercent", 5.0) or 5.0)
    
    monthly_profit = round((amount * rate_percent) / 100.0)
    total_profit = round(monthly_profit * months)
    total_maturity = round(amount + total_profit)

    today = datetime.utcnow()
    start_date_str = data.get("startDate") or today.strftime("%Y-%m-%d")
    
    mat_date = today + timedelta(days=months * 30)
    maturity_date_str = data.get("maturityDate") or mat_date.strftime("%Y-%m-%d")

    inv_id = f"inv_{uuid.uuid4().hex[:12]}"
    inv_doc = {
        "_id": inv_id,
        "userId": user_id,
        "userEmail": clean_email,
        "userName": user_name,
        "amount": amount,
        "originalPrincipal": amount,
        "term": data.get("term") or ("Long Term" if months >= 12 else "Short Term"),
        "tenure": tenure,
        "tenureMonths": months,
        "ratePercent": rate_percent,
        "rateLabel": f"{rate_percent}% monthly",
        "monthlyProfit": monthly_profit,
        "totalProfit": total_profit,
        "totalMaturityAmount": total_maturity,
        "startDate": start_date_str,
        "maturityDate": maturity_date_str,
        "status": "Running",
        "paymentId": data.get("paymentId") or f"PAY_{int(datetime.utcnow().timestamp())}",
        "paymentStatus": "completed",
        "rolloverCount": 0,
        "history": [],
        "createdAt": datetime.utcnow().isoformat()
    }

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.investments.insert_one(dict(inv_doc))
        except Exception:
            pass

    db_manager.mem_store["investments"].insert(0, inv_doc)
    
    # Update user summary
    user_invs = [i for i in db_manager.mem_store["investments"] if i.get("userEmail", "").lower() == clean_email]
    tot_amt = sum(float(i.get("amount", 0)) for i in user_invs)
    
    if user:
        user["totalInvestments"] = max(user.get("totalInvestments", 0), len(user_invs))
        user["totalAmount"] = max(float(user.get("totalAmount", 0)), tot_amt)

    db_manager.save_disk_store()

    create_notification({
        "type": "NEW_INVESTMENT",
        "title": "💰 New Investment Created!",
        "message": f"{user_name} invested ₹{amount:,.0f} at {rate_percent}% ({tenure})",
        "userName": user_name,
        "userEmail": clean_email,
        "amount": amount,
        "rate": f"{rate_percent}% monthly"
    })

    return inv_doc

def get_user_investments(user_id_or_email: str) -> List[Dict[str, Any]]:
    clean = str(user_id_or_email or "").lower().strip()
    results = []
    
    if db_manager.is_connected and db_manager.db is not None:
        try:
            docs = list(db_manager.db.investments.find({
                "$or": [{"userEmail": clean}, {"userId": clean}]
            }).sort("createdAt", -1))
            for d in docs:
                d["_id"] = str(d["_id"])
            if docs:
                results = docs
        except Exception:
            pass

    if not results:
        results = [
            dict(i) for i in db_manager.mem_store["investments"]
            if i.get("userEmail", "").lower() == clean or str(i.get("userId", "")) == clean
        ]

    # Synthesize from Monthly Ledger if no classic investment objects exist
    if not results:
        user_ledgers = [l for l in db_manager.mem_store["monthly_ledgers"] if l.get("userEmail", "").lower() == clean and float(l.get("investmentAdded", 0) or 0) > 0]
        for l in user_ledgers:
            inv_amt = float(l.get("investmentAdded", 0))
            r = float(l.get("rate", 10.0))
            results.append({
                "_id": l.get("_id"),
                "userId": l.get("userId"),
                "userEmail": l.get("userEmail"),
                "userName": l.get("userName"),
                "amount": inv_amt,
                "tenure": "Monthly Ledger",
                "term": "Compound Monthly",
                "ratePercent": r,
                "rateLabel": f"{r}% monthly",
                "status": "Running",
                "startDate": l.get("entryDate") or l.get("sortKey"),
                "maturityDate": "Open Ended",
                "totalProfit": float(l.get("interest", 0)),
                "earning": str(l.get("interest", 0)),
                "createdAt": l.get("createdAt")
            })

    return results

def get_all_investments() -> List[Dict[str, Any]]:
    if db_manager.is_connected and db_manager.db is not None:
        try:
            docs = list(db_manager.db.investments.find().sort("createdAt", -1))
            for d in docs:
                d["_id"] = str(d["_id"])
            if docs:
                return docs
        except Exception:
            pass
    return sorted(db_manager.mem_store["investments"], key=lambda x: x.get("createdAt", ""), reverse=True)

def update_investment_rate_and_rollover(
    investment_id: str,
    new_rate_percent: float,
    additional_months: int = 4,
    rollover_profit: bool = False,
    note: str = ""
) -> Optional[Dict[str, Any]]:
    inv = next((i for i in db_manager.mem_store["investments"] if str(i.get("_id")) == str(investment_id)), None)
    if not inv:
        return None

    old_amount = float(inv.get("amount", 0))
    old_rate = float(inv.get("ratePercent", 5))
    old_tenure = inv.get("tenure", "4 Month")

    accrued_profit = float(inv.get("totalProfit", 0)) or round((old_amount * old_rate * inv.get("tenureMonths", 4)) / 100.0)
    new_amount = old_amount + accrued_profit if rollover_profit else old_amount
    rate = float(new_rate_percent) if new_rate_percent is not None else old_rate
    ext_months = int(additional_months or 4)

    new_tenure = f"{ext_months // 12} year" if ext_months >= 12 else f"{ext_months} Month"
    new_monthly_profit = round((new_amount * rate) / 100.0)
    new_total_profit = round(new_monthly_profit * ext_months)
    new_total_maturity = round(new_amount + new_total_profit)

    mat_date = datetime.utcnow() + timedelta(days=ext_months * 30)

    history_entry = {
        "updatedAt": datetime.utcnow().isoformat(),
        "updatedBy": "admin",
        "previousAmount": old_amount,
        "newAmount": new_amount,
        "previousRatePercent": old_rate,
        "newRatePercent": rate,
        "previousTenure": old_tenure,
        "newTenure": new_tenure,
        "accruedProfitAdded": accrued_profit if rollover_profit else 0,
        "note": note or (
            f"Rolled over with balance of ₹{new_amount:,.0f} updated to {rate}%"
            if rollover_profit
            else f"Updated rate to {rate}% and extended by {ext_months} months"
        )
    }

    inv["amount"] = new_amount
    inv["ratePercent"] = rate
    inv["rateLabel"] = f"{rate}% monthly"
    inv["tenure"] = new_tenure
    inv["tenureMonths"] = ext_months
    inv["term"] = "Long Term" if ext_months >= 12 else "Short Term"
    inv["monthlyProfit"] = new_monthly_profit
    inv["totalProfit"] = new_total_profit
    inv["totalMaturityAmount"] = new_total_maturity
    inv["maturityDate"] = mat_date.strftime("%Y-%m-%d")
    inv["status"] = "Running"
    inv["rolloverCount"] = inv.get("rolloverCount", 0) + 1
    inv.setdefault("history", []).append(history_entry)

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.investments.replace_one({"_id": inv["_id"]}, inv)
        except Exception:
            pass

    db_manager.save_disk_store()

    create_notification({
        "type": "INVESTMENT_UPDATED",
        "title": "📈 Investment Rate & Balance Updated!",
        "message": f"{inv.get('userName')}'s investment updated to {rate}% on balance ₹{new_amount:,.0f} ({new_tenure})",
        "userName": inv.get("userName"),
        "userEmail": inv.get("userEmail"),
        "amount": new_amount,
        "rate": f"{rate}% monthly"
    })

    return inv

def toggle_investment_status(investment_id: str) -> Optional[Dict[str, Any]]:
    inv = next((i for i in db_manager.mem_store["investments"] if str(i.get("_id")) == str(investment_id)), None)
    if not inv:
        return None
    inv["status"] = "Completed" if inv.get("status") == "Running" else "Running"
    
    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.investments.update_one({"_id": inv["_id"]}, {"$set": {"status": inv["status"]}})
        except Exception:
            pass
    db_manager.save_disk_store()
    return inv

def delete_investment(investment_id: str) -> bool:
    found = False
    clean_list = []
    user_email = ""
    for item in db_manager.mem_store["investments"]:
        if str(item.get("_id")) == str(investment_id):
            user_email = item.get("userEmail", "")
            found = True
        else:
            clean_list.append(item)

    if found:
        db_manager.mem_store["investments"] = clean_list
        db_manager.save_disk_store()

        if db_manager.is_connected and db_manager.db is not None:
            try:
                db_manager.db.investments.delete_one({"_id": investment_id})
            except Exception:
                pass
        return True
    return False
