from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import BASE_DIR
from app.database import db_manager
from app.routes.views import router as views_router
from app.routes.api_auth import router as auth_router
from app.routes.api_investments import router as investments_router
from app.routes.api_ledger import router as ledger_router
from app.routes.api_admin import router as admin_router
from app.routes.api_notifications import router as notif_router
from app.routes.api_payments import router as payments_router

app = FastAPI(
    title="Bullz Investment Platform",
    description="Python & MongoDB Powered High-Performance Investment & Ledger Platform",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (CSS, JS, Assets)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include Routers
app.include_router(views_router)
app.include_router(auth_router)
app.include_router(investments_router)
app.include_router(ledger_router)
app.include_router(admin_router)
app.include_router(notif_router)
app.include_router(payments_router)

@app.on_event("startup")
async def startup_event():
    db_manager.connect()
