"""Parsing utilities for Mudrex Stats Bot"""

import re
from datetime import datetime
from typing import Tuple, Optional


def parse_month(month_str: str) -> Tuple[datetime, datetime]:
    """
    Parse month string to date range

    Args:
        month_str: Month abbreviation (jan, feb, etc.)

    Returns:
        Tuple of (start_date, end_date) for the month

    Raises:
        ValueError: If month string is invalid
    """
    months = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }

    month_lower = month_str.lower().strip()
    month_num = months.get(month_lower)

    if month_num is None:
        raise ValueError(f"Invalid month: {month_str}")

    year = datetime.now().year

    start_date = datetime(year, month_num, 1)

    if month_num == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month_num + 1, 1)

    return start_date, end_date


def extract_symbol(text: str) -> Optional[str]:
    """
    Extract trading symbol from query text

    Args:
        text: Message text containing symbol

    Returns:
        Normalized symbol (e.g., BTCUSDT) or None if not found

    Examples:
        /BTCUSDT -> BTCUSDT
        /btc -> BTCUSDT
        /ETH -> ETHUSDT
        Check /SOLUSDT chart -> SOLUSDT
    """
    if not text:
        return None

    # Match patterns like /BTCUSDT, /btc, /ETH, etc.
    match = re.search(r'/([A-Za-z]+(?:USDT)?)', text)

    if match:
        symbol = match.group(1).upper()

        # Add USDT suffix if not present
        if not symbol.endswith('USDT'):
            symbol += 'USDT'

        return symbol

    return None


def extract_command_args(text: str) -> Tuple[str, Optional[str]]:
    """
    Extract command and optional argument

    Args:
        text: Command text (e.g., "/topic1 jan")

    Returns:
        Tuple of (command, argument)

    Examples:
        /topic1 jan -> ('topic1', 'jan')
        /in -> ('in', None)
        /topusers topic1 -> ('topusers', 'topic1')
    """
    parts = text.strip().split(maxsplit=1)

    command = parts[0].lstrip('/')
    arg = parts[1] if len(parts) > 1 else None

    return command, arg


def get_topic_number_from_command(command: str) -> Optional[str]:
    """
    Extract topic number from command

    Args:
        command: Command string (e.g., 'topic1', 't2')

    Returns:
        Topic number as string or None

    Examples:
        topic1 -> '1'
        t2 -> '2'
        topusers -> None
    """
    # Match topic1, topic2, etc.
    match = re.match(r'topic(\d+)', command)
    if match:
        return match.group(1)

    # Match t1, t2, etc. (short aliases)
    match = re.match(r't(\d+)', command)
    if match:
        return match.group(1)

    return None
