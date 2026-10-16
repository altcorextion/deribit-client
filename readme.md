# Deribit client

## Build


## Design decisions

### Prepares

Начал с просмотра документации:
- есть тестовое окружение, ручки: https://test.deribit.com/api/v2 и wss://test.deribit.com/ws/api/v2
- основной протокол json-rpc, клиенты по webSocket и HTTP
- можно обращаться с ip лимитом без api token

Документация настаивает на использовании websockets, для текущей задачи он не так полезен (нет торга, обращения редкие).
Позже в [статье best-practices с market data](https://docs.deribit.com/articles/market-data-collection-best-practices) 
нашёл подтверждение использовать простой http (rest)

Интересующая ручка Deribit API Market Data: `public/get_index_price` с обязательным `index_name` - `btc_usd` или `eth_usd`
(либо `get_index_price_names` по документации)

Предварительные три ручки (контракт) для API клиента (обязательный query `ticker`):
- **GET** `/api/v1/prices?ticker=<index_name>` - много записей, с пагинацией (`&limit=&offset=`)
- **GET** `/api/v1/prices/latest?ticker=<index_name>` - одна запись (не значение)
- **GET** `/api/v1/prices/filtered?ticker=<index_name>` - много записей, если диапазон (`&from=&to=`)

Время привычнее держать в timestampz, для формата `YYYY-MM-DD` использовать парсинг обёртку

Понятия и архитектура клиента с биржей знакома [по похожему проекту] (https://github.com/altcorextion/markowitz-nn-portfolio) (MOEX),
буду ссылаться на части кода и шаблоны сборки

Начну с базы postgres, миграций, билда

### Postgres

Postgres разворачивается в docker, с клиентом связь через общую сеть. Сборка для удобства через Makefile

Таблицы (схемы) описываются через sqlalchemy, миграции через alembic
