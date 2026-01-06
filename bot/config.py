"""Configuration management for the Mudrex Stats Bot"""

import os
import json
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Bot configuration from environment variables"""

    # Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    TRACKED_BOT_USERNAME: str = os.getenv("TRACKED_BOT_USERNAME", "Mudrextest_bot")

    # Admin Access (comma-separated user IDs)
    ADMIN_IDS: List[int] = [
        int(admin_id.strip())
        for admin_id in os.getenv("ADMIN_IDS", "").split(",")
        if admin_id.strip()
    ]

    # Signal Channel
    INSIGHTS_CHANNEL_ID: int = int(os.getenv("INSIGHTS_CHANNEL_ID", "-1002163454656"))

    # Official Mudrex Group
    OFFICIAL_GROUP_ID: int = int(os.getenv("OFFICIAL_GROUP_ID", "-1001868775086"))

    # Topics Configuration (JSON format)
    TOPICS: Dict[str, Dict] = {}
    try:
        topics_json = os.getenv("TOPICS", '{"1":{"id":89270,"name":"Market Intelligence"}}')
        TOPICS = json.loads(topics_json)
    except json.JSONDecodeError:
        print("Warning: Invalid TOPICS JSON format, using default")
        TOPICS = {"1": {"id": 89270, "name": "Market Intelligence"}}

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Timezone
    TIMEZONE: str = "Asia/Kolkata"

    # Sync settings
    HISTORICAL_MESSAGE_LIMIT: int = int(os.getenv("HISTORICAL_MESSAGE_LIMIT", "1000"))
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "0.5"))

    # Scheduler settings
    UPDATE_VIEWS_INTERVAL_MINUTES: int = int(os.getenv("UPDATE_VIEWS_INTERVAL_MINUTES", "60"))
    DAILY_SNAPSHOT_HOUR: int = int(os.getenv("DAILY_SNAPSHOT_HOUR", "0"))  # Midnight IST

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN environment variable is required")
        if not cls.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        if not cls.ADMIN_IDS:
            print("Warning: No ADMIN_IDS configured. All admin commands will be disabled.")
        return True

    @classmethod
    def get_topic_by_number(cls, topic_num: str) -> Dict | None:
        """Get topic configuration by number"""
        return cls.TOPICS.get(topic_num)

    @classmethod
    def get_all_topic_ids(cls) -> List[int]:
        """Get all configured topic IDs"""
        return [topic["id"] for topic in cls.TOPICS.values()]

    @classmethod
    def get_topic_name(cls, topic_id: int) -> str | None:
        """Get topic name by ID"""
        for topic in cls.TOPICS.values():
            if topic["id"] == topic_id:
                return topic["name"]
        return None
