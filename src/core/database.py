# src/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL — use env var or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/disaster_intel")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL logging in dev
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
)

# Async sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Function to create all tables
async def create_tables():
    from src.core.models import Base  # Import here to avoid circular import
    async with engine.begin() as conn:
        # Optional: uncomment to drop all tables (dev only)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")

# Health check function
async def check_db_connection():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    return False