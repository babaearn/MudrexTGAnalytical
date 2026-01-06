"""Topic statistics service"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from bot.database.connection import get_session
from bot.database.queries import (
    get_topic_stats,
    get_bot_usage_stats,
    get_top_bot_users,
    get_top_symbols,
    get_member_events_count,
    get_daily_activity,
)
from bot.config import Config

logger = logging.getLogger(__name__)


class TopicStatsService:
    """Service for topic statistics operations"""

    @staticmethod
    async def get_stats(
        topic_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get topic statistics for a date range

        Args:
            topic_id: Topic ID
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Dictionary containing topic statistics
        """
        async with get_session() as session:
            try:
                # Get basic topic stats
                stats = await get_topic_stats(session, topic_id, start_date, end_date)

                # Get bot usage stats
                bot_stats = await get_bot_usage_stats(session, topic_id, start_date, end_date)
                stats.update(bot_stats)

                # Calculate average queries per day
                if start_date and end_date:
                    days = (end_date - start_date).days or 1
                elif bot_stats.get('total_queries', 0) > 0:
                    # Estimate based on all-time data
                    days = 30  # Default to 30 days for all-time avg
                else:
                    days = 1

                stats['avg_queries_per_day'] = int(stats.get('total_queries', 0) / days)

                # Get top users
                top_users = await get_top_bot_users(
                    session, topic_id, start_date, end_date, limit=5
                )
                stats['top_users'] = top_users

                # Get top symbols
                top_symbols = await get_top_symbols(
                    session, topic_id, start_date, end_date, limit=5
                )
                stats['top_symbols'] = top_symbols

                # Get daily activity for the last 7 days
                daily_data = await get_daily_activity(
                    session,
                    topic_id=topic_id,
                    days=7,
                )

                # Convert to day-of-week format
                daily_activity = {}
                for data in daily_data:
                    day_name = data['date'].strftime('%a')
                    daily_activity[day_name] = data.get('messages', 0)

                stats['daily_activity'] = daily_activity

                # Get member events
                member_events = await get_member_events_count(
                    session, Config.OFFICIAL_GROUP_ID, start_date, end_date
                )
                stats['members_joined'] = member_events.get('joined', 0)
                stats['members_left'] = member_events.get('left', 0)

                # Add bot username
                stats['bot_username'] = Config.TRACKED_BOT_USERNAME

                return stats

            except Exception as e:
                logger.error(f"Error getting topic stats: {e}")
                raise

    @staticmethod
    async def get_all_topics_summary() -> list[Dict[str, Any]]:
        """Get summary statistics for all configured topics"""
        topics_stats = []

        async with get_session() as session:
            for topic_num, topic_config in Config.TOPICS.items():
                topic_id = topic_config['id']
                topic_name = topic_config['name']

                try:
                    # Get basic stats
                    topic_stats = await get_topic_stats(session, topic_id)
                    bot_stats = await get_bot_usage_stats(session, topic_id)

                    topics_stats.append({
                        'number': topic_num,
                        'id': topic_id,
                        'name': topic_name,
                        'messages': topic_stats.get('total_messages', 0),
                        'queries': bot_stats.get('total_queries', 0),
                    })

                except Exception as e:
                    logger.error(f"Error getting stats for topic {topic_num}: {e}")
                    topics_stats.append({
                        'number': topic_num,
                        'id': topic_id,
                        'name': topic_name,
                        'messages': 0,
                        'queries': 0,
                    })

        return topics_stats

    @staticmethod
    async def get_all_time_stats(topic_id: int) -> Dict[str, Any]:
        """Get all-time topic statistics"""
        return await TopicStatsService.get_stats(topic_id)

    @staticmethod
    async def get_month_stats(
        topic_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get topic statistics for a specific month"""
        return await TopicStatsService.get_stats(topic_id, start_date, end_date)
