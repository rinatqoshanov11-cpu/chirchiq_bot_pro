"""Logging middleware for aiogram."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import UserService
from app.utils import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware to log all user interactions."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Log user activity."""
        user = None
        session: AsyncSession = data.get('session')

        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                f"Message from {user.id} (@{user.username}): "
                f"{event.text[:50] if event.text else '[media]'}"
            )
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(
                f"Callback from {user.id} (@{user.username}): "
                f"{event.data}"
            )

        # Update user's last activity
        if user and session:
            try:
                db_user = await UserService.get_by_telegram_id(session, user.id)
                if db_user:
                    await UserService.update_last_activity(session, db_user)
            except Exception as e:
                logger.error(f"Error updating last activity: {e}")

        return await handler(event, data)
