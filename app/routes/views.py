from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from app.database import db_manager

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter(tags=["views"])

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={"page": "home"})

@router.get("/plans")
def plans(request: Request):
    return templates.TemplateResponse(request=request, name="plans.html", context={"page": "plans"})

@router.get("/return")
def returns(request: Request):
    return templates.TemplateResponse(request=request, name="return.html", context={"page": "return"})

@router.get("/login")
def login_view(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"page": "login"})

@router.get("/signup")
def signup_view(request: Request):
    return templates.TemplateResponse(request=request, name="signup.html", context={"page": "signup"})

@router.get("/adminlogin")
def admin_login_view(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html", context={"page": "adminlogin"})

@router.get("/portfolio")
def portfolio_view(request: Request):
    return templates.TemplateResponse(request=request, name="portfolio.html", context={"page": "portfolio"})

@router.get("/admin")
def admin_view(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"page": "admin"})

@router.get("/api/status")
def status_api():
    return db_manager.get_status()
