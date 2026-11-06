from fastapi import APIRouter, HTTPException
from app.models import PaymentOrderCreate, PaymentVerify
from app.services.payment_service import create_payment_order, complete_payment

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/create-order")
def create_order(req: PaymentOrderCreate):
    if req.amount < 500:
        raise HTTPException(status_code=400, detail="Minimum starting investment amount is ₹500. You can enter any amount from ₹500 onwards.")
    
    order = create_payment_order({
        "amount": req.amount,
        "userEmail": req.userEmail,
        "userName": req.userName,
        "planDetails": req.planDetails
    })
    return order

@router.post("/verify")
def verify_payment(req: PaymentVerify):
    res = complete_payment(
        order_id=req.orderId,
        payment_id=req.paymentId,
        method=req.method or "UPI",
        user_email=req.userEmail,
        plan=req.plan
    )
    if not res:
        raise HTTPException(status_code=400, detail="Payment verification failed")
    return res
