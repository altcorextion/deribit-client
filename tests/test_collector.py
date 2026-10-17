from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deribit_client.db.repository import IndexPriceRepository
from deribit_client.deribit.client import DeribitClient
from deribit_client.deribit.errors import DeribitError
from deribit_client.deribit.transport import DeribitResponse
from deribit_client.domain import IndexPrice, Ticker
from deribit_client.worker.collector import IndexPriceCollector


class FakeTransport:
    """ Отвечает ценой 100 или кидает DeribitError для index_name из failing """

    def __init__(self, failing: frozenset[str] = frozenset()) -> None:
        self._failing = failing

    async def call(self, method: str, params: dict[str, Any]) -> DeribitResponse:
        if params["index_name"] in self._failing:
            raise DeribitError(-32602, "Invalid params")
        return DeribitResponse(result={"index_price": Decimal("100")}, us_out=1792160429679898)


def price(ticker: Ticker) -> IndexPrice:
    return IndexPrice(ticker=ticker, price=Decimal("100"), timestamp=1792160429)


async def test_collect_saves_all_tickers(
        session_factory: async_sessionmaker[AsyncSession],
) -> None:
    collector = IndexPriceCollector(DeribitClient(FakeTransport()), session_factory)

    await collector.collect([Ticker.BTC_USD, Ticker.ETH_USD])

    async with session_factory() as session:
        repository = IndexPriceRepository(session)
        assert await repository.get_latest(Ticker.BTC_USD) == price(Ticker.BTC_USD)
        assert await repository.get_latest(Ticker.ETH_USD) == price(Ticker.ETH_USD)


async def test_collect_saves_successful_and_raises_for_failed(
        session_factory: async_sessionmaker[AsyncSession],
) -> None:
    transport = FakeTransport(failing=frozenset({"eth_usd"}))
    collector = IndexPriceCollector(DeribitClient(transport), session_factory)

    with pytest.raises(ExceptionGroup) as exc_info:
        await collector.collect([Ticker.BTC_USD, Ticker.ETH_USD])

    assert exc_info.group_contains(DeribitError)
    async with session_factory() as session:
        repository = IndexPriceRepository(session)
        assert await repository.get_latest(Ticker.BTC_USD) == price(Ticker.BTC_USD)
        assert await repository.get_latest(Ticker.ETH_USD) is None