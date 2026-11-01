"""Telegram Mini App: aiohttp web server running inside the bot process."""
from .server import create_app, start_webapp, stop_webapp

__all__ = ["create_app", "start_webapp", "stop_webapp"]
