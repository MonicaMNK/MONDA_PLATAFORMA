"""Compatibilidad temporal con imports anteriores. Use backend.app.db y backend.app.models."""
from .app.db.session import SessionLocal, engine
from .app.db.seed import init_test_db as init_db, seed_demo_data
from .app.models import *  # noqa: F401,F403
from .app.models import uid, now
from .app.db.audit import audit
from .app.core.config import ROOT, DATA_DIR
