"""Export and backup service"""

import logging
import io
from datetime import datetime
from typing import Optional
import pandas as pd

from bot.database.connection import get_session
from bot.database.models import (
    ChannelPost,
    TopicMessage,
    BotUsage,
    MemberEvent,
    DailySnapshot,
    ChannelSubscriber,
)
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ExportService:
    """Service for data export and backup operations"""

    @staticmethod
    async def export_to_csv(table_name: str) -> Optional[bytes]:
        """
        Export a table to CSV format

        Args:
            table_name: Name of the table to export

        Returns:
            CSV data as bytes or None if error
        """
        async with get_session() as session:
            try:
                # Map table names to models
                table_map = {
                    'channel_posts': ChannelPost,
                    'topic_messages': TopicMessage,
                    'bot_usage': BotUsage,
                    'member_events': MemberEvent,
                    'daily_snapshots': DailySnapshot,
                    'channel_subscribers': ChannelSubscriber,
                }

                model = table_map.get(table_name)
                if not model:
                    logger.error(f"Unknown table: {table_name}")
                    return None

                # Fetch all records
                stmt = select(model)
                result = await session.execute(stmt)
                records = result.scalars().all()

                if not records:
                    logger.warning(f"No data found in {table_name}")
                    return None

                # Convert to list of dicts
                data = []
                for record in records:
                    row = {}
                    for column in model.__table__.columns:
                        value = getattr(record, column.name)
                        # Convert datetime objects to strings
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row[column.name] = value
                    data.append(row)

                # Create DataFrame and export to CSV
                df = pd.DataFrame(data)
                csv_buffer = io.BytesIO()
                df.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)

                return csv_buffer.getvalue()

            except Exception as e:
                logger.error(f"Error exporting {table_name} to CSV: {e}")
                return None

    @staticmethod
    async def create_full_backup() -> dict[str, bytes]:
        """
        Create a full database backup as multiple CSV files

        Returns:
            Dictionary mapping table names to CSV data
        """
        tables = [
            'channel_posts',
            'topic_messages',
            'bot_usage',
            'member_events',
            'daily_snapshots',
            'channel_subscribers',
        ]

        backup = {}

        for table in tables:
            logger.info(f"Exporting {table}...")
            csv_data = await ExportService.export_to_csv(table)

            if csv_data:
                backup[table] = csv_data
                logger.info(f"Exported {table} successfully")
            else:
                logger.warning(f"Skipped {table} (no data or error)")

        return backup

    @staticmethod
    async def generate_summary_report() -> str:
        """
        Generate a text summary report of all statistics

        Returns:
            Formatted text report
        """
        from bot.services.channel_stats import ChannelStatsService
        from bot.services.topic_stats import TopicStatsService
        from bot.services.bot_usage import BotUsageService
        from bot.utils.formatters import format_number

        report = []
        report.append("=" * 60)
        report.append("MUDREX TELEGRAM STATISTICS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        report.append("=" * 60)
        report.append("")

        try:
            # Channel stats
            report.append("📊 CRYPTO INSIGHTS CHANNEL")
            report.append("-" * 60)
            channel_stats = await ChannelStatsService.get_all_time_stats()
            report.append(f"Total Posts: {format_number(channel_stats.get('total_posts', 0))}")
            report.append(f"Total Views: {format_number(channel_stats.get('total_views', 0))}")
            report.append(f"Avg Views/Post: {format_number(int(channel_stats.get('avg_views_per_post', 0)))}")
            report.append(f"Total Forwards: {format_number(channel_stats.get('total_forwards', 0))}")
            report.append(f"Total Reactions: {format_number(channel_stats.get('total_reactions', 0))}")
            report.append(f"Subscribers: {format_number(channel_stats.get('subscribers', 0))}")
            report.append("")

            # Topic stats
            from bot.config import Config

            for topic_num, topic_config in Config.TOPICS.items():
                topic_id = topic_config['id']
                topic_name = topic_config['name']

                report.append(f"📊 TOPIC {topic_num}: {topic_name.upper()}")
                report.append("-" * 60)

                topic_stats = await TopicStatsService.get_all_time_stats(topic_id)
                report.append(f"Total Messages: {format_number(topic_stats.get('total_messages', 0))}")
                report.append(f"Bot Queries: {format_number(topic_stats.get('total_queries', 0))}")
                report.append(f"Unique Users: {format_number(topic_stats.get('unique_users', 0))}")
                report.append(f"Avg Queries/Day: {topic_stats.get('avg_queries_per_day', 0)}")

                # Top users
                if topic_stats.get('top_users'):
                    report.append("\nTop Users:")
                    for i, user in enumerate(topic_stats['top_users'][:5], 1):
                        report.append(f"  {i}. {user['name']} - {user['queries']} queries")

                # Top symbols
                if topic_stats.get('top_symbols'):
                    report.append("\nTop Symbols:")
                    for i, symbol in enumerate(topic_stats['top_symbols'][:5], 1):
                        report.append(f"  {i}. {symbol['symbol']} - {symbol['count']} requests")

                report.append("")

            # Overall leaderboards
            report.append("🏆 OVERALL TOP USERS (ALL TOPICS)")
            report.append("-" * 60)
            top_users = await BotUsageService.get_top_users(limit=10)
            for i, user in enumerate(top_users, 1):
                report.append(f"{i}. {user['name']} - {user['queries']} queries")
            report.append("")

            report.append("🔥 OVERALL TOP SYMBOLS (ALL TOPICS)")
            report.append("-" * 60)
            top_symbols, total = await BotUsageService.get_top_crypto_symbols(limit=10)
            for i, symbol in enumerate(top_symbols, 1):
                pct = (symbol['count'] / total * 100) if total > 0 else 0
                report.append(f"{i}. {symbol['symbol']} - {symbol['count']} ({pct:.1f}%)")
            report.append("")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            report.append(f"ERROR: {str(e)}")

        report.append("=" * 60)
        report.append("END OF REPORT")
        report.append("=" * 60)

        return "\n".join(report)
