"""Main bot application."""
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from app.models.base import init_db, close_db, async_session_maker
from app.handlers import (
    registration_router,
    common_router,
    apartments_router,
    admin_router
)
from app.middlewares import DatabaseMiddleware, LoggingMiddleware
from app.utils import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def on_startup():
    """Execute on bot startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")


async def on_shutdown():
    """Execute on bot shutdown."""
    logger.info("Closing database connections...")
    await close_db()
    logger.info("Bot stopped")


async def setup_scheduler(bot: Bot):
    """Setup task scheduler."""
    if not settings.scraper_enabled:
        logger.info("Scraper is disabled")
        return

    scheduler = AsyncIOScheduler()

    # Add scraper job
    async def scraper_job():
        """Scraper job wrapper."""
        from app.scrapers.olx_scraper import run_scraper_task

        async with async_session_maker() as session:
            await run_scraper_task(session, bot)

    scheduler.add_job(
        scraper_job,
        'interval',
        seconds=settings.scraper_interval,
        id='apartment_scraper',
        name='Apartment Scraper',
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started: scraper interval = {settings.scraper_interval}s")

    return scheduler


async def main():
    """Main function to run the bot."""
    logger.info("Starting Chirchiq Kvartira Bot...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    # Register routers
    dp.include_router(registration_router)
    dp.include_router(common_router)
    dp.include_router(apartments_router)
    dp.include_router(admin_router)

    # Setup startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Setup scheduler
    scheduler = await setup_scheduler(bot)

    try:
        logger.info("Bot started successfully! Press Ctrl+C to stop.")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except KeyboardInterrupt:
        logger.info("Received stop signal")
    finally:
        if scheduler:
            scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
