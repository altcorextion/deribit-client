from decimal import Decimal
from typing import Self

from pydantic import BaseModel

from deribit_client.domain import IndexPrice, Ticker


class IndexPriceResponse(BaseModel):
    ticker: Ticker
    price: Decimal
    timestamp: int

    @classmethod
    def from_domain(cls, price: IndexPrice) -> Self:
        return cls(ticker=price.ticker, price=price.price, timestamp=price.timestamp)