import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.services import CVEService

scheduler = AsyncIOScheduler()


async def scheduler_tasks():
    cve = await CVEService.create()
    scheduler.add_job(
        cve.calculate_priority,
        trigger="cron",
        hour=16,
        timezone=pytz.utc,
    )
