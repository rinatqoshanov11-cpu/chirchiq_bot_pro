"""Database service for user operations."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User


class UserService:
    """Service for user database operations."""

    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by database ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        full_name: str,
        phone_number: str,
        address: str,
        username: Optional[str] = None,
    ) -> User:
        """Create new user."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            phone_number=phone_number,
            address=address,
            is_registered=True,
            last_activity=datetime.utcnow(),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user: User,
        **kwargs
    ) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_last_activity(session: AsyncSession, user: User) -> None:
        """Update user's last activity timestamp."""
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_activity=datetime.utcnow())
        )
        await session.commit()

    @staticmethod
    async def is_registered(session: AsyncSession, telegram_id: int) -> bool:
        """Check if user is registered."""
        user = await UserService.get_by_telegram_id(session, telegram_id)
        return user is not None and user.is_registered

    @staticmethod
    async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
        """Check if user is admin."""
        from config import settings

        if telegram_id in settings.admin_ids:
            return True

        user = await UserService.get_by_telegram_id(session, telegram_id)
        return user is not None and user.is_admin

    @staticmethod
    async def get_all_users(
        session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
        registered_only: bool = True
    ) -> List[User]:
        """Get all users with pagination."""
        query = select(User)

        if registered_only:
            query = query.where(User.is_registered == True)

        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_count(session: AsyncSession, registered_only: bool = True) -> int:
        """Get total user count."""
        query = select(func.count(User.id))

        if registered_only:
            query = query.where(User.is_registered == True)

        result = await session.execute(query)
        return result.scalar_one()

    @staticmethod
    async def block_user(session: AsyncSession, user: User) -> User:
        """Block user."""
        user.is_blocked = True
        user.is_active = False
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def unblock_user(session: AsyncSession, user: User) -> User:
        """Unblock user."""
        user.is_blocked = False
        user.is_active = True
        await session.commit()
        await session.refresh(user)
        return user
