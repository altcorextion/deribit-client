import asyncio

import aiohttp
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from deribit_client.config import DatabaseSettings, DeribitSettings
from deribit_client.deribit.client import DeribitClient
from deribit_client.deribit.transport import HttpTransport
from deribit_client.domain import Ticker
from deribit_client.worker.collector import IndexPriceCollector


def collect_index_prices() -> None:
    asyncio.run(_collect_index_prices(DeribitSettings(), DatabaseSettings()))


async def _collect_index_prices(deribit: DeribitSettings, database: DatabaseSettings) -> None:
    engine = create_async_engine(database.url, poolclass=NullPool)
    try:
        timeout = aiohttp.ClientTimeout(total=deribit.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            client = DeribitClient(HttpTransport(session, deribit.url))
            collector = IndexPriceCollector(client, async_sessionmaker(engine))
            await collector.collect(list(Ticker))
    finally:
        await engine.dispose()
