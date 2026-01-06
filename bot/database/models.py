"""SQLAlchemy models for Mudrex Stats Bot"""

from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    UniqueConstraint,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ChannelPost(Base):
    """Channel posts tracking (Signal Channel)"""

    __tablename__ = "channel_posts"

    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger, unique=True, nullable=False, index=True)
    channel_id = Column(BigInteger, nullable=False, index=True)
    posted_at = Column(DateTime, nullable=False, index=True)
    views = Column(Integer, default=0)
    forwards = Column(Integer, default=0)
    reactions = Column(Integer, default=0)
    content_preview = Column(Text)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChannelPost(id={self.id}, message_id={self.message_id}, views={self.views})>"


class TopicMessage(Base):
    """Topic messages tracking"""

    __tablename__ = "topic_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger, nullable=False)
    group_id = Column(BigInteger, nullable=False)
    topic_id = Column(Integer, nullable=False, index=True)
    user_id = Column(BigInteger)
    username = Column(String(255))
    message_type = Column(String(50))  # 'user_query', 'bot_response', 'general'
    content_preview = Column(Text)
    created_at = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("message_id", "group_id", name="uq_message_group"),
        Index("ix_topic_messages_topic_created", "topic_id", "created_at"),
    )

    def __repr__(self):
        return f"<TopicMessage(id={self.id}, topic_id={self.topic_id}, type={self.message_type})>"


class BotUsage(Base):
    """Bot usage tracking"""

    __tablename__ = "bot_usage"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    topic_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), index=True)  # BTCUSDT, ETHUSDT, etc.
    query_text = Column(Text)
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_bot_usage_topic_queried", "topic_id", "queried_at"),
        Index("ix_bot_usage_user_queried", "user_id", "queried_at"),
    )

    def __repr__(self):
        return f"<BotUsage(id={self.id}, user={self.username}, symbol={self.symbol})>"


class MemberEvent(Base):
    """Member events (join/leave)"""

    __tablename__ = "member_events"

    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    event_type = Column(String(20), nullable=False)  # 'joined', 'left'
    event_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (Index("ix_member_events_group_event", "group_id", "event_at"),)

    def __repr__(self):
        return f"<MemberEvent(id={self.id}, user={self.username}, type={self.event_type})>"


class DailySnapshot(Base):
    """Daily snapshots for trends"""

    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    channel_id = Column(BigInteger)
    topic_id = Column(Integer)
    total_messages = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_queries = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    subscriber_count = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("date", "channel_id", "topic_id", name="uq_daily_snapshot"),
        Index("ix_daily_snapshots_date_channel", "date", "channel_id"),
        Index("ix_daily_snapshots_date_topic", "date", "topic_id"),
    )

    def __repr__(self):
        return f"<DailySnapshot(date={self.date}, channel_id={self.channel_id}, topic_id={self.topic_id})>"


class ChannelSubscriber(Base):
    """Channel subscriber tracking"""

    __tablename__ = "channel_subscribers"

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, nullable=False, index=True)
    subscriber_count = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (Index("ix_channel_subscribers_channel_recorded", "channel_id", "recorded_at"),)

    def __repr__(self):
        return f"<ChannelSubscriber(channel_id={self.channel_id}, count={self.subscriber_count})>"
