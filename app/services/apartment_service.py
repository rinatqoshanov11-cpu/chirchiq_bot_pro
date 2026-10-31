"""Database service for apartment operations."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Apartment, User
from app.models.apartment import ApartmentType, ApartmentStatus


class ApartmentService:
    """Service for apartment database operations."""

    @staticmethod
    async def create_apartment(
        session: AsyncSession,
        owner_id: int,
        apartment_type: ApartmentType,
        rooms: int,
        address: str,
        price: int,
        phone_number: str,
        **kwargs
    ) -> Apartment:
        """Create new apartment listing."""
        apartment = Apartment(
            owner_id=owner_id,
            type=apartment_type,
            rooms=rooms,
            address=address,
            price=price,
            phone_number=phone_number,
            **kwargs
        )
        session.add(apartment)
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        apartment_id: int,
        load_owner: bool = True
    ) -> Optional[Apartment]:
        """Get apartment by ID."""
        query = select(Apartment).where(Apartment.id == apartment_id)

        if load_owner:
            query = query.options(selectinload(Apartment.owner))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_apartments(
        session: AsyncSession,
        user_id: int,
        active_only: bool = False
    ) -> List[Apartment]:
        """Get all apartments by user."""
        query = select(Apartment).where(Apartment.owner_id == user_id)

        if active_only:
            query = query.where(
                and_(
                    Apartment.is_active == True,
                    Apartment.status == ApartmentStatus.APPROVED
                )
            )

        query = query.order_by(Apartment.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def search_apartments(
        session: AsyncSession,
        apartment_type: Optional[ApartmentType] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        status: ApartmentStatus = ApartmentStatus.APPROVED,
        limit: int = 20,
        offset: int = 0
    ) -> List[Apartment]:
        """Search apartments with filters."""
        query = select(Apartment).options(selectinload(Apartment.owner))

        # Base filters
        query = query.where(
            and_(
                Apartment.is_active == True,
                Apartment.status == status
            )
        )

        # Apply filters
        if apartment_type:
            query = query.where(Apartment.type == apartment_type)

        if min_rooms:
            query = query.where(Apartment.rooms >= min_rooms)

        if max_rooms:
            query = query.where(Apartment.rooms <= max_rooms)

        if min_price:
            query = query.where(Apartment.price >= min_price)

        if max_price:
            query = query.where(Apartment.price <= max_price)

        # Order and paginate
        # id is a tie-breaker so pages never repeat or skip a listing
        query = query.order_by(Apartment.created_at.desc(), Apartment.id.desc()).limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count_search(
        session: AsyncSession,
        apartment_type: Optional[ApartmentType] = None,
        status: ApartmentStatus = ApartmentStatus.APPROVED,
    ) -> int:
        """Count apartments that search_apartments would return (type filter only)."""
        query = select(func.count(Apartment.id)).where(
            and_(
                Apartment.is_active == True,
                Apartment.status == status
            )
        )
        if apartment_type:
            query = query.where(Apartment.type == apartment_type)

        result = await session.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_pending_apartments(
        session: AsyncSession,
        limit: int = 50
    ) -> List[Apartment]:
        """Get pending apartments for admin approval."""
        query = select(Apartment).options(selectinload(Apartment.owner)).where(
            Apartment.status == ApartmentStatus.PENDING
        ).order_by(Apartment.created_at.asc()).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def approve_apartment(session: AsyncSession, apartment: Apartment) -> Apartment:
        """Approve apartment listing."""
        apartment.status = ApartmentStatus.APPROVED
        apartment.is_active = True
        apartment.published_at = datetime.utcnow()
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @staticmethod
    async def reject_apartment(session: AsyncSession, apartment: Apartment) -> Apartment:
        """Reject apartment listing."""
        apartment.status = ApartmentStatus.REJECTED
        apartment.is_active = False
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @staticmethod
    async def archive_apartment(session: AsyncSession, apartment: Apartment) -> Apartment:
        """Archive apartment listing."""
        apartment.status = ApartmentStatus.ARCHIVED
        apartment.is_active = False
        apartment.archived_at = datetime.utcnow()
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @staticmethod
    async def delete_apartment(session: AsyncSession, apartment: Apartment) -> None:
        """Delete apartment listing."""
        await session.delete(apartment)
        await session.commit()

    @staticmethod
    async def update_apartment(
        session: AsyncSession,
        apartment: Apartment,
        **kwargs
    ) -> Apartment:
        """Update apartment fields."""
        for key, value in kwargs.items():
            if hasattr(apartment, key):
                setattr(apartment, key, value)

        apartment.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(apartment)
        return apartment

    @staticmethod
    async def get_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get apartment statistics."""
        # Total apartments
        total = await session.execute(select(func.count(Apartment.id)))
        total_count = total.scalar_one()

        # Active apartments
        active = await session.execute(
            select(func.count(Apartment.id)).where(
                and_(
                    Apartment.is_active == True,
                    Apartment.status == ApartmentStatus.APPROVED
                )
            )
        )
        active_count = active.scalar_one()

        # Pending apartments
        pending = await session.execute(
            select(func.count(Apartment.id)).where(
                Apartment.status == ApartmentStatus.PENDING
            )
        )
        pending_count = pending.scalar_one()

        # By type
        rent = await session.execute(
            select(func.count(Apartment.id)).where(
                and_(
                    Apartment.type == ApartmentType.RENT,
                    Apartment.is_active == True,
                    Apartment.status == ApartmentStatus.APPROVED
                )
            )
        )
        rent_count = rent.scalar_one()

        sale = await session.execute(
            select(func.count(Apartment.id)).where(
                and_(
                    Apartment.type == ApartmentType.SALE,
                    Apartment.is_active == True,
                    Apartment.status == ApartmentStatus.APPROVED
                )
            )
        )
        sale_count = sale.scalar_one()

        # Total views
        views = await session.execute(select(func.sum(Apartment.view_count)))
        total_views = views.scalar_one() or 0

        return {
            "total": total_count,
            "active": active_count,
            "pending": pending_count,
            "rent": rent_count,
            "sale": sale_count,
            "total_views": total_views,
        }

    @staticmethod
    async def find_duplicate(
        session: AsyncSession,
        address: str,
        rooms: int,
        price: int,
        apartment_type: ApartmentType
    ) -> Optional[Apartment]:
        """Find potential duplicate apartment."""
        result = await session.execute(
            select(Apartment).where(
                and_(
                    Apartment.address == address,
                    Apartment.rooms == rooms,
                    Apartment.price == price,
                    Apartment.type == apartment_type,
                    Apartment.is_active == True
                )
            ).limit(1)
        )
        return result.scalar_one_or_none()
