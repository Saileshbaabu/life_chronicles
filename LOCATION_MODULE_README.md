# 🗺️ Location Module for LifeChronicles

A comprehensive location management system that allows users to add, fix, and manage photo locations when EXIF GPS data is missing or incorrect.

## ✨ Features

- **🔍 Smart Search**: Autocomplete search for places, cities, and landmarks
- **🗺️ Interactive Map**: Leaflet-based map with draggable pins
- **📍 Current Location**: Use device GPS to set location
- **🌍 Geocoding**: Forward and reverse geocoding with OpenStreetMap Nominatim
- **📊 Confidence Scoring**: Intelligent confidence calculation based on data sources
- **💾 Persistent Storage**: Save and retrieve location data for stories/images
- **🔄 Cross-Validation**: Verify coordinates match city/country descriptions

## 🏗️ Architecture

### Backend (Django + DRF)
- **Models**: `StoryPlace` for location storage
- **Services**: `GeoProvider` abstraction with Nominatim implementation
- **Views**: RESTful API endpoints for geocoding and location management
- **Caching**: Redis or in-memory caching for geocoding results
- **Rate Limiting**: 1 request/second per IP with exponential backoff

### Frontend (React + Leaflet)
- **Components**: `LocationEditor` with search, map, and form
- **Maps**: Interactive Leaflet maps with draggable markers
- **Search**: Debounced autocomplete with keyboard navigation
- **Validation**: Real-time form validation and error handling

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Add to settings.py
INSTALLED_APPS = [
    # ... existing apps
    'image_analysis',
]

# Environment variables (.env)
NOMINATIM_BASE=https://nominatim.openstreetmap.org
NOMINATIM_USER_AGENT=LifeChronicles/1.0
NOMINATIM_EMAIL=your-email@example.com
MAP_TILES=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build component
npm run build

# Run tests
npm test
```

### 3. Integration

```tsx
import LocationEditor from './LocationEditor';

function App() {
  const handleLocationUpdate = (location) => {
    console.log('Location updated:', location);
  };

  return (
    <LocationEditor
      storyId="image_123"
      onLocationUpdate={handleLocationUpdate}
      initialLocation={{
        lat: 40.7128,
        lon: -74.0060,
        city: "New York",
        country: "United States"
      }}
    />
  );
}
```

## 📡 API Endpoints

### Geocoding Search
```http
POST /api/geocode/search/
Content-Type: application/json

{
  "query": "Kennedy Center"
}
```

**Response:**
```json
[
  {
    "label": "The John F. Kennedy Center for the Performing Arts, Washington, District of Columbia, United States",
    "lat": 38.8951,
    "lon": -77.0540,
    "place_name": "The John F. Kennedy Center for the Performing Arts",
    "city": "Washington",
    "admin": "District of Columbia",
    "country": "United States",
    "country_code": "US",
    "provider": "nominatim",
    "provider_place_id": "123456789",
    "confidence": 0.92
  }
]
```

### Reverse Geocoding
```http
POST /api/geocode/reverse/
Content-Type: application/json

{
  "lat": 38.8951,
  "lon": -77.0540
}
```

### Location Management
```http
POST /api/stories/{story_id}/location/
Content-Type: application/json

{
  "lat": 38.8951,
  "lon": -77.0540,
  "city": "Washington",
  "country": "United States"
}
```

**Response:**
```json
{
  "place_str": "The John F. Kennedy Center for the Performing Arts, Washington, United States",
  "lat": 38.8951,
  "lon": -77.0540,
  "city": "Washington",
  "admin": "District of Columbia",
  "country": "United States",
  "country_code": "US",
  "confidence": 0.9,
  "source": "user_form"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NOMINATIM_BASE` | Nominatim API base URL | `https://nominatim.openstreetmap.org` |
| `NOMINATIM_USER_AGENT` | User agent for API requests | `LifeChronicles/1.0` |
| `NOMINATIM_EMAIL` | Email for API requests (optional) | - |
| `MAP_TILES` | Map tile URL template | OpenStreetMap tiles |
| `REDIS_URL` | Redis cache URL | In-memory cache |
| `CACHE_TTL` | Cache time-to-live (seconds) | `86400` (24h) |

### Rate Limiting

- **Search**: 1 request/second per IP
- **Reverse**: 1 request/second per IP
- **Location Update**: No rate limiting (internal operations)

### Caching

- **Geocoding Results**: 24 hours TTL
- **Cache Keys**: MD5 hash of operation + parameters
- **Fallback**: In-memory cache if Redis unavailable

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
python manage.py test image_analysis

# Run specific test file
python manage.py test image_analysis.tests.test_geocoding

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- --testNamePattern="search results"
```

### Manual Testing

```bash
# Test the complete system
python test_location_module.py
```

## 🔒 Security & Best Practices

### Input Validation
- **Query Length**: Maximum 120 characters
- **Coordinates**: Valid lat/lon ranges (-90 to 90, -180 to 180)
- **HTML Sanitization**: Strip HTML tags from user input

### API Security
- **Server-Side Proxy**: Never expose Nominatim directly to browser
- **Rate Limiting**: Prevent abuse with token bucket algorithm
- **User-Agent**: Always send proper User-Agent header
- **Error Handling**: Don't leak internal system information

### Data Privacy
- **Location Data**: Store only what's necessary
- **User Consent**: Respect geolocation permissions
- **Data Retention**: Configurable cleanup policies

## 🚀 Performance Optimization

### Caching Strategy
- **Geocoding Results**: Cache for 24 hours
- **Coordinate Rounding**: Round to 5 decimal places for cache keys
- **Batch Operations**: Support for multiple location updates

### Database Optimization
- **Indexes**: On coordinates, city, country, and confidence
- **Query Optimization**: Efficient location lookups
- **Connection Pooling**: Database connection management

### Frontend Performance
- **Debounced Search**: 300ms delay to reduce API calls
- **Lazy Loading**: Load map components on demand
- **Virtual Scrolling**: For large search result lists

## 🔄 Extensibility

### Adding New Geocoding Providers

```python
class MapboxProvider(GeoProvider):
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    
    def search(self, query: str) -> List[PlaceCandidate]:
        # Implement Mapbox-specific search logic
        pass
    
    def reverse(self, lat: float, lon: float) -> Optional[PlaceCandidate]:
        # Implement Mapbox-specific reverse geocoding
        pass
```

### Custom Confidence Algorithms

```python
def calculate_custom_confidence(self, data: Dict[str, Any]) -> float:
    """Custom confidence calculation based on business rules"""
    base_confidence = 0.7
    
    # Add confidence based on data quality
    if data.get('address', {}).get('postcode'):
        base_confidence += 0.1
    
    if data.get('address', {}).get('house_number'):
        base_confidence += 0.1
    
    return min(0.95, base_confidence)
```

## 🐛 Troubleshooting

### Common Issues

1. **Rate Limiting (429)**
   - Check if multiple requests are being made
   - Implement exponential backoff
   - Verify User-Agent header

2. **Geocoding Failures**
   - Check Nominatim service status
   - Verify API endpoint URLs
   - Check network connectivity

3. **Map Display Issues**
   - Verify Leaflet CSS is loaded
   - Check tile server accessibility
   - Verify coordinate format

4. **Database Errors**
   - Run migrations: `python manage.py migrate`
   - Check database connection
   - Verify model field types

### Debug Mode

```python
# Enable debug logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'image_analysis.services.geocode': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📚 API Reference

### Models

#### StoryPlace
```python
class StoryPlace(models.Model):
    story_id = models.CharField(max_length=255, db_index=True)
    lat = models.FloatField(validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)])
    lon = models.FloatField(validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)])
    place_name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    admin = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    provider = models.CharField(max_length=50, default='nominatim')
    provider_place_id = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Services

#### GeoProvider
```python
class GeoProvider:
    def search(self, query: str) -> List[PlaceCandidate]
    def reverse(self, lat: float, lon: float) -> Optional[PlaceCandidate]
    def forward(self, city: str, country: str) -> Optional[PlaceCandidate]
```

### Serializers

#### PlaceCandidateSerializer
```python
class PlaceCandidateSerializer(serializers.Serializer):
    label = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    place_name = serializers.CharField()
    city = serializers.CharField()
    admin = serializers.CharField()
    country = serializers.CharField()
    country_code = serializers.CharField()
    provider = serializers.CharField()
    provider_place_id = serializers.CharField()
    confidence = serializers.FloatField()
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/location-enhancement`
3. **Make your changes**: Follow the coding standards
4. **Add tests**: Ensure all new functionality is tested
5. **Run tests**: `python manage.py test` and `npm test`
6. **Submit PR**: Include detailed description of changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenStreetMap**: For providing free map data and Nominatim service
- **Leaflet**: For the excellent open-source mapping library
- **Django**: For the robust web framework
- **React**: For the component-based UI library

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)

---

**Built with ❤️ for the LifeChronicles community**
