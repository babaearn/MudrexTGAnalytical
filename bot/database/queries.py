"""Database query functions for Mudrex Stats Bot"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, func, and_, or_, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    ChannelPost,
    TopicMessage,
    BotUsage,
    MemberEvent,
    DailySnapshot,
    ChannelSubscriber,
)

logger = logging.getLogger(__name__)


# ==================== Channel Post Queries ====================


async def store_channel_post(
    session: AsyncSession,
    message_id: int,
    channel_id: int,
    posted_at: datetime,
    views: int = 0,
    forwards: int = 0,
    reactions: int = 0,
    content_preview: str = None,
) -> ChannelPost:
    """Store or update a channel post"""
    try:
        # Check if post exists
        stmt = select(ChannelPost).where(ChannelPost.message_id == message_id)
        result = await session.execute(stmt)
        post = result.scalar_one_or_none()

        if post:
            # Update existing post
            post.views = views
            post.forwards = forwards
            post.reactions = reactions
            post.last_updated = datetime.utcnow()
        else:
            # Create new post
            post = ChannelPost(
                message_id=message_id,
                channel_id=channel_id,
                posted_at=posted_at,
                views=views,
                forwards=forwards,
                reactions=reactions,
                content_preview=content_preview,
            )
            session.add(post)

        await session.commit()
        return post

    except Exception as e:
        await session.rollback()
        logger.error(f"Error storing channel post: {e}")
        raise


async def get_channel_stats(
    session: AsyncSession,
    channel_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get channel statistics for a date range"""
    try:
        # Build base query
        conditions = [ChannelPost.channel_id == channel_id]

        if start_date:
            conditions.append(ChannelPost.posted_at >= start_date)
        if end_date:
            conditions.append(ChannelPost.posted_at < end_date)

        stmt = select(
            func.count(ChannelPost.id).label('total_posts'),
            func.sum(ChannelPost.views).label('total_views'),
            func.sum(ChannelPost.forwards).label('total_forwards'),
            func.sum(ChannelPost.reactions).label('total_reactions'),
            func.avg(ChannelPost.views).label('avg_views'),
        ).where(and_(*conditions))

        result = await session.execute(stmt)
        row = result.one()

        return {
            'total_posts': row.total_posts or 0,
            'total_views': row.total_views or 0,
            'total_forwards': row.total_forwards or 0,
            'total_reactions': row.total_reactions or 0,
            'avg_views_per_post': float(row.avg_views or 0),
        }

    except Exception as e:
        logger.error(f"Error getting channel stats: {e}")
        raise


async def get_latest_subscriber_count(
    session: AsyncSession,
    channel_id: int,
) -> int:
    """Get the most recent subscriber count for a channel"""
    try:
        stmt = (
            select(ChannelSubscriber.subscriber_count)
            .where(ChannelSubscriber.channel_id == channel_id)
            .order_by(desc(ChannelSubscriber.recorded_at))
            .limit(1)
        )

        result = await session.execute(stmt)
        count = result.scalar_one_or_none()
        return count or 0

    except Exception as e:
        logger.error(f"Error getting subscriber count: {e}")
        return 0


async def update_post_views(
    session: AsyncSession,
    message_id: int,
    views: int,
    forwards: int = None,
    reactions: int = None,
) -> bool:
    """Update view count for a channel post"""
    try:
        stmt = select(ChannelPost).where(ChannelPost.message_id == message_id)
        result = await session.execute(stmt)
        post = result.scalar_one_or_none()

        if post:
            post.views = views
            if forwards is not None:
                post.forwards = forwards
            if reactions is not None:
                post.reactions = reactions
            post.last_updated = datetime.utcnow()

            await session.commit()
            return True

        return False

    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating post views: {e}")
        return False


# ==================== Topic Message Queries ====================


async def store_topic_message(
    session: AsyncSession,
    message_id: int,
    group_id: int,
    topic_id: int,
    user_id: int,
    username: str,
    message_type: str,
    content_preview: str,
    created_at: datetime,
) -> TopicMessage:
    """Store a topic message"""
    try:
        message = TopicMessage(
            message_id=message_id,
            group_id=group_id,
            topic_id=topic_id,
            user_id=user_id,
            username=username,
            message_type=message_type,
            content_preview=content_preview,
            created_at=created_at,
        )
        session.add(message)
        await session.commit()
        return message

    except Exception as e:
        await session.rollback()
        logger.error(f"Error storing topic message: {e}")
        raise


async def get_topic_stats(
    session: AsyncSession,
    topic_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get topic statistics for a date range"""
    try:
        # Build base query
        conditions = [TopicMessage.topic_id == topic_id]

        if start_date:
            conditions.append(TopicMessage.created_at >= start_date)
        if end_date:
            conditions.append(TopicMessage.created_at < end_date)

        # Total messages
        stmt = select(func.count(TopicMessage.id)).where(and_(*conditions))
        result = await session.execute(stmt)
        total_messages = result.scalar_one()

        return {
            'total_messages': total_messages or 0,
        }

    except Exception as e:
        logger.error(f"Error getting topic stats: {e}")
        raise


# ==================== Bot Usage Queries ====================


async def store_bot_usage(
    session: AsyncSession,
    user_id: int,
    username: str,
    first_name: str,
    topic_id: int,
    symbol: Optional[str],
    query_text: str,
    queried_at: datetime,
) -> BotUsage:
    """Store a bot usage query"""
    try:
        usage = BotUsage(
            user_id=user_id,
            username=username,
            first_name=first_name,
            topic_id=topic_id,
            symbol=symbol,
            query_text=query_text,
            queried_at=queried_at,
        )
        session.add(usage)
        await session.commit()
        return usage

    except Exception as e:
        await session.rollback()
        logger.error(f"Error storing bot usage: {e}")
        raise


async def get_bot_usage_stats(
    session: AsyncSession,
    topic_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Get bot usage statistics"""
    try:
        conditions = []

        if topic_id is not None:
            conditions.append(BotUsage.topic_id == topic_id)
        if start_date:
            conditions.append(BotUsage.queried_at >= start_date)
        if end_date:
            conditions.append(BotUsage.queried_at < end_date)

        # Total queries and unique users
        if conditions:
            stmt = select(
                func.count(BotUsage.id).label('total_queries'),
                func.count(distinct(BotUsage.user_id)).label('unique_users'),
            ).where(and_(*conditions))
        else:
            stmt = select(
                func.count(BotUsage.id).label('total_queries'),
                func.count(distinct(BotUsage.user_id)).label('unique_users'),
            )

        result = await session.execute(stmt)
        row = result.one()

        return {
            'total_queries': row.total_queries or 0,
            'unique_users': row.unique_users or 0,
        }

    except Exception as e:
        logger.error(f"Error getting bot usage stats: {e}")
        raise


async def get_top_bot_users(
    session: AsyncSession,
    topic_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Get top bot users by query count"""
    try:
        conditions = []

        if topic_id is not None:
            conditions.append(BotUsage.topic_id == topic_id)
        if start_date:
            conditions.append(BotUsage.queried_at >= start_date)
        if end_date:
            conditions.append(BotUsage.queried_at < end_date)

        # Group by user and count queries
        if conditions:
            stmt = (
                select(
                    BotUsage.user_id,
                    BotUsage.username,
                    BotUsage.first_name,
                    func.count(BotUsage.id).label('query_count'),
                )
                .where(and_(*conditions))
                .group_by(BotUsage.user_id, BotUsage.username, BotUsage.first_name)
                .order_by(desc('query_count'))
                .limit(limit)
            )
        else:
            stmt = (
                select(
                    BotUsage.user_id,
                    BotUsage.username,
                    BotUsage.first_name,
                    func.count(BotUsage.id).label('query_count'),
                )
                .group_by(BotUsage.user_id, BotUsage.username, BotUsage.first_name)
                .order_by(desc('query_count'))
                .limit(limit)
            )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                'user_id': row.user_id,
                'username': row.username,
                'first_name': row.first_name,
                'name': row.first_name or row.username or f"User {row.user_id}",
                'queries': row.query_count,
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting top bot users: {e}")
        raise


async def get_top_symbols(
    session: AsyncSession,
    topic_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Get most requested symbols"""
    try:
        conditions = [BotUsage.symbol.isnot(None)]

        if topic_id is not None:
            conditions.append(BotUsage.topic_id == topic_id)
        if start_date:
            conditions.append(BotUsage.queried_at >= start_date)
        if end_date:
            conditions.append(BotUsage.queried_at < end_date)

        stmt = (
            select(
                BotUsage.symbol,
                func.count(BotUsage.id).label('count'),
            )
            .where(and_(*conditions))
            .group_by(BotUsage.symbol)
            .order_by(desc('count'))
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                'symbol': row.symbol,
                'count': row.count,
            }
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting top symbols: {e}")
        raise


# ==================== Member Event Queries ====================


async def store_member_event(
    session: AsyncSession,
    group_id: int,
    user_id: int,
    username: str,
    event_type: str,
    event_at: datetime,
) -> MemberEvent:
    """Store a member join/leave event"""
    try:
        event = MemberEvent(
            group_id=group_id,
            user_id=user_id,
            username=username,
            event_type=event_type,
            event_at=event_at,
        )
        session.add(event)
        await session.commit()
        return event

    except Exception as e:
        await session.rollback()
        logger.error(f"Error storing member event: {e}")
        raise


async def get_member_events_count(
    session: AsyncSession,
    group_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, int]:
    """Get count of member join/leave events"""
    try:
        conditions = [MemberEvent.group_id == group_id]

        if start_date:
            conditions.append(MemberEvent.event_at >= start_date)
        if end_date:
            conditions.append(MemberEvent.event_at < end_date)

        # Count joins
        stmt_joins = select(func.count(MemberEvent.id)).where(
            and_(*conditions, MemberEvent.event_type == 'joined')
        )
        result = await session.execute(stmt_joins)
        joined = result.scalar_one()

        # Count leaves
        stmt_leaves = select(func.count(MemberEvent.id)).where(
            and_(*conditions, MemberEvent.event_type == 'left')
        )
        result = await session.execute(stmt_leaves)
        left = result.scalar_one()

        return {
            'joined': joined or 0,
            'left': left or 0,
        }

    except Exception as e:
        logger.error(f"Error getting member events count: {e}")
        raise


# ==================== Daily Snapshot Queries ====================


async def create_daily_snapshot(
    session: AsyncSession,
    snapshot_date: date,
    channel_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    total_messages: int = 0,
    total_views: int = 0,
    total_queries: int = 0,
    unique_users: int = 0,
    subscriber_count: int = 0,
) -> DailySnapshot:
    """Create or update a daily snapshot"""
    try:
        # Check if snapshot exists
        conditions = [DailySnapshot.date == snapshot_date]

        if channel_id is not None:
            conditions.append(DailySnapshot.channel_id == channel_id)
        else:
            conditions.append(DailySnapshot.channel_id.is_(None))

        if topic_id is not None:
            conditions.append(DailySnapshot.topic_id == topic_id)
        else:
            conditions.append(DailySnapshot.topic_id.is_(None))

        stmt = select(DailySnapshot).where(and_(*conditions))
        result = await session.execute(stmt)
        snapshot = result.scalar_one_or_none()

        if snapshot:
            # Update existing snapshot
            snapshot.total_messages = total_messages
            snapshot.total_views = total_views
            snapshot.total_queries = total_queries
            snapshot.unique_users = unique_users
            snapshot.subscriber_count = subscriber_count
        else:
            # Create new snapshot
            snapshot = DailySnapshot(
                date=snapshot_date,
                channel_id=channel_id,
                topic_id=topic_id,
                total_messages=total_messages,
                total_views=total_views,
                total_queries=total_queries,
                unique_users=unique_users,
                subscriber_count=subscriber_count,
            )
            session.add(snapshot)

        await session.commit()
        return snapshot

    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating daily snapshot: {e}")
        raise


async def get_daily_activity(
    session: AsyncSession,
    topic_id: Optional[int] = None,
    channel_id: Optional[int] = None,
    days: int = 7,
) -> List[Dict[str, Any]]:
    """Get daily activity for the last N days"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        conditions = [
            DailySnapshot.date >= start_date,
            DailySnapshot.date <= end_date,
        ]

        if channel_id is not None:
            conditions.append(DailySnapshot.channel_id == channel_id)
        if topic_id is not None:
            conditions.append(DailySnapshot.topic_id == topic_id)

        stmt = (
            select(DailySnapshot)
            .where(and_(*conditions))
            .order_by(DailySnapshot.date)
        )

        result = await session.execute(stmt)
        snapshots = result.scalars().all()

        return [
            {
                'date': snapshot.date,
                'messages': snapshot.total_messages,
                'views': snapshot.total_views,
                'queries': snapshot.total_queries,
                'users': snapshot.unique_users,
            }
            for snapshot in snapshots
        ]

    except Exception as e:
        logger.error(f"Error getting daily activity: {e}")
        return []


# ==================== Subscriber Tracking ====================


async def store_subscriber_count(
    session: AsyncSession,
    channel_id: int,
    subscriber_count: int,
) -> ChannelSubscriber:
    """Store a subscriber count snapshot"""
    try:
        subscriber = ChannelSubscriber(
            channel_id=channel_id,
            subscriber_count=subscriber_count,
        )
        session.add(subscriber)
        await session.commit()
        return subscriber

    except Exception as e:
        await session.rollback()
        logger.error(f"Error storing subscriber count: {e}")
        raise


# ==================== Database Stats ====================


async def get_database_stats(session: AsyncSession) -> Dict[str, int]:
    """Get overall database statistics"""
    try:
        stats = {}

        # Channel posts count
        stmt = select(func.count(ChannelPost.id))
        result = await session.execute(stmt)
        stats['Channel Posts'] = result.scalar_one()

        # Topic messages count
        stmt = select(func.count(TopicMessage.id))
        result = await session.execute(stmt)
        stats['Topic Messages'] = result.scalar_one()

        # Bot queries count
        stmt = select(func.count(BotUsage.id))
        result = await session.execute(stmt)
        stats['Bot Queries'] = result.scalar_one()

        # Member events count
        stmt = select(func.count(MemberEvent.id))
        result = await session.execute(stmt)
        stats['Member Events'] = result.scalar_one()

        # Daily snapshots count
        stmt = select(func.count(DailySnapshot.id))
        result = await session.execute(stmt)
        stats['Daily Snapshots'] = result.scalar_one()

        return stats

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}
