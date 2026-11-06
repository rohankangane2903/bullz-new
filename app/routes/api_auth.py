from fastapi import APIRouter, HTTPException, Query
from app.models import UserRegister, UserLogin, ProfileUpdate
from app.services.auth_service import (
    find_user_by_email,
    create_user,
    update_user,
    verify_password,
    hash_password,
    create_jwt_token
)
from app.services.ledger_service import get_ledger_summary
from app.services.investment_service import get_user_investments
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
def register(req: UserRegister):
    if not req.name or not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required")
    
    clean_email = req.email.lower().strip()
    existing = find_user_by_email(clean_email)
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    hashed_pw = hash_password(req.password)
    user = create_user({
        "name": req.name.strip(),
        "email": clean_email,
        "password": hashed_pw,
        "phone": req.phone or "",
        "role": "user"
    })

    create_notification({
        "type": "USER_SIGNUP",
        "title": "👤 New User Registered",
        "message": f"{req.name} ({clean_email}) has just joined Bullz! Phone: {req.phone or 'Not provided'}",
        "userName": req.name,
        "userEmail": clean_email
    })

    token = create_jwt_token({
        "userId": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"]
    })

    return {
        "success": True,
        "message": "Account created successfully",
        "token": token,
        "user": {
            "id": user["_id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user.get("phone", ""),
            "role": user["role"],
            "totalInvestments": 0,
            "totalAmount": 0
        }
    }

@router.post("/login")
def login(req: UserLogin):
    clean_email = req.email.lower().strip()
    user = find_user_by_email(clean_email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials. User not found.")

    # Strict role check separating User login and Admin login
    if req.role == "admin" and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Admin credentials required.")
    if req.role == "user" and user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="This is the User Login portal. Administrator account detected. Please use the dedicated Admin Portal to sign in.")

    # Compare password
    pw_match = verify_password(req.password, user.get("password", ""))
    if not pw_match:
        raise HTTPException(status_code=401, detail="Invalid password.")

    # Upgrade to bcrypt hash if plaintext was stored
    if not user.get("password", "").startswith("$2"):
        new_hashed = hash_password(req.password)
        update_user(user["_id"], {"password": new_hashed})

    # Update last login
    from datetime import datetime
    update_user(user["_id"], {"lastLogin": datetime.utcnow().isoformat()})

    if user.get("role") != "admin":
        create_notification({
            "type": "USER_LOGIN",
            "title": "🔑 User Logged In",
            "message": f"{user['name']} ({user['email']}) just logged in",
            "userName": user["name"],
            "userEmail": user["email"]
        })

    ledger_summary = get_ledger_summary(user["email"])
    investments = get_user_investments(user["email"])
    inv_total = sum(float(i.get("amount", 0)) for i in investments)
    total_amount = max(float(user.get("totalAmount", 0)), float(ledger_summary.get("currentBalance", 0)), inv_total)
    total_investments = max(len(investments), ledger_summary.get("entryCount", 0), int(user.get("totalInvestments", 0)))

    token = create_jwt_token({
        "userId": user["_id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"]
    })

    return {
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["_id"],
            "name": user["name"],
            "email": user["email"],
            "phone": user.get("phone", ""),
            "role": user["role"],
            "totalInvestments": total_investments,
            "totalAmount": total_amount,
            "rate": ledger_summary.get("latestRate") or user.get("rate") or "10% monthly",
            "term": user.get("term", "Compound Monthly"),
            "tenure": user.get("tenure", "Monthly Ledger"),
            "startDate": user.get("startDate", ""),
            "notes": user.get("notes", ""),
            "ledgerSummary": ledger_summary,
            "investments": investments
        }
    }

@router.get("/me")
def me(email: str = Query(...)):
    clean_email = email.lower().strip()
    user = find_user_by_email(clean_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ledger_summary = get_ledger_summary(user["email"])
    investments = get_user_investments(user["email"])
    inv_total = sum(float(i.get("amount", 0)) for i in investments)
    total_amount = max(float(user.get("totalAmount", 0)), float(ledger_summary.get("currentBalance", 0)), inv_total)
    total_investments = max(len(investments), ledger_summary.get("entryCount", 0), int(user.get("totalInvestments", 0)))

    return {
        "id": user["_id"],
        "name": user["name"],
        "email": user["email"],
        "phone": user.get("phone", ""),
        "role": user["role"],
        "totalInvestments": total_investments,
        "totalAmount": total_amount,
        "rate": ledger_summary.get("latestRate") or user.get("rate") or "10% monthly",
        "term": user.get("term", "Compound Monthly"),
        "tenure": user.get("tenure", "Monthly Ledger"),
        "startDate": user.get("startDate", ""),
        "notes": user.get("notes", ""),
        "ledgerSummary": ledger_summary,
        "investments": investments
    }

@router.put("/profile")
def update_profile(req: ProfileUpdate):
    clean_email = req.email.lower().strip()
    user = find_user_by_email(clean_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {}
    if req.name and req.name.strip():
        updates["name"] = req.name.strip()
    if req.phone is not None:
        updates["phone"] = req.phone.strip()
    if req.password and req.password.strip():
        updates["password"] = hash_password(req.password.strip())

    updated = update_user(clean_email, updates)
    ledger_summary = get_ledger_summary(clean_email)
    investments = get_user_investments(clean_email)

    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": {
            "id": updated["_id"],
            "name": updated["name"],
            "email": updated["email"],
            "phone": updated.get("phone", ""),
            "role": updated["role"],
            "totalInvestments": len(investments),
            "totalAmount": ledger_summary.get("currentBalance", 0),
            "ledgerSummary": ledger_summary,
            "investments": investments
        }
    }
