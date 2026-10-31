"""User model."""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, BigInteger, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class User(Base):
    """User model for storing user information."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_registered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    apartments: Mapped[List["Apartment"]] = relationship(
        "Apartment",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, full_name='{self.full_name}')>"

    @property
    def is_superadmin(self) -> bool:
        """Check if user is superadmin (defined in settings)."""
        from config import settings
        return self.telegram_id in settings.admin_ids

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "address": self.address,
            "is_admin": self.is_admin,
            "is_registered": self.is_registered,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
