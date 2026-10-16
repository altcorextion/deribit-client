from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class DeribitResponse:
    result: Any
    us_out: int


class JsonRpcTransport(Protocol):
    async def call(self, method: str, params: dict[str, Any]) -> DeribitResponse: ...
