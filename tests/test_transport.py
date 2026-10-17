from decimal import Decimal
from typing import Any, AsyncIterator

import aiohttp
import pytest
from aiohttp import web, test_utils

from deribit_client.deribit.errors import DeribitError
from deribit_client.deribit.transport import HttpTransport, DeribitResponse


class FakeDeribit:
    """ Ответ json-prc 2.0 payload и итерация запросов """

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.status = 200
        self.payload: dict[str, Any] | str = {"jsonrpc": "2.0", "result": {}, "usOut": 0}

    async def handle(self, request: web.Request) -> web.Response:
        self.requests.append(await request.json())
        if isinstance(self.payload, str):
            return web.Response(status=self.status, text=self.payload,
                                content_type="text/html")
        return web.json_response(self.payload, status=self.status)


@pytest.fixture
def deribit() -> FakeDeribit:
    return FakeDeribit()


@pytest.fixture
async def transport(deribit: FakeDeribit) -> AsyncIterator[HttpTransport]:
    app = web.Application()
    app.router.add_post("/api/v2", deribit.handle)
    async with test_utils.TestServer(app) as server, aiohttp.ClientSession() as session:
        yield HttpTransport(session, str(server.make_url("/api/v2")))


async def test_sends_json_rpc_request(deribit: FakeDeribit, transport: HttpTransport) -> None:
    await transport.call("public/get_index_price", {"index_name": "btc_usd"})

    assert deribit.requests == [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "public/get_index_price",
            "params": {"index_name": "btc_usd"},
        }
    ]


async def test_increments_request_id(deribit: FakeDeribit, transport: HttpTransport) -> None:
    await transport.call("public/test", {})
    await transport.call("public/test", {})

    assert [request["id"] for request in deribit.requests] == [1, 2]


async def test_returns_result_and_server_time(deribit: FakeDeribit, transport: HttpTransport) -> None:
    deribit.payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"index_price": 82263.52, "estimated_delivery_price": 82263.52},
        "usIn": 1792160429679607,
        "usOut": 1792160429679898,
        "usDiff": 291,
        "testnet": False,
    }

    response = await transport.call("public/get_index_price", {"index_name": "btc_usd"})

    assert response == DeribitResponse(
        result={
            "index_price": Decimal("82263.52"),
            "estimated_delivery_price": Decimal("82263.52"),
        },
        us_out=1792160429679898,
    )


async def test_raises_deribit_error_on_error_response(deribit: FakeDeribit, transport: HttpTransport) -> None:
    deribit.status = 400
    deribit.payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32602,
            "message": "Invalid params",
            "data": {"reason": "invalid index", "param": "index_name"},
        },
        "usOut": 1792160431137450,
    }

    with pytest.raises(DeribitError) as exc_info:
        await transport.call("public/get_index_price", {"index_name": "xxx_usd"})

    assert (exc_info.value.code, exc_info.value.message) == (-32602, "Invalid params")


async def test_raises_on_non_json_response(deribit: FakeDeribit, transport: HttpTransport) -> None:
    deribit.status = 502
    deribit.payload = "error code: 502"

    with pytest.raises(aiohttp.ContentTypeError):
        await transport.call("public/get_index_price", {"index_name": "btc_usd"})
