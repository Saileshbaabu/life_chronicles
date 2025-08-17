from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import math
import uuid

class Media(models.Model):
    """Stores uploaded images and their metadata"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='media/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    
    # EXIF data
    exif_datetime = models.DateTimeField(null=True, blank=True)
    exif_gps_lat = models.FloatField(null=True, blank=True)
    exif_gps_lon = models.FloatField(null=True, blank=True)
    exif_camera_model = models.CharField(max_length=100, blank=True)
    
    # Upload metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'media'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.id})"

class ImageAnalysis(models.Model):
    """Stores AI analysis results for images"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media = models.OneToOneField(Media, on_delete=models.CASCADE, related_name='analysis')
    
    # AI analysis results
    img_caption = models.TextField(blank=True)
    detected_objects = models.JSONField(default=list)
    attributes = models.JSONField(default=list)
    ocr_text = models.TextField(blank=True)
    
    # Location and time
    place = models.CharField(max_length=200, blank=True)
    place_confidence = models.FloatField(default=0.0)
    local_time = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=100, blank=True)
    
    # Additional context
    user_notes = models.TextField(blank=True)
    merged_notes_transcript = models.TextField(blank=True)
    
    # Analysis metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    ai_model = models.CharField(max_length=50, default='gpt-4o')
    
    class Meta:
        db_table = 'image_analysis'
        verbose_name_plural = 'Image analyses'
    
    def __str__(self):
        return f"Analysis for {self.media.original_filename}"

class Story(models.Model):
    """A day story combining multiple photos"""
    
    TONE_CHOICES = [
        ('reportage', 'Reportage'),
        ('travelogue', 'Travelogue'),
        ('diary', 'Diary'),
    ]
    
    LENGTH_CHOICES = [
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ta', 'Tamil'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lang = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='diary')
    length = models.CharField(max_length=10, choices=LENGTH_CHOICES, default='medium')
    
    # Story metadata
    story_date = models.DateField(null=True, blank=True)
    place_str = models.TextField(blank=True)
    place_confidence = models.FloatField(default=0.0)
    
    # Generated content
    json = models.JSONField(default=dict)
    
    # Timestamps and sharing
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    share_token = models.CharField(max_length=100, null=True, blank=True, unique=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'stories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Story {self.id} - {self.story_date or 'Unknown Date'}"
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

class StoryItem(models.Model):
    """Individual photos within a story, ordered by time"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='items')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='story_items')
    
    # Ordering and timing
    order_idx = models.PositiveIntegerField()
    local_time = models.CharField(max_length=5, blank=True)  # HH:MM format
    daypart = models.CharField(max_length=16, blank=True)  # morning, afternoon, evening, night
    
    class Meta:
        db_table = 'story_items'
        ordering = ['order_idx']
        unique_together = ['story', 'order_idx']
    
    def __str__(self):
        return f"{self.story.id} - Item {self.order_idx} ({self.daypart})"


class StoryPlace(models.Model):
    """Location information for a story/image"""
    
    SOURCE_CHOICES = [
        ('exif', 'EXIF GPS'),
        ('user_form', 'User Form'),
        ('search', 'Geocoding Search'),
        ('reverse', 'Reverse Geocoding'),
    ]
    
    story_id = models.CharField(max_length=255, db_index=True)
    
    lat = models.FloatField(
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)]
    )
    lon = models.FloatField(
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)]
    )
    
    place_name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    admin = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    
    provider = models.CharField(max_length=50, default='nominatim')
    provider_place_id = models.CharField(max_length=100, blank=True)
    
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.7
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='user_form')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'story_place'
        unique_together = ['story_id']
        indexes = [
            models.Index(fields=['lat', 'lon']),
            models.Index(fields=['city', 'country']),
            models.Index(fields=['confidence']),
        ]
    
    def __str__(self):
        return f"{self.place_name or self.city or 'Unknown'}, {self.country or 'Unknown'}"
    
    @property
    def place_str(self):
        parts = []
        if self.place_name:
            parts.append(self.place_name)
        elif self.city:
            parts.append(self.city)
        
        if self.admin and self.admin != self.city:
            parts.append(self.admin)
        
        if self.country:
            parts.append(self.country)
        
        return ", ".join(parts) if parts else ""
    
    def distance_to(self, other_lat, other_lon):
        return haversine_distance(self.lat, self.lon, other_lat, other_lon)


class Article(models.Model):
    """Generated article from image analysis"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ta', 'Tamil'),
    ]
    
    # Unique identifier for the article
    article_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Article content
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    image_caption = models.CharField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=500, blank=True)
    tags = models.JSONField(default=list)
    
    # Language and metadata
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    target_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    
    # Image information
    image_url = models.URLField(blank=True)
    image_alt = models.CharField(max_length=500, blank=True)
    
    # Analysis data
    img_caption = models.TextField(blank=True)
    detected_objects = models.JSONField(default=list)
    attributes = models.JSONField(default=list)
    ocr_text = models.TextField(blank=True)
    place = models.CharField(max_length=200, blank=True)
    place_confidence = models.FloatField(default=0.0)
    local_time = models.CharField(max_length=100, blank=True)
    season = models.CharField(max_length=100, blank=True)
    merged_notes_transcript = models.TextField(blank=True)
    
    # EXIF data
    exif_data = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'articles'
        indexes = [
            models.Index(fields=['article_id']),
            models.Index(fields=['language']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_language_display()})"
    
    @property
    def share_url(self):
        """Generate share URL for the article"""
        return f"https://lifechronicles.com/share/{self.article_id}"
    
    def to_pdf_data(self):
        """Convert to format expected by PDF builder"""
        return {
            'brand': 'LifeChronicles',
            'dateline': self.created_at.strftime('%A, %d %B %Y'),
            'section': 'Photo Feature',
            'title': self.title,
            'subtitle': self.subtitle,
            'body': self.body,
            'image_url': self.image_url,
            'image_alt': self.image_alt,
            'image_caption': self.image_caption,
            'tags': self.tags,
            'lang': self.language,
            'share_url': self.share_url
        }


def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return r * c
