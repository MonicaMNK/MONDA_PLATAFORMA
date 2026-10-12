"""Compatibilidad: el punto de entrada histórico ahora reexporta la app modular."""
from .app.main import app

__all__ = ["app"]
