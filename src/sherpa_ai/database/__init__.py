"""Database module for Sherpa AI.

This module provides database functionality for tracking user usage and managing whitelists.
It exports the UserUsageTracker class which handles token usage tracking on a per-user basis.

Example:
    >>> from sherpa_ai.database import UserUsageTracker
    >>> tracker = UserUsageTracker()
    >>> tracker.check_usage("user123", 100)
    {'token-left': 900, 'can_execute': True, 'message': '', 'time_left': '23 hours : 59 min : 59 sec'}
"""

from sherpa_ai.database.user_usage_tracker import UserUsageTracker


__all__ = ["UserUsageTracker"]
