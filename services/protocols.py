"""
Protocol metadata service — static data from config.py PROTOCOLS dict.

No external API calls. Pure local data access + age calculation.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import PROTOCOLS


def get_protocol_metadata(protocol_key: str) -> Optional[Dict[str, Any]]:
    """
    Get static metadata for a single protocol from the PROTOCOLS registry.

    Returns: Protocol metadata dict or None if key not found.
    """
    return PROTOCOLS.get(protocol_key)


def get_all_protocols() -> Dict[str, Dict[str, Any]]:
    """
    Get metadata for all 6 registered protocols.

    Returns: Full PROTOCOLS dict from config.py.
    """
    return PROTOCOLS


def calculate_age_days(launch_year: int) -> int:
    """
    Calculate the number of days since a protocol launched.
    Assumes launch date is January 1 of the given year.

    Args:
        launch_year: The year the protocol launched (e.g. 2023)

    Returns: Number of days since launch as int.
    """
    launch_date = datetime(launch_year, 1, 1, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - launch_date).days
