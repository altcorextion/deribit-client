from decimal import Decimal

from sqlalchemy import UniqueConstraint, BigInteger, Identity, String, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IndexPriceModel(Base):
    """ Таблица цен и времени """
    __tablename__ = "index_prices"
    __table_args__ = (
        UniqueConstraint("ticker", "timestamp", name="uq_index_prices_ticker_timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    timestamp: Mapped[int] = mapped_column(BigInteger)
