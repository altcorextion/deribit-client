from deribit_client.deribit.transport import JsonRpcTransport
from deribit_client.domain import Ticker, IndexPrice


class DeribitClient:
    def __init__(self, transport: JsonRpcTransport) -> None:
        self._transport = transport

    async def get_index_price(self, ticker: Ticker) -> IndexPrice:
        response = await self._transport.call(
            "public/get_index_price", {"index_name": ticker.value}
        )

        return IndexPrice(
            ticker=ticker,
            price=response.result["index_price"],
            timestamp=response.us_out // 1_000_000 # без микросекунд
        )