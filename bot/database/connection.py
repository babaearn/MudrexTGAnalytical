"""Database connection management"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from bot.config import Config
from bot.database.models import Base

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine = None
_async_session_maker = None


def get_async_database_url(url: str) -> str:
    """Convert PostgreSQL URL to async format"""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def init_db():
    """Initialize database connection and create tables"""
    global _engine, _async_session_maker

    try:
        database_url = get_async_database_url(Config.DATABASE_URL)

        _engine = create_async_engine(
            database_url,
            echo=False,
            poolclass=NullPool,  # Use NullPool for serverless environments
            pool_pre_ping=True,
        )

        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create all tables
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def get_session() -> AsyncSession:
    """Get a new database session"""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _async_session_maker()


async def close_db():
    """Close database connection"""
    global _engine

    if _engine:
        await _engine.dispose()
        logger.info("Database connection closed")


async def test_connection() -> bool:
    """Test database connection"""
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
