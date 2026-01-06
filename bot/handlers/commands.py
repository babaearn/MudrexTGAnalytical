"""Command handlers for user-facing commands"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.config import Config
from bot.services.channel_stats import ChannelStatsService
from bot.services.topic_stats import TopicStatsService
from bot.services.bot_usage import BotUsageService
from bot.utils.formatters import (
    format_channel_stats,
    format_topic_stats,
    format_topics_list,
    format_leaderboard,
)
from bot.utils.parsers import parse_month, get_topic_number_from_command
from bot.utils.validators import is_admin

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "👋 Welcome to Mudrex Statistics Bot!\n\n"
        "📊 Available Commands:\n\n"
        "📺 Channel Stats:\n"
        "/in - Crypto Insights all-time stats\n"
        "/in jan - January stats\n"
        "/intotal - Complete historical summary\n\n"
        "📋 Topic Stats:\n"
        "/topics - List all configured topics\n"
        "/topic1 - Topic 1 all-time stats\n"
        "/topic1 jan - Topic 1 January stats\n"
        "/t1 - Short alias for /topic1\n\n"
        "📈 Analytics:\n"
        "/topusers - Top bot users (all topics)\n"
        "/topusers topic1 - Top users in topic 1\n"
        "/topusers jan - Top users in January\n"
        "/topcrypto - Most requested symbols\n"
        "/topcrypto topic1 - Top symbols in topic 1\n"
        "/topcrypto jan - Top symbols in January\n\n"
    )

    if is_admin(update):
        welcome_message += (
            "🔧 Admin Commands:\n"
            "/status - Bot health and stats\n"
            "/backup - Export database backup\n"
            "/sync - Force re-sync historical data\n"
            "/report - Generate full report\n\n"
        )

    welcome_message += "Use /help for more detailed information."

    await update.message.reply_text(welcome_message)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = (
        "📖 Mudrex Statistics Bot - Help\n\n"
        "This bot tracks statistics for:\n"
        "• Mudrex Crypto Insights Channel (views, posts, reactions)\n"
        "• Official Mudrex Group Topics (bot engagement, user activity)\n\n"
        "📅 Time Periods:\n"
        "• No argument = All-time stats\n"
        "• jan, feb, mar, etc. = Specific month stats\n"
        "• total = Complete historical summary with trends\n\n"
        "📊 Examples:\n"
        "/in - All-time channel stats\n"
        "/in dec - December channel stats\n"
        "/topic1 - All-time topic 1 stats\n"
        "/topic1 jan - January topic 1 stats\n"
        "/topusers - All-time top users\n"
        "/topusers jan - January top users\n"
        "/topcrypto topic1 - Top symbols in topic 1\n\n"
        "💡 Tip: Use short aliases like /t1 instead of /topic1"
    )

    await update.message.reply_text(help_message)


async def cmd_in(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /in command - Crypto Insights channel stats

    Usage:
        /in - All-time stats
        /in jan - January stats
        /in dec - December stats
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        # Parse argument for month
        arg = context.args[0] if context.args else None
        period = "All Time"
        start_date = None
        end_date = None

        if arg and arg.lower() not in ['total']:
            try:
                start_date, end_date = parse_month(arg)
                period = start_date.strftime("%B %Y")
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid month: {arg}\n"
                    "Use: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec"
                )
                return

        # Get stats
        await update.message.reply_text("📊 Fetching channel statistics...")

        stats = await ChannelStatsService.get_stats(start_date, end_date)
        message = format_channel_stats(stats, period)

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /in command: {e}")
        await update.message.reply_text(f"❌ Error fetching statistics: {str(e)}")


async def cmd_intotal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /intotal command - Complete historical channel summary"""
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text("📊 Generating complete historical summary...")

        stats = await ChannelStatsService.get_all_time_stats()
        message = format_channel_stats(stats, "Complete History")

        # Add additional insights
        message += "\n\n📈 INSIGHTS:\n"
        if stats.get('total_posts', 0) > 0:
            message += f"└─ Content Consistency: {stats['total_posts']} posts published\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /intotal command: {e}")
        await update.message.reply_text(f"❌ Error fetching statistics: {str(e)}")


async def cmd_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /topics command - List all configured topics"""
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text("📋 Fetching topics...")

        topics_stats = await TopicStatsService.get_all_topics_summary()
        message = format_topics_list(topics_stats)

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /topics command: {e}")
        await update.message.reply_text(f"❌ Error fetching topics: {str(e)}")


async def cmd_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /topic<n> and /t<n> commands - Topic stats

    Usage:
        /topic1 - All-time stats for topic 1
        /topic1 jan - January stats for topic 1
        /t1 - Short alias for /topic1
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        # Extract topic number from command
        command = update.message.text.split()[0][1:]  # Remove leading /
        topic_num = get_topic_number_from_command(command)

        if not topic_num:
            await update.message.reply_text("❌ Invalid command. Use /topic1, /topic2, etc.")
            return

        # Get topic configuration
        topic_config = Config.get_topic_by_number(topic_num)
        if not topic_config:
            await update.message.reply_text(f"❌ Topic {topic_num} is not configured.")
            return

        topic_id = topic_config['id']
        topic_name = topic_config['name']

        # Parse argument for month
        arg = context.args[0] if context.args else None
        period = "All Time"
        start_date = None
        end_date = None

        if arg and arg.lower() not in ['total']:
            try:
                start_date, end_date = parse_month(arg)
                period = start_date.strftime("%B %Y")
            except ValueError:
                await update.message.reply_text(
                    f"❌ Invalid month: {arg}\n"
                    "Use: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec"
                )
                return

        # Get stats
        await update.message.reply_text(f"📊 Fetching {topic_name} statistics...")

        stats = await TopicStatsService.get_stats(topic_id, start_date, end_date)
        message = format_topic_stats(stats, topic_name, period)

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /topic command: {e}")
        await update.message.reply_text(f"❌ Error fetching statistics: {str(e)}")


async def cmd_topusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /topusers command - Top bot users leaderboard

    Usage:
        /topusers - All-time top users (all topics)
        /topusers topic1 - Top users in topic 1
        /topusers jan - Top users in January
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        # Parse arguments
        arg = context.args[0] if context.args else None
        topic_id = None
        start_date = None
        end_date = None
        period = "All Time"

        if arg:
            # Check if it's a topic filter
            topic_num = get_topic_number_from_command(arg)
            if topic_num:
                topic_config = Config.get_topic_by_number(topic_num)
                if topic_config:
                    topic_id = topic_config['id']
                    period = f"{topic_config['name']} - All Time"
            else:
                # Try parsing as month
                try:
                    start_date, end_date = parse_month(arg)
                    period = start_date.strftime("%B %Y")
                except ValueError:
                    await update.message.reply_text(
                        f"❌ Invalid argument: {arg}\n"
                        "Use: topic1, topic2, jan, feb, mar, etc."
                    )
                    return

        # Get leaderboard data
        await update.message.reply_text("🏆 Fetching top users...")

        users = await BotUsageService.get_top_users(topic_id, start_date, end_date, limit=10)

        if not users:
            await update.message.reply_text("❌ No user data available for this period.")
            return

        # Format leaderboard
        leaderboard_data = [
            {'name': user['name'], 'value': user['queries']}
            for user in users
        ]

        title = f"TOP BOT USERS - {period.upper()}"
        message = format_leaderboard(leaderboard_data, title, "Queries")

        # Add total count
        message += f"\nTotal Unique Users: {users[0].get('total_count', len(users))}"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /topusers command: {e}")
        await update.message.reply_text(f"❌ Error fetching top users: {str(e)}")


async def cmd_topcrypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /topcrypto command - Most requested symbols

    Usage:
        /topcrypto - All-time top symbols (all topics)
        /topcrypto topic1 - Top symbols in topic 1
        /topcrypto jan - Top symbols in January
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        # Parse arguments
        arg = context.args[0] if context.args else None
        topic_id = None
        start_date = None
        end_date = None
        period = "All Time"

        if arg:
            # Check if it's a topic filter
            topic_num = get_topic_number_from_command(arg)
            if topic_num:
                topic_config = Config.get_topic_by_number(topic_num)
                if topic_config:
                    topic_id = topic_config['id']
                    period = f"{topic_config['name']} - All Time"
            else:
                # Try parsing as month
                try:
                    start_date, end_date = parse_month(arg)
                    period = start_date.strftime("%B %Y")
                except ValueError:
                    await update.message.reply_text(
                        f"❌ Invalid argument: {arg}\n"
                        "Use: topic1, topic2, jan, feb, mar, etc."
                    )
                    return

        # Get top symbols
        await update.message.reply_text("🔥 Fetching top symbols...")

        symbols, total_queries = await BotUsageService.get_top_crypto_symbols(
            topic_id, start_date, end_date, limit=10
        )

        if not symbols:
            await update.message.reply_text("❌ No symbol data available for this period.")
            return

        # Format leaderboard
        leaderboard_data = [
            {
                'name': symbol['symbol'],
                'value': symbol['count'],
            }
            for symbol in symbols
        ]

        title = f"TOP REQUESTED SYMBOLS - {period.upper()}"
        message = format_leaderboard(
            leaderboard_data,
            title,
            "Queries",
            show_percentage=True,
            total=total_queries
        )

        # Add total count
        message += f"\nTotal Queries: {total_queries}"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /topcrypto command: {e}")
        await update.message.reply_text(f"❌ Error fetching top symbols: {str(e)}")


def setup_commands(application):
    """
    Set up all user-facing command handlers

    Args:
        application: Telegram application instance
    """
    # Basic commands
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))

    # Channel stats commands
    application.add_handler(CommandHandler("in", cmd_in))
    application.add_handler(CommandHandler("intotal", cmd_intotal))

    # Topic commands
    application.add_handler(CommandHandler("topics", cmd_topics))

    # Dynamic topic handlers - topic1, topic2, ..., topic10, t1, t2, ..., t10
    for i in range(1, 11):
        application.add_handler(CommandHandler(f"topic{i}", cmd_topic))
        application.add_handler(CommandHandler(f"t{i}", cmd_topic))

    # Analytics commands
    application.add_handler(CommandHandler("topusers", cmd_topusers))
    application.add_handler(CommandHandler("topcrypto", cmd_topcrypto))

    logger.info("Commands set up successfully")
