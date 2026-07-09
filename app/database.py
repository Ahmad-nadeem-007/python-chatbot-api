# Database connection and session setup
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Async Engine setup
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Session maker for async queries
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for tables
class Base(DeclarativeBase):
    pass

# Dependency injection for FastAPI routers
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session