"""
Nazmito API package initializer.
"""

# Expose FastAPI app for convenience when importing api
try:
    from .main import app  # noqa: F401
except Exception:
    # Avoid import-time failures during partial environments (e.g., tests collecting)
    app = None  # type: ignore
