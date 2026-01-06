"""Formatting utilities for Mudrex Stats Bot"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


def format_number(num: int) -> str:
    """
    Format number with thousands separators

    Args:
        num: Number to format

    Returns:
        Formatted string (e.g., 1,234,567)
    """
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{num:,}"


def format_progress_bar(value: int, max_value: int, length: int = 10) -> str:
    """
    Create a text-based progress bar

    Args:
        value: Current value
        max_value: Maximum value
        length: Bar length in characters

    Returns:
        Progress bar string (e.g., "████████░░")
    """
    if max_value == 0:
        return "░" * length

    filled = int((value / max_value) * length)
    return "█" * filled + "░" * (length - filled)


def format_channel_stats(stats: Dict[str, Any], period: str = "All Time") -> str:
    """
    Format signal channel statistics

    Args:
        stats: Dictionary containing channel statistics
        period: Time period label

    Returns:
        Formatted stats message
    """
    message = "📊 MUDREX CRYPTO INSIGHTS\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📅 Period: {period}\n"
    message += f"👥 Subscribers: {format_number(stats.get('subscribers', 0))}\n"
    message += f"📝 Total Posts: {format_number(stats.get('total_posts', 0))}\n"
    message += f"👁 Total Views: {format_number(stats.get('total_views', 0))}\n"

    avg_views = stats.get('avg_views_per_post', 0)
    message += f"📈 Avg Views/Post: {format_number(int(avg_views))}\n"

    message += f"📤 Total Forwards: {format_number(stats.get('total_forwards', 0))}\n"
    message += f"❤️ Total Reactions: {format_number(stats.get('total_reactions', 0))}\n"

    # Add view trends if available
    if 'daily_views' in stats and stats['daily_views']:
        message += "\n📊 VIEW TRENDS (Last 7 Days):\n"
        max_views = max(stats['daily_views'].values()) if stats['daily_views'] else 1

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days:
            views = stats['daily_views'].get(day, 0)
            bar = format_progress_bar(views, max_views)
            message += f"{day}: {bar} {format_number(views)}\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return message


def format_topic_stats(
    stats: Dict[str, Any],
    topic_name: str,
    period: str = "All Time"
) -> str:
    """
    Format topic statistics

    Args:
        stats: Dictionary containing topic statistics
        topic_name: Name of the topic
        period: Time period label

    Returns:
        Formatted stats message
    """
    message = f"📊 {topic_name.upper()} STATS\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📅 Period: {period}\n"
    message += f"📝 Total Messages: {format_number(stats.get('total_messages', 0))}\n"

    # Bot engagement section
    message += f"\n🤖 BOT ENGAGEMENT (@{stats.get('bot_username', 'Mudrextest_bot')}):\n"
    message += f"├─ Total Queries: {format_number(stats.get('total_queries', 0))}\n"
    message += f"├─ Unique Users: {format_number(stats.get('unique_users', 0))}\n"
    message += f"└─ Avg Queries/Day: {stats.get('avg_queries_per_day', 0)}\n"

    # Top users
    if 'top_users' in stats and stats['top_users']:
        message += "\n🏆 TOP BOT USERS:\n"
        for i, user in enumerate(stats['top_users'][:5], 1):
            name = user.get('name', 'Unknown')
            queries = user.get('queries', 0)
            message += f"{i}. {name} — {queries} queries\n"

    # Top symbols
    if 'top_symbols' in stats and stats['top_symbols']:
        message += "\n🔥 TOP SYMBOLS REQUESTED:\n"
        for i, symbol_data in enumerate(stats['top_symbols'][:5], 1):
            symbol = symbol_data.get('symbol', 'Unknown')
            count = symbol_data.get('count', 0)
            message += f"{i}. /{symbol} — {count}\n"

    # Activity trends
    if 'daily_activity' in stats and stats['daily_activity']:
        message += "\n📈 ACTIVITY (Last 7 Days):\n"
        max_msgs = max(stats['daily_activity'].values()) if stats['daily_activity'] else 1

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in days:
            msgs = stats['daily_activity'].get(day, 0)
            bar = format_progress_bar(msgs, max_msgs)
            message += f"{day}: {bar} {msgs} msgs\n"

    # Member events
    if 'members_joined' in stats or 'members_left' in stats:
        message += "\n👥 MEMBERS (Since Bot Start):\n"
        message += f"├─ Joined: +{stats.get('members_joined', 0)}\n"
        message += f"└─ Left: -{stats.get('members_left', 0)}\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return message


def format_leaderboard(
    data: List[Dict[str, Any]],
    title: str,
    value_label: str = "Queries",
    show_percentage: bool = False,
    total: int = 0
) -> str:
    """
    Format leaderboard data

    Args:
        data: List of dictionaries with 'name' and 'value' keys
        title: Leaderboard title
        value_label: Label for the value column
        show_percentage: Whether to show percentage
        total: Total count for percentage calculation

    Returns:
        Formatted leaderboard message
    """
    message = f"🏆 {title}\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    if show_percentage and total > 0:
        message += f"Rank  {'Name':<20} {value_label:<10} %\n"
    else:
        message += f"Rank  {'Name':<20} {value_label}\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}

    for i, item in enumerate(data[:10], 1):
        medal = medals.get(i, "")
        rank = f"{medal} {i}." if medal else f"{i}."
        name = item.get('name', 'Unknown')[:20]
        value = item.get('value', 0)

        if show_percentage and total > 0:
            pct = (value / total) * 100
            message += f"{rank:<5} {name:<20} {value:<10} {pct:.1f}%\n"
        else:
            message += f"{rank:<5} {name:<20} {value}\n"

    if 'total_count' in data[0] if data else False:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"Total Unique: {data[0].get('total_count', len(data))}\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return message


def format_topics_list(topics_stats: List[Dict[str, Any]]) -> str:
    """
    Format list of all configured topics

    Args:
        topics_stats: List of topic statistics

    Returns:
        Formatted topics list message
    """
    message = "📋 CONFIGURED TOPICS\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "Official Mudrex Group Topics:\n\n"

    for topic in topics_stats:
        num = topic.get('number', '?')
        name = topic.get('name', 'Unknown')
        topic_id = topic.get('id', 0)
        messages = topic.get('messages', 0)
        queries = topic.get('queries', 0)

        emoji = {
            "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣",
            "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣", "10": "🔟"
        }.get(num, f"{num}.")

        message += f"{emoji} /topic{num} — {name}\n"
        message += f"└─ ID: {topic_id} | Messages: {format_number(messages)} | Bot Queries: {format_number(queries)}\n\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "Use /topic<n> or /t<n> to view detailed stats"

    return message


def format_status(status_data: Dict[str, Any]) -> str:
    """
    Format bot status information

    Args:
        status_data: Dictionary containing status information

    Returns:
        Formatted status message
    """
    message = "🤖 BOT STATUS\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    bot_status = "✅ Online" if status_data.get('bot_online') else "❌ Offline"
    db_status = "✅ Connected" if status_data.get('db_connected') else "❌ Disconnected"

    message += f"{bot_status}\n"
    message += f"Database: {db_status}\n"

    if 'last_sync' in status_data:
        last_sync = status_data['last_sync']
        if isinstance(last_sync, datetime):
            time_ago = datetime.now() - last_sync
            if time_ago < timedelta(minutes=1):
                sync_text = "just now"
            elif time_ago < timedelta(hours=1):
                sync_text = f"{int(time_ago.total_seconds() / 60)} mins ago"
            else:
                sync_text = f"{int(time_ago.total_seconds() / 3600)} hours ago"
        else:
            sync_text = str(last_sync)

        message += f"Last Sync: {sync_text}\n"

    if 'db_stats' in status_data:
        message += "\n📊 Database Stats:\n"
        for key, value in status_data['db_stats'].items():
            message += f"├─ {key}: {format_number(value)} records\n"

    if 'uptime' in status_data:
        uptime = status_data['uptime']
        message += f"\n⏰ Uptime: {uptime}\n"

    if 'next_sync' in status_data:
        message += f"🔄 Next Sync: {status_data['next_sync']}\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    return message
