"""
Mudrex Telegram Statistics Bot

Main entry point for the bot application.
Initializes database, sets up handlers, and starts the bot.
"""

import logging
import sys
from telegram.ext import Application

from bot.config import Config
from bot.database.connection import init_db, close_db
from bot.handlers import setup_listeners, setup_commands, setup_admin_commands
from bot.schedulers import setup_schedulers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """
    Post-initialization callback

    Called after the application is initialized but before it starts.
    Initializes database and sets up schedulers.
    """
    logger.info("Initializing Mudrex Stats Bot...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Set up schedulers
    try:
        setup_schedulers(application)
        logger.info("Schedulers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize schedulers: {e}")
        raise

    logger.info("Bot initialization complete")


async def post_shutdown(application: Application) -> None:
    """
    Post-shutdown callback

    Called when the bot is shutting down.
    Closes database connections and cleans up resources.
    """
    logger.info("Shutting down Mudrex Stats Bot...")

    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

    logger.info("Bot shutdown complete")


def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated")

        # Log configuration summary
        logger.info(f"Bot Token: {'*' * 20}{Config.BOT_TOKEN[-5:]}")
        logger.info(f"Tracked Bot: @{Config.TRACKED_BOT_USERNAME}")
        logger.info(f"Admin IDs: {len(Config.ADMIN_IDS)} configured")
        logger.info(f"Topics: {len(Config.TOPICS)} configured")
        logger.info(f"Insights Channel ID: {Config.INSIGHTS_CHANNEL_ID}")
        logger.info(f"Official Group ID: {Config.OFFICIAL_GROUP_ID}")

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Create application
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Set up handlers
    try:
        setup_listeners(application)
        setup_commands(application)
        setup_admin_commands(application)
        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Failed to set up handlers: {e}")
        sys.exit(1)

    # Start the bot
    logger.info("Starting Mudrex Stats Bot...")
    logger.info("Press Ctrl+C to stop the bot")

    try:
        application.run_polling(
            allowed_updates=[
                "message",
                "channel_post",
                "chat_member",
            ],
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
