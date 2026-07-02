# Database connection aur session setup
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

# Base class tables ke liye
class Base(DeclarativeBase):
    pass

# Dependency injection FastAPI routers ke liye
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session