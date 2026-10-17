from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from deribit_client.db.models import IndexPriceModel
from deribit_client.domain import IndexPrice, Ticker


class IndexPriceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, price: IndexPrice) -> None:
        statement = (
            insert(IndexPriceModel)
            .values(ticker=price.ticker.value, price=price.price, timestamp=price.timestamp)
            .on_conflict_do_nothing(index_elements=["ticker", "timestamp"])
        )
        await self._session.execute(statement)

    async def get_latest(self, ticker: Ticker) -> IndexPrice | None:
        statement = (
            select(IndexPriceModel)
            .where(IndexPriceModel.ticker == ticker.value)
            .order_by(IndexPriceModel.timestamp.desc())
            .limit(1)
        )
        model = await self._session.scalar(statement)
        return _to_domain(model) if model is not None else None

    async def get_all(self, ticker: Ticker, *, limit: int, offset: int) -> list[IndexPrice]:
        return await self.get_by_range(
            ticker, date_from=None, date_to=None, limit=limit, offset=offset
        )

    async def get_by_range(
            self,
            ticker: Ticker,
            *,
            date_from: int | None,
            date_to: int | None,
            limit: int,
            offset: int,
    ) -> list[IndexPrice]:
        statement = select(IndexPriceModel).where(IndexPriceModel.ticker == ticker.value)
        if date_from is not None:
            statement = statement.where(IndexPriceModel.timestamp >= date_from)
        if date_to is not None:
            statement = statement.where(IndexPriceModel.timestamp <= date_to)
        statement = statement.order_by(IndexPriceModel.timestamp).limit(limit).offset(offset)

        models = await self._session.scalars(statement)
        return [_to_domain(model) for model in models]


def _to_domain(model: IndexPriceModel) -> IndexPrice:
    return IndexPrice(ticker=Ticker(model.ticker), price=model.price, timestamp=model.timestamp)