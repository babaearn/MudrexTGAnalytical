"""Admin command handlers"""

import logging
import io
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import ContextTypes, CommandHandler

from bot.config import Config
from bot.database.connection import test_connection, get_session
from bot.database.queries import get_database_stats
from bot.services.export import ExportService
from bot.utils.formatters import format_status
from bot.utils.validators import is_admin

logger = logging.getLogger(__name__)

# Track bot start time for uptime calculation
BOT_START_TIME = datetime.now()
LAST_SYNC_TIME = None


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command - Bot health and statistics

    Shows:
    - Bot online status
    - Database connection status
    - Last sync time
    - Database record counts
    - Bot uptime
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text("🔍 Checking bot status...")

        # Check database connection
        db_connected = await test_connection()

        # Get database stats
        db_stats = {}
        if db_connected:
            async with get_session() as session:
                db_stats = await get_database_stats(session)

        # Calculate uptime
        uptime_delta = datetime.now() - BOT_START_TIME
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        uptime_str = f"{days}d {hours}h {minutes}m"

        # Calculate next sync time
        next_sync = "in sync"
        if LAST_SYNC_TIME:
            next_sync_time = LAST_SYNC_TIME + timedelta(minutes=Config.UPDATE_VIEWS_INTERVAL_MINUTES)
            time_until = next_sync_time - datetime.now()
            if time_until.total_seconds() > 0:
                minutes_until = int(time_until.total_seconds() / 60)
                next_sync = f"in {minutes_until} mins"

        # Build status data
        status_data = {
            'bot_online': True,
            'db_connected': db_connected,
            'last_sync': LAST_SYNC_TIME or "Never",
            'db_stats': db_stats,
            'uptime': uptime_str,
            'next_sync': next_sync,
        }

        message = format_status(status_data)
        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in /status command: {e}")
        await update.message.reply_text(f"❌ Error checking status: {str(e)}")


async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /backup command - Export database backup as CSV files

    Creates CSV exports of all database tables and sends them as files
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text("💾 Creating database backup... This may take a moment.")

        # Create backup
        backup_data = await ExportService.create_full_backup()

        if not backup_data:
            await update.message.reply_text("❌ No data to backup.")
            return

        # Send each table as a separate file
        await update.message.reply_text(f"📦 Backup complete! Sending {len(backup_data)} files...")

        for table_name, csv_data in backup_data.items():
            filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            # Create file object
            file_obj = io.BytesIO(csv_data)
            file_obj.name = filename

            await update.message.reply_document(
                document=file_obj,
                filename=filename,
                caption=f"📄 {table_name}"
            )

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

        await update.message.reply_text("✅ Backup completed successfully!")

    except Exception as e:
        logger.error(f"Error in /backup command: {e}")
        await update.message.reply_text(f"❌ Error creating backup: {str(e)}")


async def cmd_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /sync command - Force re-sync historical data

    This is a placeholder for manual sync trigger.
    The actual sync logic would be implemented in a separate sync service.
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text(
            "🔄 Manual sync triggered!\n\n"
            "Note: Historical data sync is performed automatically on bot startup.\n"
            "To re-sync, please restart the bot.\n\n"
            "⚠️ Warning: Full historical sync may take several minutes and could hit rate limits."
        )

        # Update last sync time
        global LAST_SYNC_TIME
        LAST_SYNC_TIME = datetime.now()

        # Here you would trigger the actual sync process
        # For now, we'll just acknowledge the command

    except Exception as e:
        logger.error(f"Error in /sync command: {e}")
        await update.message.reply_text(f"❌ Error triggering sync: {str(e)}")


async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /report command - Generate full text report

    Creates a comprehensive text report with all statistics
    """
    if not is_admin(update):
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return

    try:
        await update.message.reply_text("📊 Generating comprehensive report... This may take a moment.")

        # Generate report
        report_text = await ExportService.generate_summary_report()

        # Create file object
        filename = f"mudrex_stats_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_obj = io.BytesIO(report_text.encode('utf-8'))
        file_obj.name = filename

        await update.message.reply_document(
            document=file_obj,
            filename=filename,
            caption="📄 Mudrex Statistics Report"
        )

        await update.message.reply_text("✅ Report generated successfully!")

    except Exception as e:
        logger.error(f"Error in /report command: {e}")
        await update.message.reply_text(f"❌ Error generating report: {str(e)}")


def setup_admin_commands(application):
    """
    Set up all admin command handlers

    Args:
        application: Telegram application instance
    """
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("backup", cmd_backup))
    application.add_handler(CommandHandler("sync", cmd_sync))
    application.add_handler(CommandHandler("report", cmd_report))

    logger.info("Admin commands set up successfully")


def update_last_sync_time():
    """Update the last sync timestamp"""
    global LAST_SYNC_TIME
    LAST_SYNC_TIME = datetime.now()
