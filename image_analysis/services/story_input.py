"""
Story input service for building story data from media and analysis
"""
from datetime import datetime, date
from typing import List, Dict, Any
import logging
from .daypart import get_daypart_from_datetime, get_dayparts_order

logger = logging.getLogger(__name__)

def build_story_input(
    media_list: List[Dict[str, Any]], 
    place_ctx: Dict[str, Any], 
    lang: str, 
    tone: str, 
    length: str
) -> Dict[str, Any]:
    """
    Build story input data from media list and place context.
    
    Args:
        media_list: List of media objects with analysis data
        place_ctx: Place context with location and timezone info
        lang: Target language ('en' or 'ta')
        tone: Story tone ('reportage', 'travelogue', 'diary')
        length: Story length ('short', 'medium', 'long')
        
    Returns:
        STORY_INPUT dictionary ready for story generation
    """
    try:
        # Process each media item to get daypart and local time
        photos = []
        all_dayparts = set()
        earliest_date = None
        
        for media_item in media_list:
            # Get datetime from EXIF or upload time
            dt = _get_datetime_from_media(media_item)
            
            # Get daypart and local time
            daypart, local_time = get_daypart_from_datetime(dt, place_ctx)
            all_dayparts.add(daypart)
            
            # Track earliest date
            if dt:
                item_date = dt.date()
                if earliest_date is None or item_date < earliest_date:
                    earliest_date = item_date
            
            # Build photo data
            photo_data = {
                "media_id": str(media_item.get('id', '')),
                "daypart": daypart,
                "local_time": local_time,
                "img_caption": media_item.get('analysis', {}).get('img_caption', ''),
                "objects": _filter_low_confidence_items(
                    media_item.get('analysis', {}).get('detected_objects', [])
                ),
                "attributes": _filter_low_confidence_items(
                    media_item.get('analysis', {}).get('attributes', [])
                ),
                "ocr_text": media_item.get('analysis', {}).get('ocr_text', ''),
                "user_notes": media_item.get('analysis', {}).get('user_notes', ''),
                "image_url": media_item.get('image_url', ''),
                "alt_text": media_item.get('alt_text', '')
            }
            
            photos.append(photo_data)
        
        # Sort photos by daypart order and then by local time
        dayparts_order = get_dayparts_order(list(all_dayparts))
        photos.sort(key=lambda x: (
            dayparts_order.index(x['daypart']) if x['daypart'] in dayparts_order else 999,
            x['local_time'] if x['local_time'] else '99:99'
        ))
        
        # Build place string
        place_str = _build_place_string(place_ctx)
        place_confidence = place_ctx.get('confidence', 0.0)
        
        # Build story input
        story_input = {
            "lang": lang,
            "tone": tone,
            "length": length,
            "story_date": earliest_date.isoformat() if earliest_date else None,
            "place_str": place_str,
            "place_confidence": place_confidence,
            "dayparts_order": dayparts_order,
            "photos": photos
        }
        
        logger.info(f"Built story input with {len(photos)} photos, {len(dayparts_order)} dayparts")
        return story_input
        
    except Exception as e:
        logger.error(f"Error building story input: {e}")
        raise

def _get_datetime_from_media(media_item: Dict[str, Any]) -> datetime:
    """
    Extract datetime from media item, preferring EXIF over upload time.
    
    Args:
        media_item: Media object with datetime information
        
    Returns:
        Datetime object or None
    """
    try:
        # Try EXIF datetime first
        exif_datetime = media_item.get('exif_datetime')
        if exif_datetime:
            if isinstance(exif_datetime, str):
                return datetime.fromisoformat(exif_datetime.replace('Z', '+00:00'))
            elif isinstance(exif_datetime, datetime):
                return exif_datetime
        
        # Fallback to upload time
        uploaded_at = media_item.get('uploaded_at')
        if uploaded_at:
            if isinstance(uploaded_at, str):
                return datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
            elif isinstance(uploaded_at, datetime):
                return uploaded_at
        
        # Final fallback to current time
        logger.warning(f"No datetime found for media {media_item.get('id')}, using current time")
        return datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Error parsing datetime for media {media_item.get('id')}: {e}")
        return datetime.utcnow()

def _filter_low_confidence_items(items: List[Dict[str, Any]], threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Filter out low-confidence objects/attributes.
    
    Args:
        items: List of items with confidence scores
        threshold: Minimum confidence threshold
        
    Returns:
        Filtered list of items
    """
    if not items:
        return []
    
    filtered = []
    for item in items:
        # If item has confidence field, check threshold
        if 'confidence' in item:
            if item.get('confidence', 0.0) >= threshold:
                filtered.append(item)
        else:
            # If no confidence field, include the item
            filtered.append(item)
    
    return filtered

def _build_place_string(place_ctx: Dict[str, Any]) -> str:
    """
    Build place string from place context.
    
    Args:
        place_ctx: Place context dictionary
        
    Returns:
        Formatted place string
    """
    parts = []
    
    # Add place name if available
    if place_ctx.get('place_name'):
        parts.append(place_ctx['place_name'])
    elif place_ctx.get('city'):
        parts.append(place_ctx['city'])
    
    # Add admin/state if different from city
    if place_ctx.get('admin') and place_ctx.get('admin') != place_ctx.get('city'):
        parts.append(place_ctx['admin'])
    
    # Add country
    if place_ctx.get('country'):
        parts.append(place_ctx['country'])
    
    return ", ".join(parts) if parts else ""
