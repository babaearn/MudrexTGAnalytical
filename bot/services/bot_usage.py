"""Bot usage tracking service"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from bot.database.connection import get_session
from bot.database.queries import (
    get_top_bot_users,
    get_top_symbols,
    get_bot_usage_stats,
)

logger = logging.getLogger(__name__)


class BotUsageService:
    """Service for bot usage analytics"""

    @staticmethod
    async def get_top_users(
        topic_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top bot users

        Args:
            topic_id: Filter by topic (None for all topics)
            start_date: Start of date range
            end_date: End of date range
            limit: Number of users to return

        Returns:
            List of top users with query counts
        """
        async with get_session() as session:
            try:
                users = await get_top_bot_users(
                    session, topic_id, start_date, end_date, limit
                )

                # Add total count for display
                if users:
                    # Get total unique users
                    stats = await get_bot_usage_stats(session, topic_id, start_date, end_date)
                    total_users = stats.get('unique_users', len(users))

                    for user in users:
                        user['total_count'] = total_users

                return users

            except Exception as e:
                logger.error(f"Error getting top users: {e}")
                raise

    @staticmethod
    async def get_top_crypto_symbols(
        topic_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get most requested crypto symbols

        Args:
            topic_id: Filter by topic (None for all topics)
            start_date: Start of date range
            end_date: End of date range
            limit: Number of symbols to return

        Returns:
            Tuple of (list of top symbols, total queries)
        """
        async with get_session() as session:
            try:
                symbols = await get_top_symbols(
                    session, topic_id, start_date, end_date, limit
                )

                # Get total queries for percentage calculation
                stats = await get_bot_usage_stats(session, topic_id, start_date, end_date)
                total_queries = stats.get('total_queries', 0)

                # Calculate percentages
                for symbol in symbols:
                    if total_queries > 0:
                        symbol['percentage'] = (symbol['count'] / total_queries) * 100
                    else:
                        symbol['percentage'] = 0

                return symbols, total_queries

            except Exception as e:
                logger.error(f"Error getting top symbols: {e}")
                raise

    @staticmethod
    async def get_leaderboard_data(
        metric: str,  # 'users' or 'symbols'
        topic_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get leaderboard data formatted for display

        Args:
            metric: Type of leaderboard ('users' or 'symbols')
            topic_id: Filter by topic
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Tuple of (leaderboard data, metadata)
        """
        if metric == 'users':
            users = await BotUsageService.get_top_users(
                topic_id, start_date, end_date, limit=10
            )

            # Format for leaderboard display
            leaderboard = [
                {
                    'name': user['name'],
                    'value': user['queries'],
                }
                for user in users
            ]

            metadata = {
                'total_users': users[0]['total_count'] if users else 0,
            }

            return leaderboard, metadata

        elif metric == 'symbols':
            symbols, total_queries = await BotUsageService.get_top_crypto_symbols(
                topic_id, start_date, end_date, limit=10
            )

            # Format for leaderboard display
            leaderboard = [
                {
                    'name': symbol['symbol'],
                    'value': symbol['count'],
                    'percentage': symbol.get('percentage', 0),
                }
                for symbol in symbols
            ]

            metadata = {
                'total_queries': total_queries,
            }

            return leaderboard, metadata

        else:
            raise ValueError(f"Invalid metric: {metric}")
