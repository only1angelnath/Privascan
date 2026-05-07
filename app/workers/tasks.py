from app.workers.celery_app import celery_app
import structlog

log = structlog.get_logger()


@celery_app.task(name="app.workers.tasks.rescore_all_curated", bind=True)
def rescore_all_curated(self):
    log.info("task.rescore_all_curated.start")
    return {"status": "stub"}


@celery_app.task(name="app.workers.tasks.rescore_watchlist_addresses", bind=True)
def rescore_watchlist_addresses(self):
    log.info("task.rescore_watchlist.start")
    return {"status": "stub"}


@celery_app.task(name="app.workers.tasks.refresh_ofac_list", bind=True)
def refresh_ofac_list(self):
    log.info("task.refresh_ofac.start")
    return {"status": "stub"}


@celery_app.task(name="app.workers.tasks.check_ofac_delisting", bind=True)
def check_ofac_delisting(self):
    log.info("task.check_ofac_delisting.start")
    return {"status": "stub"}


@celery_app.task(name="app.workers.tasks.refresh_exploit_db", bind=True)
def refresh_exploit_db(self):
    log.info("task.refresh_exploit_db.start")
    return {"status": "stub"}


@celery_app.task(name="app.workers.tasks.score_contract", bind=True, max_retries=2)
def score_contract(self, address: str, chain_id: int, scan_type: str = "community"):
    log.info("task.score_contract.start", address=address, chain_id=chain_id)
    return {"status": "stub", "address": address}


@celery_app.task(name="app.workers.tasks.score_ecosystem", bind=True, max_retries=2)
def score_ecosystem(self, protocol_id: str, scan_type: str = "curated"):
    log.info("task.score_ecosystem.start", protocol_id=protocol_id)
    return {"status": "stub", "protocol_id": protocol_id}
