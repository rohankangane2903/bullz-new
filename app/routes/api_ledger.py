from fastapi import APIRouter, HTTPException, Query
from app.models import LedgerEntryCreate, LedgerEntryUpdate
from app.services.ledger_service import (
    get_user_ledger,
    get_ledger_summary,
    add_ledger_entry,
    update_ledger_entry,
    delete_ledger_entry
)

router = APIRouter(prefix="/api/ledger", tags=["ledger"])

@router.get("")
def get_ledger(email: str = Query(...)):
    clean_email = email.lower().strip()
    entries = get_user_ledger(clean_email)
    summary = get_ledger_summary(clean_email)
    return {
        "success": True,
        "email": clean_email,
        "entries": entries,
        "summary": summary
    }

@router.post("")
def add_entry(req: LedgerEntryCreate):
    if not req.userEmail or req.rate is None:
        raise HTTPException(status_code=400, detail="userEmail and rate are required")

    entry = add_ledger_entry({
        "userEmail": req.userEmail,
        "entryDate": req.entryDate,
        "investmentAdded": req.investmentAdded,
        "rate": req.rate,
        "note": req.note
    })

    entries = get_user_ledger(req.userEmail)
    summary = get_ledger_summary(req.userEmail)
    return {
        "success": True,
        "entry": entry,
        "entries": entries,
        "summary": summary
    }

@router.put("/{entry_id}")
def update_entry(entry_id: str, req: LedgerEntryUpdate):
    from app.database import db_manager
    ok = update_ledger_entry(entry_id, {
        "entryDate": req.entryDate,
        "investmentAdded": req.investmentAdded,
        "rate": req.rate,
        "note": req.note
    })
    if not ok:
        raise HTTPException(status_code=404, detail="Ledger entry not found")

    email = req.userEmail
    if not email:
        entry = next((item for item in db_manager.mem_store["monthly_ledgers"] if str(item.get("_id")) == str(entry_id)), None)
        if entry:
            email = entry.get("userEmail")

    entries = get_user_ledger(email) if email else []
    summary = get_ledger_summary(email) if email else None
    return {
        "success": True,
        "message": "Ledger entry updated & recalculated",
        "entries": entries,
        "summary": summary
    }

@router.delete("/{entry_id}")
def delete_entry(entry_id: str):
    ok = delete_ledger_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Ledger entry not found")
    return {
        "success": True,
        "message": "Ledger entry deleted & recalculated"
    }
