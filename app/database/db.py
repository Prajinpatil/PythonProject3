"""
Database Configuration - SQLAlchemy Setup
Async database with SQLite (easily switchable to PostgreSQL)
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# ========== DATABASE ENGINE ==========
# Using SQLite for dev/hackathon - switch to PostgreSQL for production
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    future=True,
    # SQLite-specific settings (remove for PostgreSQL)
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# ========== SESSION FACTORY ==========
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# ========== BASE MODEL ==========
Base = declarative_base()


# ========== DEPENDENCY ==========
async def get_db() -> AsyncSession:
    """
    Dependency for database sessions
    
    Usage in FastAPI routes:
        @router.get("/events")
        async def get_events(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== DATABASE LIFECYCLE ==========
async def init_db():
    """
    Initialize database
    Creates all tables
    """
    logger.info("Initializing database...")
    
    async with engine.begin() as conn:
        # Drop all tables (for dev - remove in production)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_db():
    """
    Close database connections
    Call on application shutdown
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database sessions
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ========== HEALTH CHECK ==========
async def check_db_health() -> bool:
    """
    Check if database is accessible
    Used for health check endpoints
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
