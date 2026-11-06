import sys
from pathlib import Path

# Force UTF-8 stdout/stderr encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"[*] Bullz Python Web Application is live at: http://{HOST}:{PORT}")
    print(f"[*] Admin Portal: http://{HOST}:{PORT}/adminlogin")
    print(f"[*] Investor Login: http://{HOST}:{PORT}/login")
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info", app_dir=str(PROJECT_ROOT))
