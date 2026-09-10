"""HTTP integration boundary for browser-facing production simulation."""

from .app import app, create_app

__all__ = ["app", "create_app"]
