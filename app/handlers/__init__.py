"""Handlers package."""
from .language import router as language_router
from .registration import router as registration_router
from .common import router as common_router
from .apartments import router as apartments_router
from .admin import router as admin_router
from .fallback import router as fallback_router

__all__ = [
    "language_router",
    "registration_router",
    "common_router",
    "apartments_router",
    "admin_router",
    "fallback_router",
]
