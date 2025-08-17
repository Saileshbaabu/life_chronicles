from rest_framework import serializers
from .models import StoryPlace


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image uploads."""
    image = serializers.ImageField(
        max_length=None,
        allow_empty_file=False,
        use_url=False
    )


class ImageAnalysisResponseSerializer(serializers.Serializer):
    """Serializer for image analysis responses."""
    img_caption = serializers.CharField()
    objects = serializers.ListField(child=serializers.CharField())
    ocr_text = serializers.CharField(allow_blank=True)
    gps = serializers.DictField(allow_null=True, required=False)
    datetime = serializers.CharField(allow_null=True, required=False)
    camera_model = serializers.CharField(allow_null=True, required=False)
    article = serializers.DictField(required=False)  # Now contains structured article data
    target_language = serializers.CharField(required=False, default='en')

class PlaceCandidateSerializer(serializers.Serializer):
    """Serializer for geocoding search results"""
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

class GeocodeSearchSerializer(serializers.Serializer):
    """Serializer for geocoding search requests"""
    query = serializers.CharField(max_length=120, required=True)

class GeocodeReverseSerializer(serializers.Serializer):
    """Serializer for reverse geocoding requests"""
    lat = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        required=True
    )
    lon = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        required=True
    )

class LocationUpdateSerializer(serializers.Serializer):
    """Serializer for updating story location"""
    lat = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        required=False
    )
    lon = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        required=False
    )
    place_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    admin = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country_code = serializers.CharField(max_length=2, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate that either coordinates or city/country are provided"""
        has_coords = data.get('lat') is not None and data.get('lon') is not None
        has_location = data.get('city') and data.get('country')
        
        if not has_coords and not has_location:
            raise serializers.ValidationError(
                "Either coordinates (lat, lon) or location (city, country) must be provided"
            )
        
        return data

class StoryPlaceSerializer(serializers.ModelSerializer):
    """Serializer for StoryPlace model"""
    place_str = serializers.CharField(read_only=True)
    
    class Meta:
        model = StoryPlace
        fields = [
            'id', 'lat', 'lon', 'place_name', 'city', 'admin', 
            'country', 'country_code', 'provider', 'provider_place_id',
            'confidence', 'source', 'created_at', 'updated_at', 'place_str'
        ]
        read_only_fields = ['id', 'provider', 'provider_place_id', 'created_at', 'updated_at']

class LocationResponseSerializer(serializers.Serializer):
    """Serializer for location update responses"""
    place_str = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    city = serializers.CharField()
    admin = serializers.CharField()
    country = serializers.CharField()
    country_code = serializers.CharField()
    confidence = serializers.FloatField()
    source = serializers.CharField()
