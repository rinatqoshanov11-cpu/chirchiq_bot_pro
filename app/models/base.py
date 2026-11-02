"""Base database configuration."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.db_echo,
    pool_pre_ping=True,
    # Small pool: free hosted Postgres plans (e.g. Neon) allow few connections
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Columns added after the table was first created (no Alembic migrations in this project)
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION"))
        await conn.execute(text("ALTER TABLE apartments ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION"))
        # Registration no longer asks for a home address
        await conn.execute(text("ALTER TABLE users ALTER COLUMN address DROP NOT NULL"))


async def close_db():
    """Close database connections."""
    await engine.dispose()
