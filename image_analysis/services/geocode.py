import requests
import time
import hashlib
import json
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class PlaceCandidate:
    """Represents a geocoding result candidate"""
    
    def __init__(self, data: Dict[str, Any]):
        self.label = data.get('display_name', '')
        self.lat = float(data.get('lat', 0))
        self.lon = float(data.get('lon', 0))
        self.place_name = data.get('name', '')
        self.city = self._extract_city(data)
        self.admin = self._extract_admin(data)
        self.country = data.get('address', {}).get('country', '')
        self.country_code = data.get('address', {}).get('country_code', '').upper()
        self.provider = 'nominatim'
        self.provider_place_id = str(data.get('place_id', ''))
        self.confidence = self._calculate_confidence(data)
    
    def _extract_city(self, data: Dict[str, Any]) -> str:
        """Extract city from address components"""
        address = data.get('address', {})
        for key in ['city', 'town', 'village', 'municipality']:
            if address.get(key):
                return address[key]
        return ''
    
    def _extract_admin(self, data: Dict[str, Any]) -> str:
        """Extract administrative region from address components"""
        address = data.get('address', {})
        for key in ['state', 'province', 'region']:
            if address.get(key):
                return address[key]
        return ''
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Map Nominatim importance to confidence score (0.5 to 0.95)"""
        importance = float(data.get('importance', 0.1))
        # Map importance (0.0 to 1.0) to confidence (0.5 to 0.95)
        confidence = 0.5 + (importance * 0.45)
        return min(0.95, max(0.5, confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'label': self.label,
            'lat': self.lat,
            'lon': self.lon,
            'place_name': self.place_name,
            'city': self.city,
            'admin': self.admin,
            'country': self.country,
            'country_code': self.country_code,
            'provider': self.provider,
            'provider_place_id': self.provider_place_id,
            'confidence': self.confidence,
        }

class GeoProvider:
    """Base class for geocoding providers"""
    
    def search(self, query: str) -> List[PlaceCandidate]:
        """Search for places by query string"""
        raise NotImplementedError
    
    def reverse(self, lat: float, lon: float) -> Optional[PlaceCandidate]:
        """Reverse geocode coordinates to place"""
        raise NotImplementedError
    
    def forward(self, city: str, country: str) -> Optional[PlaceCandidate]:
        """Forward geocode city/country to coordinates"""
        raise NotImplementedError

class NominatimProvider(GeoProvider):
    """Nominatim geocoding provider implementation"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'NOMINATIM_BASE', 'https://nominatim.openstreetmap.org')
        self.user_agent = getattr(settings, 'NOMINATIM_USER_AGENT', 'LifeChronicles/1.0')
        self.email = getattr(settings, 'NOMINATIM_EMAIL', '')
        self.rate_limit_delay = 1.0  # 1 request per second
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Nominatim with rate limiting and error handling"""
        self._rate_limit()
        
        # Add required headers
        headers = {
            'User-Agent': self.user_agent
        }
        
        # Add email if configured
        if self.email:
            params['email'] = self.email
        
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 429:
                # Rate limited - extract retry-after header
                retry_after = response.headers.get('Retry-After', 60)
                logger.warning(f"Rate limited by Nominatim. Retry after {retry_after} seconds")
                time.sleep(int(retry_after))
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Nominatim: {e}")
            return None
    
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation"""
        # Create a hash of the parameters
        param_str = json.dumps(kwargs, sort_keys=True)
        return f"geocode:{operation}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def search(self, query: str) -> List[PlaceCandidate]:
        """Search for places by query string"""
        if not query or len(query.strip()) > 120:
            return []
        
        query = query.strip()
        cache_key = self._get_cache_key('search', query=query)
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return [PlaceCandidate(item) for item in cached_result]
        
        # Make API request
        params = {
            'q': query,
            'format': 'json',
            'limit': 5,
            'addressdetails': 1,
        }
        
        result = self._make_request('search', params)
        if not result:
            return []
        
        # Convert to PlaceCandidate objects
        candidates = [PlaceCandidate(item) for item in result]
        
        # Cache for 24 hours
        cache.set(cache_key, [c.to_dict() for c in candidates], 86400)
        
        return candidates
    
    def reverse(self, lat: float, lon: float) -> Optional[PlaceCandidate]:
        """Reverse geocode coordinates to place"""
        # Round coordinates to 5 decimal places for caching
        lat_rounded = round(lat, 5)
        lon_rounded = round(lon, 5)
        
        cache_key = self._get_cache_key('reverse', lat=lat_rounded, lon=lon_rounded)
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return PlaceCandidate(cached_result)
        
        # Make API request
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
        }
        
        result = self._make_request('reverse', params)
        if not result:
            return None
        
        # Convert to PlaceCandidate object
        candidate = PlaceCandidate(result)
        
        # Cache for 24 hours
        cache.set(cache_key, candidate.to_dict(), 86400)
        
        return candidate
    
    def forward(self, city: str, country: str) -> Optional[PlaceCandidate]:
        """Forward geocode city/country to coordinates"""
        if not city or not country:
            return None
        
        query = f"{city}, {country}"
        cache_key = self._get_cache_key('forward', city=city, country=country)
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return PlaceCandidate(cached_result)
        
        # Make API request
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
        }
        
        result = self._make_request('search', params)
        if not result or not result:
            return None
        
        # Convert to PlaceCandidate object
        candidate = PlaceCandidate(result[0])
        
        # Cache for 24 hours
        cache.set(cache_key, candidate.to_dict(), 86400)
        
        return candidate

# Default provider instance
geocoding_provider = NominatimProvider()
