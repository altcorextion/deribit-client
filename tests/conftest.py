from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from deribit_client.config import DatabaseSettings


@pytest.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    settings = DatabaseSettings()
    engine = create_async_engine(settings.url.set(database=f"{settings.name}_test"))
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield async_sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
        await transaction.rollback()
    await engine.dispose()
