from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = ""

class UserLogin(BaseModel):
    email: str
    password: str
    role: Optional[str] = "user"

class ProfileUpdate(BaseModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None

class AdminCreateClient(BaseModel):
    name: str
    email: str
    password: Optional[str] = "1234"
    phone: Optional[str] = ""
    startDate: Optional[str] = ""
    initialAmount: Optional[float] = 0.0
    initialRate: Optional[float] = 10.0
    notes: Optional[str] = ""

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    startDate: Optional[str] = None

class InvestmentCreate(BaseModel):
    email: str
    amount: float
    tenure: str
    term: Optional[str] = None
    ratePercent: Optional[float] = 5.0
    paymentId: Optional[str] = None

class RateOrExtendRequest(BaseModel):
    newRatePercent: float
    additionalMonths: Optional[int] = 4
    rolloverProfit: Optional[bool] = False
    note: Optional[str] = ""

class LedgerEntryCreate(BaseModel):
    userEmail: str
    entryDate: Optional[str] = ""
    investmentAdded: Optional[float] = 0.0
    rate: float = 10.0
    note: Optional[str] = ""

class LedgerEntryUpdate(BaseModel):
    userEmail: Optional[str] = None
    entryDate: Optional[str] = None
    investmentAdded: Optional[float] = None
    rate: Optional[float] = None
    note: Optional[str] = None

class PaymentOrderCreate(BaseModel):
    amount: float
    userEmail: str
    userName: Optional[str] = "Investor"
    planDetails: Dict[str, Any]

class PaymentVerify(BaseModel):
    orderId: str
    paymentId: Optional[str] = None
    method: Optional[str] = "UPI"
    userEmail: str
    plan: Dict[str, Any]
