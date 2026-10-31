"""Handlers package."""
from .registration import router as registration_router
from .common import router as common_router
from .apartments import router as apartments_router
from .admin import router as admin_router

__all__ = [
    "registration_router",
    "common_router",
    "apartments_router",
    "admin_router",
]
