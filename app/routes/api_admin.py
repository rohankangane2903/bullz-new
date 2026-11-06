import re
from fastapi import APIRouter, HTTPException
from app.models import AdminCreateClient, ClientUpdate, InvestmentCreate
from app.services.auth_service import (
    get_all_clients,
    find_user_by_id,
    find_user_by_email,
    create_user,
    update_user,
    delete_user,
    hash_password
)
from app.services.ledger_service import (
    get_ledger_summary,
    add_ledger_entry,
    normalize_date
)
from app.services.investment_service import (
    get_all_investments,
    create_investment
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/clients")
def list_clients():
    users = get_all_clients()
    all_invs = get_all_investments()

    clients_data = []
    for u in users:
        u_id = str(u.get("_id", ""))
        u_email = str(u.get("email", "")).lower()
        
        user_invs = [
            i for i in all_invs
            if str(i.get("userId", "")) == u_id or str(i.get("userEmail", "")).lower() == u_email
        ]
        ledger_sum = get_ledger_summary(u_email)
        inv_total = sum(float(i.get("amount", 0)) for i in user_invs)
        total_amount = max(float(u.get("totalAmount", 0)), float(ledger_sum.get("currentBalance", 0)), inv_total)
        
        # Monthly payout calculation
        # Extract numeric rate from strings like "10% monthly", "10.0%", "10% monthly", etc.
        rate_raw = str(ledger_sum.get("latestRate", "10")) if ledger_sum.get("latestRate") else "10"
        rate_match = re.search(r"[\d.]+", rate_raw)
        rate_num = float(rate_match.group()) if rate_match else 10.0
        running_invs = [i for i in user_invs if i.get("status") == "Running"]
        monthly_payout = sum(float(i.get("monthlyProfit", 0)) for i in running_invs) or round(total_amount * (rate_num / 100.0))

        clients_data.append({
            "id": u_id,
            "_id": u_id,
            "name": u.get("name", "Investor"),
            "email": u.get("email"),
            "phone": u.get("phone", ""),
            "role": u.get("role", "user"),
            "notes": u.get("notes", ""),
            "term": u.get("term", "Compound Monthly"),
            "tenure": u.get("tenure", "Monthly Ledger"),
            "rate": ledger_sum.get("latestRate") or u.get("rate") or "10% monthly",
            "startDate": u.get("startDate") or u.get("createdAt"),
            "totalInvestments": max(len(user_invs), ledger_sum.get("entryCount", 0), int(u.get("totalInvestments", 0))),
            "totalAmount": total_amount,
            "monthlyPayout": monthly_payout,
            "investments": user_invs,
            "ledgerSummary": ledger_sum
        })

    return clients_data

@router.post("/create-client")
def create_client(req: AdminCreateClient):
    clean_email = req.email.lower().strip()
    if find_user_by_email(clean_email):
        raise HTTPException(status_code=400, detail="User with this email already exists")

    entry_date, sort_key = normalize_date(req.startDate)
    hashed_pw = hash_password(req.password or "1234")

    user = create_user({
        "name": req.name.strip(),
        "email": clean_email,
        "password": hashed_pw,
        "phone": req.phone or "",
        "notes": req.notes or "",
        "startDate": sort_key,
        "rate": f"{req.initialRate}% monthly",
        "term": "Compound Monthly",
        "tenure": "Monthly Ledger",
        "role": "user",
        "totalInvestments": 1 if (req.initialAmount and req.initialAmount > 0) else 0,
        "totalAmount": req.initialAmount or 0.0
    })

    if req.initialAmount and req.initialAmount > 0:
        add_ledger_entry({
            "userEmail": clean_email,
            "entryDate": entry_date,
            "investmentAdded": req.initialAmount,
            "rate": req.initialRate,
            "note": f"Initial deposit: {req.notes}" if req.notes else "Initial deposit upon onboarding"
        })

        create_investment({
            "userId": user["_id"],
            "userEmail": clean_email,
            "userName": req.name.strip(),
            "amount": req.initialAmount,
            "tenure": "Monthly Ledger",
            "term": "Compound Monthly",
            "ratePercent": req.initialRate,
            "startDate": sort_key
        })

    create_notification({
        "type": "USER_SIGNUP",
        "title": "👤 Client Created by Admin",
        "message": f"Admin added client {req.name} ({clean_email}) starting {entry_date}",
        "userName": req.name,
        "userEmail": clean_email
    })

    return {
        "success": True,
        "message": "Client created successfully with initial ledger",
        "user": user
    }

@router.put("/clients/{client_id}")
def update_client_profile(client_id: str, req: ClientUpdate):
    user = find_user_by_id(client_id)
    if not user:
        raise HTTPException(status_code=404, detail="Client not found")

    updates = {}
    if req.name:
        updates["name"] = req.name.strip()
    if req.phone is not None:
        updates["phone"] = req.phone.strip()
    if req.notes is not None:
        updates["notes"] = req.notes.strip()
    if req.startDate:
        updates["startDate"] = req.startDate.strip()

    updated = update_user(client_id, updates)
    return {"success": True, "user": updated}

@router.delete("/clients/{client_id}")
def remove_client(client_id: str):
    ok = delete_user(client_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"success": True, "message": "Client deleted"}
