import os
from celery import Celery
from celery.schedules import crontab
from app.config import settings

broker_url = settings.celery_broker_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
backend_url = settings.celery_result_backend or os.environ.get("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery(
    "privascan",
    broker=broker_url,
    backend=backend_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=120,
    task_time_limit=180,
    timezone="UTC",
    enable_utc=True,
    beat_schedule_filename="/tmp/celerybeat-schedule",
)

celery_app.conf.beat_schedule = {
    # Rescore all 14 curated protocols every 6 hours
    "rescore-all-curated": {
        "task": "app.workers.tasks.rescore_all_curated",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Rescore watchlist contracts daily at 2am UTC
    "rescore-watchlist": {
        "task": "app.workers.tasks.rescore_watchlist_addresses",
        "schedule": crontab(minute=0, hour=2),
    },
    # Download OFAC consolidated list daily at 3am UTC
    "refresh-ofac-list": {
        "task": "app.workers.tasks.refresh_ofac_list",
        "schedule": crontab(minute=0, hour=3),
    },
    # Check for OFAC delistings at 3:30am UTC (30min after refresh)
    "check-ofac-delisting": {
        "task": "app.workers.tasks.check_ofac_delisting",
        "schedule": crontab(minute=30, hour=3),
    },
    # Pull DeFiHackLabs weekly on Sunday at 4am UTC
    "refresh-exploit-db": {
        "task": "app.workers.tasks.refresh_exploit_db",
        "schedule": crontab(minute=0, hour=4, day_of_week=0),
    },
}
