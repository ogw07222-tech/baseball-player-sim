"""HTTP integration boundary for browser-facing production simulation."""
from __future__ import annotations

__all__ = ["app", "create_app"]


def __getattr__(name: str):
    """Lazily expose app symbols without importing app.py during package init."""
    if name in __all__:
        from .app import app, create_app

        return {"app": app, "create_app": create_app}[name]
    raise AttributeError(name)
