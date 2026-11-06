import re
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.database import db_manager
from app.services.notification_service import create_notification

def normalize_date(d_str: Optional[str] = None) -> Tuple[str, str]:
    if not d_str:
        now = datetime.utcnow()
        dd = f"{now.day:02d}"
        mm = f"{now.month:02d}"
        yyyy = f"{now.year}"
        return f"{dd}-{mm}-{yyyy}", f"{yyyy}-{mm}-{dd}"
    
    s = str(d_str).strip()
    
    # Check DD-MM-YYYY or DD/MM/YYYY
    dm = re.match(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$", s)
    if dm:
        dd = f"{int(dm.group(1)):02d}"
        mm = f"{int(dm.group(2)):02d}"
        yyyy = dm.group(3)
        return f"{dd}-{mm}-{yyyy}", f"{yyyy}-{mm}-{dd}"
        
    # Check YYYY-MM-DD
    ym = re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", s)
    if ym:
        yyyy = ym.group(1)
        mm = f"{int(ym.group(2)):02d}"
        dd = f"{int(ym.group(3)):02d}"
        return f"{dd}-{mm}-{yyyy}", f"{yyyy}-{mm}-{dd}"

    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        dd = f"{dt.day:02d}"
        mm = f"{dt.month:02d}"
        yyyy = f"{dt.year}"
        return f"{dd}-{mm}-{yyyy}", f"{yyyy}-{mm}-{dd}"
    except Exception:
        return s, s

def recalculate_ledger(user_email: str) -> List[Dict[str, Any]]:
    clean_email = str(user_email or "").lower().strip()
    
    # Find all entries for this user in mem_store
    user_entries = [l for l in db_manager.mem_store["monthly_ledgers"] if l.get("userEmail", "").lower() == clean_email]
    
    # Sort chronologically by sortKey, then createdAt
    user_entries.sort(key=lambda x: (x.get("sortKey", ""), x.get("createdAt", "")))
    
    running_prev_balance = 0.0
    for item in user_entries:
        item["previousBalance"] = running_prev_balance
        base = running_prev_balance + float(item.get("investmentAdded", 0) or 0)
        rate = float(item.get("rate", 10.0) or 10.0)
        interest = round((base * rate) / 100.0)
        total_balance = round(base + interest)
        
        item["interest"] = interest
        item["totalBalance"] = total_balance
        item["updatedAt"] = datetime.utcnow().isoformat()
        running_prev_balance = total_balance

    # Update in MongoDB if connected
    if db_manager.is_connected and db_manager.db is not None:
        try:
            for item in user_entries:
                db_manager.db.monthly_ledgers.replace_one({"_id": item["_id"]}, item, upsert=True)
        except Exception:
            pass

    # Update user's profile totalAmount and totalInvestments
    latest = user_entries[-1] if user_entries else None
    tot_amt = latest["totalBalance"] if latest else 0.0
    
    for u in db_manager.mem_store["users"]:
        if u.get("email", "").lower() == clean_email:
            u["totalAmount"] = tot_amt
            u["totalInvestments"] = len(user_entries)
            if latest and latest.get("rate"):
                u["rate"] = f"{latest['rate']}% monthly"
            break

    if db_manager.is_connected and db_manager.db is not None:
        try:
            db_manager.db.users.update_one(
                {"email": clean_email},
                {"$set": {"totalAmount": tot_amt, "totalInvestments": len(user_entries)}}
            )
        except Exception:
            pass

    db_manager.save_disk_store()
    return user_entries

def get_user_ledger(user_email: str) -> List[Dict[str, Any]]:
    clean_email = str(user_email or "").lower().strip()
    return recalculate_ledger(clean_email)

def get_ledger_summary(user_email: str) -> Dict[str, Any]:
    clean_email = str(user_email or "").lower().strip()
    entries = get_user_ledger(clean_email)
    
    total_invested = sum(float(e.get("investmentAdded", 0) or 0) for e in entries)
    total_interest = sum(float(e.get("interest", 0) or 0) for e in entries)
    latest = entries[-1] if entries else None
    
    current_balance = latest["totalBalance"] if latest else total_invested
    latest_rate = f"{latest['rate']}%" if latest else "10%"
    latest_date = latest["entryDate"] if latest else "N/A"

    if not entries:
        # Check user profile
        user = next((u for u in db_manager.mem_store["users"] if u.get("email", "").lower() == clean_email), None)
        if user:
            u_amt = float(user.get("totalAmount", 0) or 0)
            u_rate = user.get("rate", "10% monthly")
            return {
                "entryCount": 0,
                "totalInvested": u_amt,
                "totalInterest": 0,
                "currentBalance": u_amt,
                "latestDate": user.get("startDate", "N/A"),
                "latestRate": u_rate
            }

    return {
        "entryCount": len(entries),
        "totalInvested": total_invested,
        "totalInterest": total_interest,
        "currentBalance": current_balance,
        "latestDate": latest_date,
        "latestRate": latest_rate
    }

def add_ledger_entry(data: Dict[str, Any]) -> Dict[str, Any]:
    clean_email = str(data.get("userEmail", "")).lower().strip()
    user = next((u for u in db_manager.mem_store["users"] if u.get("email", "").lower() == clean_email), None)
    user_name = user.get("name", "Investor") if user else "Investor"
    user_id = user.get("_id") if user else None

    entry_date, sort_key = normalize_date(data.get("entryDate"))
    inv_added = float(data.get("investmentAdded", 0.0) or 0.0)
    rate = float(data.get("rate", 10.0) or 10.0)
    note = str(data.get("note", "") or "")

    entry_id = f"led_{uuid.uuid4().hex[:12]}"
    new_entry = {
        "_id": entry_id,
        "userId": user_id,
        "userEmail": clean_email,
        "userName": user_name,
        "entryDate": entry_date,
        "sortKey": sort_key,
        "investmentAdded": inv_added,
        "previousBalance": 0.0,
        "rate": rate,
        "interest": 0.0,
        "totalBalance": 0.0,
        "note": note,
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }

    db_manager.mem_store["monthly_ledgers"].append(new_entry)
    db_manager.save_disk_store()

    # Cascade recalculation
    recalculate_ledger(clean_email)

    create_notification({
        "type": "INVESTMENT_UPDATED",
        "title": "📊 Monthly Ledger Entry Added",
        "message": f"{user_name}: {entry_date} | Added ₹{inv_added:,.0f} @ {rate}%",
        "userName": user_name,
        "userEmail": clean_email,
        "amount": inv_added,
        "rate": f"{rate}% monthly"
    })

    return new_entry

def update_ledger_entry(entry_id: str, data: Dict[str, Any]) -> bool:
    user_email = ""
    for item in db_manager.mem_store["monthly_ledgers"]:
        if str(item.get("_id")) == str(entry_id):
            user_email = item.get("userEmail", "")
            if data.get("entryDate"):
                ed, sk = normalize_date(data["entryDate"])
                item["entryDate"] = ed
                item["sortKey"] = sk
            if data.get("investmentAdded") is not None:
                item["investmentAdded"] = float(data["investmentAdded"])
            if data.get("rate") is not None:
                item["rate"] = float(data["rate"])
            if data.get("note") is not None:
                item["note"] = str(data["note"])
            item["updatedAt"] = datetime.utcnow().isoformat()
            break

    if user_email:
        recalculate_ledger(user_email)
        return True
    return False

def delete_ledger_entry(entry_id: str) -> bool:
    user_email = ""
    found = False
    new_list = []
    for item in db_manager.mem_store["monthly_ledgers"]:
        if str(item.get("_id")) == str(entry_id):
            user_email = item.get("userEmail", "")
            found = True
        else:
            new_list.append(item)
    
    if found:
        db_manager.mem_store["monthly_ledgers"] = new_list
        db_manager.save_disk_store()

        if db_manager.is_connected and db_manager.db is not None:
            try:
                db_manager.db.monthly_ledgers.delete_one({"_id": entry_id})
            except Exception:
                pass

        if user_email:
            recalculate_ledger(user_email)
        return True
    return False
