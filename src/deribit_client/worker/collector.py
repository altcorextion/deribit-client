import asyncio
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from deribit_client.db.repository import IndexPriceRepository
from deribit_client.deribit.client import DeribitClient
from deribit_client.domain import Ticker, IndexPrice


class IndexPriceCollector:
    """ Забирает index price по тикерам и сохраняет их """

    def __init__(
            self, client: DeribitClient, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._client = client
        self._session_factory = session_factory

    async def collect(self, tickers: Sequence[Ticker]) -> list[IndexPrice]:
        results = await asyncio.gather(
            *(self._client.get_index_price(ticker) for ticker in tickers),
            return_exceptions=True,
        )
        prices = [result for result in results if isinstance(result, IndexPrice)]
        errors = [result for result in results if isinstance(result, BaseException)]

        async with self._session_factory() as session, session.begin():
            repository = IndexPriceRepository(session)
            for price in prices:
                await repository.add(price)

        if errors:
            raise BaseExceptionGroup("Failed to fetch index prices", errors)

        return prices