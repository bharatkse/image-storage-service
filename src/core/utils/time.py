"""
Time-related utilities for the application.

All timestamps are generated in UTC and serialized using
ISO-8601 format with timezone information to ensure
correct lexicographic ordering in DynamoDB.
"""

from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format.

    Example:
        2024-01-15T10:42:31.123456+00:00

    This format is safe for:
    - DynamoDB range key comparisons
    - Sorting
    - JSON serialization
    """
    return datetime.now(timezone.utc).isoformat()
