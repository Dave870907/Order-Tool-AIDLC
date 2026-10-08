import logging
from datetime import datetime
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)


class DeadlineScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        self._scheduler.start()
        logger.info("Deadline scheduler started")

    def schedule(self, session_id: str, deadline: datetime, callback: Callable) -> None:
        job_id = f"deadline_{session_id}"
        self._scheduler.add_job(
            callback,
            trigger="date",
            run_date=deadline,
            id=job_id,
            replace_existing=True,
        )
        logger.info("Scheduled deadline for session %s at %s", session_id, deadline)

    def cancel(self, session_id: str) -> None:
        job_id = f"deadline_{session_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info("Cancelled deadline job for session %s", session_id)
