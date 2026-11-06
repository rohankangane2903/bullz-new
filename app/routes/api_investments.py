from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.models import InvestmentCreate, RateOrExtendRequest
from app.services.investment_service import (
    create_investment,
    get_user_investments,
    get_all_investments,
    update_investment_rate_and_rollover,
    toggle_investment_status,
    delete_investment
)
from app.services.auth_service import find_user_by_email

router = APIRouter(prefix="/api/investments", tags=["investments"])

@router.get("")
def list_investments(email: Optional[str] = Query(None)):
    if email:
        return get_user_investments(email)
    return get_all_investments()

@router.post("")
def create_new_investment(req: InvestmentCreate):
    if req.amount < 500:
        raise HTTPException(status_code=400, detail="Minimum starting investment amount is ₹500")

    user = find_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    inv = create_investment({
        "userId": user["_id"],
        "userEmail": user["email"],
        "userName": user["name"],
        "amount": req.amount,
        "tenure": req.tenure,
        "term": req.term,
        "ratePercent": req.ratePercent,
        "paymentId": req.paymentId
    })
    return {"success": True, "investment": inv}

@router.put("/{inv_id}/rate-or-extend")
def update_rate_or_extend(inv_id: str, req: RateOrExtendRequest):
    inv = update_investment_rate_and_rollover(
        investment_id=inv_id,
        new_rate_percent=req.newRatePercent,
        additional_months=req.additionalMonths,
        rollover_profit=req.rolloverProfit,
        note=req.note
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return {
        "success": True,
        "message": "Investment rate and balance updated successfully!",
        "investment": inv
    }

@router.put("/{inv_id}/status")
def toggle_status(inv_id: str):
    inv = toggle_investment_status(inv_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return {"success": True, "investment": inv}

@router.delete("/{inv_id}")
def delete_inv(inv_id: str):
    ok = delete_investment(inv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Investment not found")
    return {"success": True, "message": "Investment deleted"}
