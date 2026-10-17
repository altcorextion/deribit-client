from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from deribit_client.api.schemas import IndexPriceResponse
from deribit_client.db.repository import IndexPriceRepository
from deribit_client.domain import Ticker


async def get_repository(request: Request) -> AsyncIterator[IndexPriceRepository]:
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield IndexPriceRepository(session)

Repository = Annotated[IndexPriceRepository, Depends(get_repository)]
Limit = Annotated[int, Query(ge=1, le=1000)]
Offset = Annotated[int, Query(ge=0)]

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])


@router.get("")
async def get_prices(
        ticker: Ticker, repository: Repository, limit: Limit = 100, offset: Offset = 0
) -> list[IndexPriceResponse]:
    prices = await repository.get_all(ticker, limit=limit, offset=offset)
    return [IndexPriceResponse.from_domain(price) for price in prices]


@router.get("/latest")
async def get_latest_price(ticker: Ticker, repository: Repository) -> IndexPriceResponse:
    price = await repository.get_latest(ticker)
    if price is None:
        raise HTTPException(status_code=404, detail=f"No prices for {ticker}")
    return IndexPriceResponse.from_domain(price)


@router.get("/filtered")
async def get_prices_by_date(
        ticker: Ticker,
        repository: Repository,
        date_from: Annotated[int | None, Query(alias="from", ge=0)] = None,
        date_to: Annotated[int | None, Query(alias="to", ge=0)] = None,
        limit: Limit = 100,
        offset: Offset = 0,
) -> list[IndexPriceResponse]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=422, detail="'from' must be <= 'to'")
    prices = await repository.get_by_range(
        ticker, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
    return [IndexPriceResponse.from_domain(price) for price in prices]
