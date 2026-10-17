from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deribit_client.db.repository import IndexPriceRepository
from deribit_client.domain import IndexPrice, Ticker


@pytest.fixture
async def repository(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[IndexPriceRepository]:
    async with session_factory() as session:
        yield IndexPriceRepository(session)


def btc(timestamp: int, price: str = "100") -> IndexPrice:
    return IndexPrice(ticker=Ticker.BTC_USD, price=Decimal(price), timestamp=timestamp)


async def test_get_latest_returns_newest_by_timestamp(repository: IndexPriceRepository) -> None:
    await repository.add(btc(200, price="2"))
    await repository.add(btc(100, price="1"))

    assert await repository.get_latest(Ticker.BTC_USD) == btc(200, price="2")


async def test_add_skips_duplicate(repository: IndexPriceRepository) -> None:
    await repository.add(btc(100, price="1"))
    await repository.add(btc(100, price="2"))

    assert await repository.get_all(Ticker.BTC_USD, limit=10, offset=0) == [btc(100,
                                                                                price="1")]


async def test_get_all_filters_by_ticker_and_sorts_by_time(repository: IndexPriceRepository) -> None:
    eth = IndexPrice(ticker=Ticker.ETH_USD, price=Decimal("1"), timestamp=150)
    for price in (btc(300), eth, btc(100), btc(200)):
        await repository.add(price)

    assert await repository.get_all(Ticker.BTC_USD, limit=10, offset=0) == [
        btc(100),
        btc(200),
        btc(300),
    ]


async def test_get_all_paginates(repository: IndexPriceRepository) -> None:
    for timestamp in (100, 200, 300):
        await repository.add(btc(timestamp))

    assert await repository.get_all(Ticker.BTC_USD, limit=1, offset=1) == [btc(200)]


async def test_get_by_range_includes_bounds(repository: IndexPriceRepository) -> None:
    for timestamp in (100, 200, 300, 400):
        await repository.add(btc(timestamp))

    result = await repository.get_by_range(Ticker.BTC_USD, date_from=200, date_to=300, limit=10, offset=0)

    assert result == [btc(200), btc(300)]


async def test_get_by_range_with_open_bound(repository: IndexPriceRepository) -> None:
    for timestamp in (100, 200, 300):
        await repository.add(btc(timestamp))

    result = await repository.get_by_range(Ticker.BTC_USD, date_from=200, date_to=None, limit=10, offset=0)

    assert result == [btc(200), btc(300)]