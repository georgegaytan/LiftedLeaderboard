from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    return scheduler


