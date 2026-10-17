from decimal import Decimal
from typing import Any

import pytest

from deribit_client.deribit.client import DeribitClient
from deribit_client.deribit.transport import DeribitResponse
from deribit_client.domain import Ticker, IndexPrice


class FakeTransport:
    def __init__(self, response: DeribitResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call(self, method: str, params: dict[str, Any]) -> DeribitResponse:
        self.calls.append((method, params))
        return self.response


@pytest.fixture
def transport() -> FakeTransport:
    return FakeTransport(
        DeribitResponse(result={"index_price": Decimal("63463.12")}, us_out=1792192794123123)
    )


async def test_get_index_price_requests_index_by_ticker(transport: FakeTransport) -> None:
    await DeribitClient(transport).get_index_price(Ticker.ETH_USD)

    assert transport.calls == [("public/get_index_price", {"index_name": "eth_usd"})]


async def test_get_index_price_converts_timestamp_to_seconds(transport: FakeTransport) -> None:
    price = await DeribitClient(transport).get_index_price(Ticker.BTC_USD)

    assert price == IndexPrice(
        ticker=Ticker.BTC_USD,
        price=Decimal("63463.12"),
        timestamp=1792192794,
    )