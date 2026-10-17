from celery import Celery

from deribit_client.config import RedisSettings
from deribit_client.worker.tasks import collect_index_prices


def create_celery_app(settings: RedisSettings) -> Celery:
    app = Celery("deribit_client", broker=settings.url)
    app.task(name="collect_index_prices")(collect_index_prices)
    app.conf.beat_schedule = {
        "collect-index-prices-every-minute": {
            "task": "collect_index_prices",
            "schedule": 60.0,
            "options": {"expires": 60},
        },
    }
    return app


app = create_celery_app(RedisSettings())