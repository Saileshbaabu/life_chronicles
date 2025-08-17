"""
Daypart services for categorizing photos by time of day
"""
from datetime import datetime, time
from typing import Optional, Union
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)

def bucket_daypart(local_dt: Union[datetime, time]) -> str:
    """
    Bucket a local datetime or time into daypart categories.
    
    Args:
        local_dt: Local datetime or time object
        
    Returns:
        Daypart string: 'morning', 'afternoon', 'evening', or 'night'
    """
    if isinstance(local_dt, datetime):
        local_time = local_dt.time()
    else:
        local_time = local_dt
    
    # Define daypart boundaries
    morning_start = time(5, 0)      # 05:00
    morning_end = time(11, 59)      # 11:59
    afternoon_start = time(12, 0)   # 12:00
    afternoon_end = time(16, 59)    # 16:59
    evening_start = time(17, 0)     # 17:00
    evening_end = time(20, 59)      # 20:59
    
    if morning_start <= local_time <= morning_end:
        return 'morning'
    elif afternoon_start <= local_time <= afternoon_end:
        return 'afternoon'
    elif evening_start <= local_time <= evening_end:
        return 'evening'
    else:
        return 'night'

def tz_for_place(place_ctx: dict) -> ZoneInfo:
    """
    Get timezone for a place context.
    
    Args:
        place_ctx: Dictionary with place information including timezone, lat, lon
        
    Returns:
        ZoneInfo timezone object
    """
    # If timezone is explicitly provided, use it
    if place_ctx.get('timezone'):
        try:
            return ZoneInfo(place_ctx['timezone'])
        except Exception:
            logger.warning(f"Unknown timezone: {place_ctx['timezone']}")
    
    # Try to derive timezone from coordinates
    lat = place_ctx.get('lat')
    lon = place_ctx.get('lon')
    
    if lat is not None and lon is not None:
        try:
            # Use zoneinfo to get timezone from coordinates
            tz = ZoneInfo.atlas().get((lat, lon))
            if tz:
                return tz
        except Exception as e:
            logger.warning(f"Failed to derive timezone from coordinates: {e}")
    
    # Fallback to UTC
    logger.info("Using UTC as fallback timezone")
    return ZoneInfo("UTC")

def to_local(utc_dt: datetime, tz: ZoneInfo) -> datetime:
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_dt: UTC datetime object
        tz: Target timezone
        
    Returns:
        Localized datetime object
    """
    if utc_dt.tzinfo is None:
        # Assume UTC if no timezone info
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    
    return utc_dt.astimezone(tz)

def get_daypart_from_datetime(dt: datetime, place_ctx: dict) -> tuple[str, str]:
    """
    Get daypart and local time string from a datetime.
    
    Args:
        dt: Datetime object (UTC or local)
        place_ctx: Place context for timezone conversion
        
    Returns:
        Tuple of (daypart, local_time_str)
    """
    try:
        # Convert to local timezone
        local_tz = tz_for_place(place_ctx)
        local_dt = to_local(dt, local_tz)
        
        # Get daypart
        daypart = bucket_daypart(local_dt)
        
        # Format local time as HH:MM
        local_time_str = local_dt.strftime('%H:%M')
        
        return daypart, local_time_str
        
    except Exception as e:
        logger.error(f"Error processing datetime {dt}: {e}")
        return 'unknown', ''

def get_dayparts_order(dayparts: list[str]) -> list[str]:
    """
    Get ordered list of dayparts based on natural progression.
    
    Args:
        dayparts: List of daypart strings
        
    Returns:
        Ordered list of dayparts
    """
    natural_order = ['morning', 'afternoon', 'evening', 'night']
    
    # Filter to only include dayparts that are present
    present_dayparts = [dp for dp in natural_order if dp in dayparts]
    
    return present_dayparts
