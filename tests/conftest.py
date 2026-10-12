import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEST_DB = ROOT / "data" / "test_entrega2.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB}")
os.environ.setdefault("MONDA_ALLOW_PBKDF2_FOR_TESTS", "1")
os.environ.setdefault("MONDA_DEMO", "1")
os.environ.setdefault("RAG_MODE", "fallback")
os.environ.setdefault("COOKIE_SECURE", "0")
