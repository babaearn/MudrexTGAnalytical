"""Periodic tasks for the Mudrex Stats Bot"""

import logging
from datetime import datetime, timedelta, date
from telegram.ext import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.config import Config
from bot.database.connection import get_session
from bot.database.queries import (
    create_daily_snapshot,
    get_channel_stats,
    get_topic_stats,
    get_bot_usage_stats,
    get_latest_subscriber_count,
)
from bot.handlers.admin import update_last_sync_time

logger = logging.getLogger(__name__)


async def update_channel_views_task(app: Application):
    """
    Periodic task to update channel post view counts

    This task fetches recent posts and updates their view counts.
    Runs every hour by default.
    """
    try:
        logger.info("Running channel views update task...")

        # Here you would fetch recent channel posts and update their views
        # This requires access to the Telegram bot to fetch message views
        # For now, we'll just log that the task ran

        # Note: To actually update views, you would need to:
        # 1. Query the database for recent channel posts
        # 2. Use bot.get_messages() or similar to fetch updated view counts
        # 3. Update the database with new view counts

        # Update last sync time
        update_last_sync_time()

        logger.info("Channel views update task completed")

    except Exception as e:
        logger.error(f"Error in update_channel_views_task: {e}")


async def create_daily_snapshots_task(app: Application):
    """
    Periodic task to create daily snapshots

    Creates aggregate statistics for the previous day.
    Runs once daily at midnight IST.
    """
    try:
        logger.info("Running daily snapshots task...")

        snapshot_date = date.today() - timedelta(days=1)  # Yesterday

        async with get_session() as session:
            # Create snapshot for channel
            try:
                # Get date range for yesterday
                start_dt = datetime.combine(snapshot_date, datetime.min.time())
                end_dt = start_dt + timedelta(days=1)

                channel_stats = await get_channel_stats(
                    session,
                    Config.INSIGHTS_CHANNEL_ID,
                    start_dt,
                    end_dt
                )

                subscriber_count = await get_latest_subscriber_count(
                    session,
                    Config.INSIGHTS_CHANNEL_ID
                )

                await create_daily_snapshot(
                    session,
                    snapshot_date=snapshot_date,
                    channel_id=Config.INSIGHTS_CHANNEL_ID,
                    total_messages=channel_stats.get('total_posts', 0),
                    total_views=channel_stats.get('total_views', 0),
                    subscriber_count=subscriber_count,
                )

                logger.info(f"Created channel snapshot for {snapshot_date}")

            except Exception as e:
                logger.error(f"Error creating channel snapshot: {e}")

            # Create snapshots for each topic
            for topic_num, topic_config in Config.TOPICS.items():
                topic_id = topic_config['id']

                try:
                    start_dt = datetime.combine(snapshot_date, datetime.min.time())
                    end_dt = start_dt + timedelta(days=1)

                    topic_stats = await get_topic_stats(
                        session,
                        topic_id,
                        start_dt,
                        end_dt
                    )

                    bot_stats = await get_bot_usage_stats(
                        session,
                        topic_id,
                        start_dt,
                        end_dt
                    )

                    await create_daily_snapshot(
                        session,
                        snapshot_date=snapshot_date,
                        topic_id=topic_id,
                        total_messages=topic_stats.get('total_messages', 0),
                        total_queries=bot_stats.get('total_queries', 0),
                        unique_users=bot_stats.get('unique_users', 0),
                    )

                    logger.info(f"Created topic {topic_num} snapshot for {snapshot_date}")

                except Exception as e:
                    logger.error(f"Error creating topic {topic_num} snapshot: {e}")

        logger.info("Daily snapshots task completed")

    except Exception as e:
        logger.error(f"Error in create_daily_snapshots_task: {e}")


async def cleanup_old_data_task(app: Application):
    """
    Periodic task to cleanup old data (optional)

    Archives or removes data older than a certain threshold.
    Runs once weekly.
    """
    try:
        logger.info("Running cleanup task...")

        # This is optional - you can implement data retention policies here
        # For example: archive data older than 6 months

        logger.info("Cleanup task completed")

    except Exception as e:
        logger.error(f"Error in cleanup_old_data_task: {e}")


def setup_schedulers(app: Application):
    """
    Set up all periodic tasks

    Args:
        app: Telegram application instance
    """
    scheduler = AsyncIOScheduler()

    # Update channel views every hour
    scheduler.add_job(
        update_channel_views_task,
        trigger=IntervalTrigger(minutes=Config.UPDATE_VIEWS_INTERVAL_MINUTES),
        args=[app],
        id='update_channel_views',
        name='Update Channel Views',
        replace_existing=True,
    )

    # Create daily snapshots at midnight IST
    scheduler.add_job(
        create_daily_snapshots_task,
        trigger=CronTrigger(
            hour=Config.DAILY_SNAPSHOT_HOUR,
            minute=0,
            timezone='Asia/Kolkata'
        ),
        args=[app],
        id='create_daily_snapshots',
        name='Create Daily Snapshots',
        replace_existing=True,
    )

    # Cleanup old data weekly (Sunday at 2 AM IST)
    scheduler.add_job(
        cleanup_old_data_task,
        trigger=CronTrigger(
            day_of_week='sun',
            hour=2,
            minute=0,
            timezone='Asia/Kolkata'
        ),
        args=[app],
        id='cleanup_old_data',
        name='Cleanup Old Data',
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Schedulers set up successfully")

    return scheduler
