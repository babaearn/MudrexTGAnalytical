"""Message and event listeners for real-time tracking"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, ChatMemberHandler, filters

from bot.config import Config
from bot.database.connection import get_session
from bot.database.queries import (
    store_channel_post,
    store_topic_message,
    store_bot_usage,
    store_member_event,
)
from bot.utils.parsers import extract_symbol

logger = logging.getLogger(__name__)


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new channel posts and updates

    Tracks views, forwards, and reactions for the signal channel
    """
    if not update.channel_post:
        return

    post = update.channel_post

    # Only track posts from the configured channel
    if post.chat.id != Config.INSIGHTS_CHANNEL_ID:
        return

    async with get_session() as session:
        try:
            # Extract content preview (first 200 chars)
            content_preview = None
            if post.text:
                content_preview = post.text[:200]
            elif post.caption:
                content_preview = post.caption[:200]

            # Count reactions
            reactions_count = 0
            if hasattr(post, 'reactions') and post.reactions:
                reactions_count = sum(r.total_count for r in post.reactions)

            await store_channel_post(
                session=session,
                message_id=post.message_id,
                channel_id=post.chat.id,
                posted_at=post.date,
                views=post.forward_from_message_id or 0,
                forwards=0,  # Will be updated later
                reactions=reactions_count,
                content_preview=content_preview,
            )

            logger.info(f"Stored channel post: {post.message_id}")

        except Exception as e:
            logger.error(f"Error handling channel post: {e}")


async def handle_topic_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle messages in topic threads

    Tracks all messages and identifies bot queries
    """
    if not update.message:
        return

    message = update.message

    # Only track messages from the configured group
    if message.chat.id != Config.OFFICIAL_GROUP_ID:
        return

    # Get topic ID (thread ID)
    topic_id = message.message_thread_id
    if topic_id is None:
        return  # Not a topic message

    # Check if this topic is configured
    if topic_id not in Config.get_all_topic_ids():
        return

    async with get_session() as session:
        try:
            # Determine message type
            message_type = 'general'
            user_id = message.from_user.id if message.from_user else None
            username = message.from_user.username if message.from_user else None

            # Check if this is a bot response
            if message.from_user and message.from_user.username == Config.TRACKED_BOT_USERNAME:
                message_type = 'bot_response'

                # If it's a reply, extract the original query
                if message.reply_to_message:
                    original_msg = message.reply_to_message
                    original_user = original_msg.from_user

                    if original_user and original_msg.text:
                        # This is a bot response to a user query
                        # Store the bot usage
                        symbol = extract_symbol(original_msg.text)

                        await store_bot_usage(
                            session=session,
                            user_id=original_user.id,
                            username=original_user.username or '',
                            first_name=original_user.first_name or '',
                            topic_id=topic_id,
                            symbol=symbol,
                            query_text=original_msg.text,
                            queried_at=original_msg.date,
                        )

                        logger.info(f"Stored bot usage: {original_user.username} -> {symbol}")

            elif message.text and message.text.startswith('/'):
                # User might be querying the bot
                message_type = 'user_query'

            # Extract content preview
            content_preview = None
            if message.text:
                content_preview = message.text[:200]
            elif message.caption:
                content_preview = message.caption[:200]

            # Store the message
            await store_topic_message(
                session=session,
                message_id=message.message_id,
                group_id=message.chat.id,
                topic_id=topic_id,
                user_id=user_id,
                username=username or '',
                message_type=message_type,
                content_preview=content_preview,
                created_at=message.date,
            )

        except Exception as e:
            logger.error(f"Error handling topic message: {e}")


async def handle_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle member join/leave events

    Tracks when users join or leave the group
    """
    if not update.chat_member:
        return

    member_update = update.chat_member

    # Only track events from the configured group
    if member_update.chat.id != Config.OFFICIAL_GROUP_ID:
        return

    async with get_session() as session:
        try:
            old_status = member_update.old_chat_member.status
            new_status = member_update.new_chat_member.status

            event_type = None

            # Determine event type
            if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
                event_type = 'joined'
            elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked']:
                event_type = 'left'

            if event_type:
                user = member_update.from_user
                await store_member_event(
                    session=session,
                    group_id=member_update.chat.id,
                    user_id=user.id,
                    username=user.username or '',
                    event_type=event_type,
                    event_at=datetime.utcnow(),
                )

                logger.info(f"Stored member event: {user.username} {event_type}")

        except Exception as e:
            logger.error(f"Error handling member update: {e}")


def setup_listeners(application):
    """
    Set up all message and event listeners

    Args:
        application: Telegram application instance
    """
    # Channel post handler
    application.add_handler(
        MessageHandler(
            filters.ChatType.CHANNEL,
            handle_channel_post,
        )
    )

    # Topic message handler (messages in the group with topics)
    application.add_handler(
        MessageHandler(
            filters.ChatType.SUPERGROUP & filters.IS_TOPIC_MESSAGE,
            handle_topic_message,
        )
    )

    # Member update handler
    application.add_handler(
        ChatMemberHandler(
            handle_member_update,
            ChatMemberHandler.CHAT_MEMBER,
        )
    )

    logger.info("Listeners set up successfully")
