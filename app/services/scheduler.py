from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    def __init__(self, orchestrator) -> None:
        self.orchestrator = orchestrator
        self.scheduler = AsyncIOScheduler(timezone=settings.app_timezone)

    def start(self) -> None:
        if self.scheduler.running:
            return
        self.scheduler.add_job(
            self._safe_generate_and_send,
            CronTrigger(hour=8, minute=0, timezone=settings.app_timezone),
            id="daily-news-briefing",
            replace_existing=True,
        )
        self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _safe_generate_and_send(self) -> None:
        try:
            self.orchestrator.generate_and_archive()
        except Exception as exc:
            logger.exception("Daily generation failed: %s", exc)
