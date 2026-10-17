import itertools
import json
from dataclasses import dataclass
from decimal import Decimal
from functools import partial
from typing import Any, Protocol

import aiohttp

from deribit_client.deribit.errors import DeribitError


@dataclass(frozen=True, slots=True)
class DeribitResponse:
    result: Any
    us_out: int


class JsonRpcTransport(Protocol):
    async def call(self, method: str, params: dict[str, Any]) -> DeribitResponse: ...


class HttpTransport:
    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self._session = session
        self._url = url
        self._request_ids = itertools.count(1)

    async def call(self, method: str, params: dict[str, Any]) -> DeribitResponse:
        request = {
            "jsonrpc": "2.0",
            "id": next(self._request_ids),
            "method": method,
            "params": params,
        }
        async with self._session.post(self._url, json=request) as response:
            body = await response.json(loads=partial(json.loads, parse_float=Decimal))

        if "error" in body:
            raise DeribitError(body["error"]["code"], body["error"]["message"])
        return DeribitResponse(result=body["result"], us_out=body["usOut"])
