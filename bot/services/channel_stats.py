"""Channel statistics service"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from bot.database.connection import get_session
from bot.database.queries import (
    get_channel_stats,
    get_latest_subscriber_count,
    get_daily_activity,
)
from bot.config import Config

logger = logging.getLogger(__name__)


class ChannelStatsService:
    """Service for channel statistics operations"""

    @staticmethod
    async def get_stats(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get channel statistics for a date range

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary containing channel statistics
        """
        async with get_session() as session:
            try:
                # Get basic stats
                stats = await get_channel_stats(
                    session,
                    Config.INSIGHTS_CHANNEL_ID,
                    start_date,
                    end_date,
                )

                # Get latest subscriber count
                subscriber_count = await get_latest_subscriber_count(
                    session,
                    Config.INSIGHTS_CHANNEL_ID,
                )
                stats['subscribers'] = subscriber_count

                # Get daily views for the last 7 days
                daily_data = await get_daily_activity(
                    session,
                    channel_id=Config.INSIGHTS_CHANNEL_ID,
                    days=7,
                )

                # Convert to day-of-week format
                daily_views = {}
                for data in daily_data:
                    day_name = data['date'].strftime('%a')
                    daily_views[day_name] = data.get('views', 0)

                stats['daily_views'] = daily_views

                return stats

            except Exception as e:
                logger.error(f"Error getting channel stats: {e}")
                raise

    @staticmethod
    async def get_all_time_stats() -> Dict[str, Any]:
        """Get all-time channel statistics"""
        return await ChannelStatsService.get_stats()

    @staticmethod
    async def get_month_stats(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get channel statistics for a specific month"""
        return await ChannelStatsService.get_stats(start_date, end_date)
