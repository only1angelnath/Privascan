from celery.schedules import crontab
from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "rescore-curated": {
        "task": "app.workers.tasks.rescore_all_curated",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "rescore-watchlist": {
        "task": "app.workers.tasks.rescore_watchlist_addresses",
        "schedule": crontab(minute=0, hour=2),
    },
    "refresh-ofac": {
        "task": "app.workers.tasks.refresh_ofac_list",
        "schedule": crontab(minute=0, hour=3),
    },
    "check-ofac-resolutions": {
        "task": "app.workers.tasks.check_ofac_delisting",
        "schedule": crontab(minute=30, hour=3),
    },
    "refresh-exploits": {
        "task": "app.workers.tasks.refresh_exploit_db",
        "schedule": crontab(minute=0, hour=4, day_of_week=0),
    },
}
