"""Compatibilidad temporal con el módulo histórico de seguridad."""
from .app.core.security import *  # noqa: F401,F403
from .app.core.config import settings
ACCESS_MINUTES = settings.access_minutes
