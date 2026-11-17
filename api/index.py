import sys
from pathlib import Path

# Ensure the project root is on sys.path so 'app' package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

# Vercel ASGI handler
handler = app
