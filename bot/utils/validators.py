"""Validation utilities for Mudrex Stats Bot"""

from telegram import Update
from bot.config import Config


def is_admin(update: Update) -> bool:
    """
    Check if user is an admin

    Args:
        update: Telegram update object

    Returns:
        True if user is admin, False otherwise
    """
    if not update.effective_user:
        return False

    user_id = update.effective_user.id
    return user_id in Config.ADMIN_IDS


async def admin_only(update: Update) -> bool:
    """
    Decorator-friendly admin check with user feedback

    Args:
        update: Telegram update object

    Returns:
        True if user is admin, False otherwise (also sends message to user)
    """
    if is_admin(update):
        return True

    if update.message:
        await update.message.reply_text(
            "⛔ This command is only available to administrators."
        )

    return False
