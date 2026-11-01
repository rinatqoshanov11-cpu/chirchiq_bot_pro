"""Apartment model."""
from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum
from sqlalchemy import (
    String, Integer, BigInteger, Boolean, DateTime,
    Text, Float, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ApartmentType(str, PyEnum):
    """Apartment type enumeration."""
    RENT = "rent"
    SALE = "sale"


class ApartmentStatus(str, PyEnum):
    """Apartment status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class Apartment(Base):
    """Apartment model for storing apartment listings."""

    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Owner information
    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Apartment details
    type: Mapped[ApartmentType] = mapped_column(
        Enum(ApartmentType, native_enum=False),
        nullable=False,
        index=True
    )
    rooms: Mapped[int] = mapped_column(Integer, nullable=False)
    area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Location
    address: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Pricing
    price: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="UZS", nullable=False)

    # Description and media
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photos: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Contact
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status and visibility
    status: Mapped[ApartmentStatus] = mapped_column(
        Enum(ApartmentStatus, native_enum=False),
        default=ApartmentStatus.PENDING,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Statistics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    external_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="apartments")

    def __repr__(self) -> str:
        return (
            f"<Apartment(id={self.id}, type={self.type.value}, "
            f"rooms={self.rooms}, price={self.price}, status={self.status.value})>"
        )

    @property
    def type_emoji(self) -> str:
        """Get emoji for apartment type."""
        return "🔑" if self.type == ApartmentType.RENT else "💰"

    @property
    def status_emoji(self) -> str:
        """Get emoji for apartment status."""
        emojis = {
            ApartmentStatus.PENDING: "⏳",
            ApartmentStatus.APPROVED: "✅",
            ApartmentStatus.REJECTED: "❌",
            ApartmentStatus.ARCHIVED: "📦",
        }
        return emojis.get(self.status, "❓")

    @property
    def formatted_price(self) -> str:
        """Get formatted price string."""
        return f"{self.price:,} {self.currency}"

    def to_dict(self) -> dict:
        """Convert apartment to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "rooms": self.rooms,
            "address": self.address,
            "price": self.price,
            "description": self.description,
            "photos_count": len(self.photos),
            "phone_number": self.phone_number,
            "status": self.status.value,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    async def increment_views(self, session):
        """Increment view count."""
        self.view_count += 1
        await session.commit()

    async def increment_contacts(self, session):
        """Increment contact count."""
        self.contact_count += 1
        await session.commit()
