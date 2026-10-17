# Deribit client


## Build

1. Склонировать проект
```bash
git clone https://github.com/altcorextion/deribit-client.git && cd deribit-client
```

2. Настройка окружения (скопировать и установить `DB_PASS`)
```bash
cp .env.example .env
```

Скачать зависимости:
```bash
uv sync
```

3. Запуск:
```bash
make up
```

4. Миграции:
```bash
make migrate-up
```


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

Время привычнее держать в timestamptz, для формата `YYYY-MM-DD` использовать парсинг обёртку

Понятия и архитектура клиента с биржей знакома [по похожему проекту](https://github.com/altcorextion/markowitz-nn-portfolio) (MOEX),
буду ссылаться на части кода и шаблоны сборки

Начну с базы postgres, миграций, билда


### Postgres

Postgres разворачивается в docker, с клиентом связь через общую сеть. Сборка для удобства через Makefile

Таблицы (схемы) описываются через sqlalchemy, миграции через [alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

Типы и поля в схеме:
- `id` BIGINT identity # приватный, uuid в данном случае дороже и бесполезен
- `ticker` VARCHAR(16) # `index_name` в deribit API
- `price` NUMERIC(20, 8) # не теряет значения, при операциях, округлениях
- `timestamp` BIGINT # по тз, `usOut` в deribit API

Так же логично добавить индекс UNIQUE для полей `ticker` и `timestamp`. Postgres добавит индекс, что ускорит обращение 
к полям и сортирует их (чтение с конца самое быстрое). Пары используются во всех ручках, в том числе при запросе с фильтрацией

Запись через `INSERT ... ON CONFLICT DO NOTHING` не упадёт на существующей записи. При массовом чтении данных с deribit API
(в будущем) можно запускать задачи регулярного чтения


### Client

Две domain сущности (класса) `Ticker` и `IndexPrice` в качестве сообщений бизнес-логики. 
Транспорт (deribit API) с сообщением `DerebitResponse` и интерфейсы `JsonRpcTransport` и `HttpTransport` без привязки к логике выполнения.
Клиент с асинхронным методом получения данных (`IndexPrice`)
Обработка rpc ошибок deribit API (`DeribitError`)

Тесты:
- клиента (json/http)
  - получение `index_price` по тикеру
  - конвертация UNIX timestamp в секунды
- обработки запросов (json-rpc)
  - стандартный запрос (200)
  - итерация запросов
  - корректного ответа
  - возврата ошибки при ошибке в запросе
  - возврата ошибки при отправке non-json объекта

Репозиторий с `AssyncSession`, коммит транзакции наравне с вызовом

Тесты:
- запись актуального значения
- игнорирование дубликатов
- фильтрация и сортировка вывода
- пагинация
- границы включительно
- граница открыта
- Decimal