from collections.abc import AsyncIterator
from decimal import Decimal

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deribit_client.api.app import create_app
from deribit_client.api.routes import get_repository
from deribit_client.db.repository import IndexPriceRepository
from deribit_client.domain import IndexPrice, Ticker


@pytest.fixture
async def repository(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[IndexPriceRepository]:
    async with session_factory() as session:
        yield IndexPriceRepository(session)


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[httpx.AsyncClient]:
    async def override_repository() -> AsyncIterator[IndexPriceRepository]:
        async with session_factory() as session:
            yield IndexPriceRepository(session)

    app = create_app()
    app.dependency_overrides[get_repository] = override_repository
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def btc(timestamp: int) -> IndexPrice:
    return IndexPrice(ticker=Ticker.BTC_USD, price=Decimal("100.5"), timestamp=timestamp)


async def test_ticker_is_required(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/prices/latest")

    assert response.status_code == 422


async def test_unknown_ticker_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/prices/latest", params={"ticker": "xxx_usd"})

    assert response.status_code == 422


async def test_latest_returns_404_without_data(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/prices/latest", params={"ticker": "btc_usd"})

    assert response.status_code == 404


async def test_latest_returns_newest_price(
    client: httpx.AsyncClient, repository: IndexPriceRepository
) -> None:
    await repository.add(btc(100))
    await repository.add(btc(200))

    response = await client.get("/api/v1/prices/latest", params={"ticker": "btc_usd"})

    assert response.status_code == 200
    body = response.json()
    assert (body["ticker"], body["timestamp"]) == ("btc_usd", 200)
    assert Decimal(body["price"]) == Decimal("100.5")


async def test_prices_paginates(
    client: httpx.AsyncClient, repository: IndexPriceRepository
) -> None:
    for timestamp in (100, 200, 300):
        await repository.add(btc(timestamp))

    response = await client.get(
        "/api/v1/prices", params={"ticker": "btc_usd", "limit": 1, "offset": 1}
    )

    assert [item["timestamp"] for item in response.json()] == [200]


async def test_filtered_returns_range(
    client: httpx.AsyncClient, repository: IndexPriceRepository
) -> None:
    for timestamp in (100, 200, 300):
        await repository.add(btc(timestamp))

    response = await client.get(
        "/api/v1/prices/filtered", params={"ticker": "btc_usd", "from": 150, "to": 300}
    )

    assert [item["timestamp"] for item in response.json()] == [200, 300]


async def test_filtered_rejects_inverted_range(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/prices/filtered", params={"ticker": "btc_usd", "from": 300, "to": 100}
    )

    assert response.status_code == 422
