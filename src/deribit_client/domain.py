from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class Ticker(StrEnum):
    BTC_USD = "btc_usd"
    ETH_USD = "eth_usd"


@dataclass(frozen=True, slots=True)
class IndexPrice:
    ticker: Ticker
    price: Decimal
    timestamp: int
