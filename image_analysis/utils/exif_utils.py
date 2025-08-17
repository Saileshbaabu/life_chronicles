"""
EXIF utility functions for image analysis.
"""
import os
import tempfile
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def convert_gps_to_decimal(gps_lat, gps_lon, lat_ref, lon_ref):
    """
    Convert GPS coordinates from degrees, minutes, seconds to decimal degrees.
    
    Args:
        gps_lat: GPS latitude in degrees, minutes, seconds
        gps_lon: GPS longitude in degrees, minutes, seconds
        lat_ref: Latitude reference ('N' or 'S')
        lon_ref: Longitude reference ('E' or 'W')
    
    Returns:
        tuple: (decimal_lat, decimal_lon)
    """
    try:
        # Convert latitude
        lat_deg = float(gps_lat[0])
        lat_min = float(gps_lat[1])
        lat_sec = float(gps_lat[2])
        decimal_lat = lat_deg + (lat_min / 60.0) + (lat_sec / 3600.0)
        if lat_ref == 'S':
            decimal_lat = -decimal_lat
            
        # Convert longitude
        lon_deg = float(gps_lon[0])
        lon_min = float(gps_lon[1])
        lon_sec = float(gps_lon[2])
        decimal_lon = lon_deg + (lon_min / 60.0) + (lon_sec / 3600.0)
        if lon_ref == 'W':
            decimal_lon = -decimal_lon
            
        return round(decimal_lat, 6), round(decimal_lon, 6)
    except (TypeError, ValueError, IndexError) as e:
        logger.warning(f"Error converting GPS coordinates: {e}")
        return None, None


def extract_exif_data(image_path):
    """
    Extract EXIF data from an image file.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        dict: Dictionary containing EXIF data
    """
    try:
        with Image.open(image_path) as img:
            exif_data = {}
            
            # Extract basic EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
                
                # Extract GPS data
                gps_data = {}
                if 'GPSInfo' in exif_data:
                    for gps_tag_id, gps_value in exif_data['GPSInfo'].items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
                    
                    # Convert GPS coordinates to decimal
                    if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                        lat_ref = gps_data.get('GPSLatitudeRef', 'N')
                        lon_ref = gps_data.get('GPSLongitudeRef', 'E')
                        decimal_lat, decimal_lon = convert_gps_to_decimal(
                            gps_data['GPSLatitude'],
                            gps_data['GPSLongitude'],
                            lat_ref,
                            lon_ref
                        )
                        
                        if decimal_lat is not None and decimal_lon is not None:
                            exif_data['gps_decimal'] = {
                                'lat': decimal_lat,
                                'lon': decimal_lon
                            }
            
            return exif_data
            
    except Exception as e:
        logger.error(f"Error extracting EXIF data: {e}")
        return {}


def save_image_to_temp(uploaded_file):
    """
    Save an uploaded image to a temporary file.
    
    Args:
        uploaded_file: Django UploadedFile object
    
    Returns:
        str: Path to the temporary file
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_path = temp_file.name
        
        # Write the uploaded file content
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        
        temp_file.close()
        return temp_path
        
    except Exception as e:
        logger.error(f"Error saving image to temp: {e}")
        return None


def cleanup_temp_file(file_path):
    """
    Clean up a temporary file.
    
    Args:
        file_path: Path to the temporary file
    """
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up temporary file {file_path}: {e}")
