import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.application.services import CVEService

scheduler = AsyncIOScheduler()


async def scheduler_tasks():
    scheduler.add_job(
        CVEService.generate_priority,
        trigger="cron",
        hour=16,
        timezone=pytz.utc,
    )
