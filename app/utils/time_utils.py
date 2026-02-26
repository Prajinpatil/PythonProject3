"""
Time Utilities - Temporal Analysis for Surveillance
Classifies time periods, calculates windows, timezone handling
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional
import pytz


def classify_time_of_day(dt: datetime) -> str:
    """
    Classify time into surveillance periods
    
    Returns:
        "night", "dawn", "day", or "dusk"
    """
    hour = dt.hour
    
    if 22 <= hour or hour < 6:  # 10 PM - 6 AM
        return "night"
    elif 6 <= hour < 8:  # 6 AM - 8 AM
        return "dawn"
    elif 8 <= hour < 18:  # 8 AM - 6 PM
        return "day"
    else:  # 6 PM - 10 PM
        return "dusk"


def get_time_multiplier(dt: datetime) -> float:
    """
    Get threat multiplier based on time of day
    Night intrusions are more suspicious
    """
    from app.core.constants import TIME_MULTIPLIERS
    
    period = classify_time_of_day(dt)
    return TIME_MULTIPLIERS.get(period, 1.0)


def is_business_hours(dt: datetime) -> bool:
    """
    Check if datetime falls within business hours
    Weekdays 8 AM - 6 PM
    """
    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    return 8 <= dt.hour < 18


def is_weekend(dt: datetime) -> bool:
    """Check if datetime is on weekend"""
    return dt.weekday() >= 5


def get_shift(dt: datetime) -> str:
    """
    Determine security shift
    Useful for staffing analytics
    """
    hour = dt.hour
    
    if 6 <= hour < 14:
        return "morning"
    elif 14 <= hour < 22:
        return "evening"
    else:
        return "night"


def calculate_time_window(
    start: datetime,
    window_minutes: int = 30
) -> Tuple[datetime, datetime]:
    """
    Calculate time window for pattern detection
    
    Returns:
        (start_time, end_time) tuple
    """
    end = start + timedelta(minutes=window_minutes)
    return (start, end)


def get_recent_window(minutes: int = 60) -> Tuple[datetime, datetime]:
    """
    Get time window for "recent" events
    
    Args:
        minutes: How far back to look
        
    Returns:
        (start_time, end_time) where end_time is now
    """
    now = datetime.utcnow()
    start = now - timedelta(minutes=minutes)
    return (start, now)


def get_daily_window() -> Tuple[datetime, datetime]:
    """Get last 24 hours window"""
    now = datetime.utcnow()
    start = now - timedelta(days=1)
    return (start, now)


def get_weekly_window() -> Tuple[datetime, datetime]:
    """Get last 7 days window"""
    now = datetime.utcnow()
    start = now - timedelta(days=7)
    return (start, now)


def parse_iso_datetime(dt_string: str) -> Optional[datetime]:
    """
    Parse ISO format datetime string
    Handles common formats with fallback
    """
    try:
        # Try with timezone
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try without timezone
            return datetime.fromisoformat(dt_string)
        except ValueError:
            return None


def to_local_timezone(dt: datetime, timezone: str = "UTC") -> datetime:
    """
    Convert UTC datetime to local timezone
    
    Args:
        dt: UTC datetime
        timezone: Timezone name (e.g., "America/New_York", "Asia/Tokyo")
    """
    try:
        tz = pytz.timezone(timezone)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(tz)
    except pytz.exceptions.UnknownTimeZoneError:
        return dt


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format
    
    Example:
        format_duration(3665) -> "1h 1m 5s"
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def get_hour_of_day(dt: datetime) -> int:
    """Get hour of day (0-23)"""
    return dt.hour


def get_day_of_week(dt: datetime) -> str:
    """Get day name"""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[dt.weekday()]


def calculate_event_frequency(
    event_times: list,
    window_hours: int = 1
) -> float:
    """
    Calculate event frequency (events per hour)
    
    Args:
        event_times: List of datetime objects
        window_hours: Time window to analyze
        
    Returns:
        Events per hour rate
    """
    if not event_times:
        return 0.0
    
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=window_hours)
    
    recent_events = [dt for dt in event_times if dt >= cutoff]
    
    return len(recent_events) / window_hours


def is_within_cooldown(
    last_event_time: datetime,
    cooldown_seconds: int = 300
) -> bool:
    """
    Check if enough time has passed since last event
    Prevents alert spam
    
    Args:
        last_event_time: When last event occurred
        cooldown_seconds: Minimum time between events
        
    Returns:
        True if still in cooldown period
    """
    now = datetime.utcnow()
    elapsed = (now - last_event_time).total_seconds()
    return elapsed < cooldown_seconds


def time_until_expiry(expiry_time: datetime) -> timedelta:
    """
    Calculate time remaining until expiry
    """
    now = datetime.utcnow()
    return expiry_time - now


def is_expired(expiry_time: datetime) -> bool:
    """Check if datetime has passed"""
    return datetime.utcnow() > expiry_time


# ========== TIMESTAMP HELPERS ==========
def now_utc() -> datetime:
    """Get current UTC time"""
    return datetime.utcnow()


def now_timestamp() -> float:
    """Get current Unix timestamp"""
    return datetime.utcnow().timestamp()


def datetime_from_timestamp(timestamp: float) -> datetime:
    """Convert Unix timestamp to datetime"""
    return datetime.utcfromtimestamp(timestamp)


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO string"""
    return dt.isoformat() + "Z" if dt.tzinfo is None else dt.isoformat()
