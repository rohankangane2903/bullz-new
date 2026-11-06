# Bullz (Python & MongoDB Edition) 🚀

Rebuilt completely from scratch as a high-performance Python web application with native **MongoDB** database support, modern **FastAPI** backend, and responsive **Jinja2** frontend.

---

## 🌟 Highlights

- **Backend**: Python 3.10+ (FastAPI + Uvicorn + PyMongo + Bcrypt + PyJWT)
- **Database**: **MongoDB** (`users`, `investments`, `monthly_ledgers`, `notifications`, `payments`)
  - Auto-connects to MongoDB using `MONGODB_URI` from `.env`.
  - Zero-downtime local disk store (`data/bullz_store.json`) for seamless offline operation & instant recovery.
  - Automatically seeds and synchronizes to MongoDB when connected.
- **Frontend**: Python-rendered Jinja2 templates + Ultra-modern fintech dark/light theme + Aurora animations + Interactive client-side controllers.
- **Monthly Compound Ledger Engine**: Real-time cascading calculation of closing balances, capital additions, monthly returns, and interest rollovers.
- **Role-Separated Authentication**:
  - **Investor Portal**: Sign up, Log in, View Portfolio, Track Ledger, Export to CSV, Profile updates.
  - **Admin Command Center**: Onboard clients (with backdated dates), CRUD operations on Monthly Ledgers with cascading recalculations, Rate & Profit Rollovers, Live Activity Feed.
- **Checkout & Simulation**: Multi-channel payment simulation (UPI, Card, NetBanking, Razorpay Sandbox) with auto-contract activation in MongoDB.

---

## 📁 Project Structure

```
bullz new/
├── app/
│   ├── routes/
│   │   ├── views.py              # HTML Frontend Views (Home, Plans, Return, Login, Admin, Portfolio)
│   │   ├── api_auth.py           # Registration, Login, Profile updates
│   │   ├── api_admin.py          # Admin client management, creation with initial ledger
│   │   ├── api_investments.py    # Investment contracts & rate/rollover logic
│   │   ├── api_ledger.py         # Monthly compound ledger CRUD with cascade recalculation
│   │   ├── api_notifications.py  # Live admin activity notifications
│   │   └── api_payments.py       # Payment intent creation & verification
│   ├── services/
│   │   ├── auth_service.py       # Bcrypt password hashing & JWT token issuance
│   │   ├── ledger_service.py     # Compound monthly ledger formula & date normalization
│   │   ├── investment_service.py # Term calculations & profit rollover
│   │   ├── notification_service.py # Event logging & unread tracking
│   │   └── payment_service.py    # Payment order processing & auto-activation
│   ├── config.py                 # Configuration loader from .env
│   ├── database.py               # MongoDB PyMongo connection & disk fallback store
│   ├── models.py                 # Pydantic validation schemas
│   └── main.py                   # FastAPI Application setup & static routing
├── static/
│   ├── assets/                   # Brand logos & SVG illustrations
│   ├── css/style.css             # Glassmorphism dark/light fintech design system
│   └── js/app.js                 # Interactive client state, calculators & API integration
├── templates/
│   ├── base.html                 # Common shell, navbar, theme toggle, modals
│   ├── home.html                 # Landing page (hero, about, theory, CTA, contact)
│   ├── plans.html                # Plans & real-time return calculator
│   ├── return.html               # Return model & compound ledger breakdown
│   ├── login.html                # User login portal
│   ├── signup.html               # User registration
│   ├── admin_login.html          # Dedicated Administrator Portal
│   ├── portfolio.html            # User portfolio with full monthly compound ledger
│   └── admin.html                # Admin command center & ledger manager
├── data/                         # Local persistence store for zero-downtime operation
├── .env                          # Environment variables & MongoDB URI
├── requirements.txt              # Python dependencies
├── run.py                        # Single-command application launcher
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Run the Application

From within the `bullz new` directory, run:

```bash
python run.py
```

The application will start on **`http://127.0.0.1:8000`**.

### 2. Configure MongoDB

By default, the application connects to local MongoDB:
```ini
MONGODB_URI=mongodb://127.0.0.1:27017/bullz
MONGODB_DB_NAME=bullz
```

To connect to **MongoDB Atlas (Cloud)**, open `.env` and update the connection string:
```ini
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/bullz?retryWrites=true&w=majority
```

*Note: If MongoDB is starting or momentarily unreachable, the application automatically uses its local disk store (`data/bullz_store.json`), and automatically synchronizes to MongoDB as soon as it connects.*

---

## 🔐 Default Credentials

- **Admin Portal**: [http://127.0.0.1:8000/adminlogin](http://127.0.0.1:8000/adminlogin)
  - **Email**: `admin@gmail.com`
  - **Password**: `admin`
- **User Portal**: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
  - Or sign up a new account at [http://127.0.0.1:8000/signup](http://127.0.0.1:8000/signup)

---

## 📊 Monthly Compound Ledger Calculation Formula

```
Base = Previous Closing Balance + Injected Capital
Monthly Interest = Base * (Rate % / 100)
Total Balance = Base + Monthly Interest
```

Whenever an entry is added, updated, or removed, the entire chain recalculates dynamically across all subsequent rows.
