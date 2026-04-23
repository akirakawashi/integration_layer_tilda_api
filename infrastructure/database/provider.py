from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from setting.config import database_config


class DatabaseProvider:
    _engine: AsyncEngine | None = None
    _session_maker: async_sessionmaker[AsyncSession] | None = None

    @classmethod
    async def init_engine(cls) -> None:
        """Initialize the database engine"""
        if cls._engine is None:
            logger.debug(
                f"Creating database engine: pool_size={database_config.pool_size}, "
                f"max_overflow={database_config.max_overflow}"
            )
            cls._engine = create_async_engine(
                database_config.url,
                echo=database_config.echo,
                pool_size=database_config.pool_size,
                max_overflow=database_config.max_overflow,
                pool_pre_ping=True,
            )
            cls._session_maker = async_sessionmaker(cls._engine, expire_on_commit=False, class_=AsyncSession)

        if cls._session_maker is None:
            raise RuntimeError("Session maker is not initialized")

    @classmethod
    async def dispose_engine(cls) -> None:
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_maker = None

    @classmethod
    @asynccontextmanager
    async def session_lifecycle(cls) -> AsyncIterator[AsyncSession]:
        """Provide a database session with proper lifecycle management"""
        if cls._session_maker is None:
            await cls.init_engine()

        if cls._session_maker is None:
            raise RuntimeError("Database engine is not initialized")

        async with cls._session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def get_session(cls) -> AsyncIterator[AsyncSession]:
        """Get a new database session"""
        async with cls.session_lifecycle() as session:
            yield session
