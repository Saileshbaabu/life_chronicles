import logging
import json
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .serializers import (
    ImageUploadSerializer, ImageAnalysisResponseSerializer,
    PlaceCandidateSerializer, GeocodeSearchSerializer, GeocodeReverseSerializer,
    LocationUpdateSerializer, StoryPlaceSerializer, LocationResponseSerializer
)
from .ai_service import AIService
from .utils import extract_exif_data, save_image_to_temp, cleanup_temp_file
from .services.geocode import geocoding_provider
from .models import StoryPlace, Article
import os

logger = logging.getLogger(__name__)


def index_view(request):
    """
    Frontend view for the image analysis interface.
    """
    return render(request, 'image_analysis/index.html')


class RegenerateArticleView(APIView):
    """
    API view for regenerating articles with additional location context.
    """
    
    def post(self, request):
        try:
            data = request.data
            city = data.get('city', '')
            country = data.get('country', '')
            coordinates = data.get('coordinates', '')
            original_analysis = data.get('original_analysis', '')
            
            # Create location context
            location_context = ""
            if city and country:
                location_context = f"Location: {city}, {country}"
            elif city:
                location_context = f"Location: {city}"
            elif coordinates:
                location_context = f"Coordinates: {coordinates}"
            
            # Initialize AI service and regenerate article
            ai_service = AIService()
            
            # Create enhanced prompt with location
            enhanced_prompt = f"""
            CRITICAL: Create an article based ONLY on the ACTUAL image analysis provided. Do NOT invent fictional content.
            
            Image Analysis (REAL DATA ONLY):
            {original_analysis}
            
            Additional Location Context:
            {location_context}
            
            ARTICLE REQUIREMENTS:
            1. Start with the poetic caption and build upon it artistically
            2. If location is provided, include relevant cultural/historical context
            3. Keep the narrative grounded in the actual image content
            4. Do NOT invent people, places, or events not in the image
            5. Maintain the poetic, artistic tone from the caption
            
            WRITING STYLE:
            - Begin with the poetic description and expand it naturally
            - Use the same artistic, evocative language style
            - Create a flowing narrative that builds from the visual elements
            - Keep it grounded in reality while being artistically expressive
            
            RULES:
            - Base everything on the provided analysis
            - Do NOT invent fictional narratives
            - If analysis is minimal, keep the article brief but poetic
            - Focus on what you can reasonably infer from the visible content
            - Maintain artistic language throughout
            
            Write in first person, but keep it realistic and based on the actual image.
            """
            
            # Call OpenAI API for enhanced article generation
            response = ai_service.client.chat.completions.create(
                model=ai_service.model,
                messages=[
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            enhanced_article = response.choices[0].message.content.strip()
            
            return Response({
                'success': True,
                'article': enhanced_article,
                'location_context': location_context
            })
            
        except Exception as e:
            logger.error(f"Error regenerating article: {e}")
            return Response(
                {'error': 'Failed to regenerate article', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageAnalysisView(APIView):
    """
    API view for analyzing uploaded images.
    
    Accepts multipart/form-data with an 'image' field.
    Returns analysis results including AI-generated caption, objects, OCR text,
    and EXIF metadata (GPS, datetime, camera model).
    """
    
    parser_classes = (MultiPartParser,)
    
    def post(self, request):
        """
        Handle POST request for image analysis.
        
        Returns:
            Response: JSON containing image analysis results
        """
        try:
            # Validate input
            serializer = ImageUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid input', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OpenAI API key is configured
            if not settings.OPENAI_API_KEY:
                return Response(
                    {'error': 'OpenAI API key not configured'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get the uploaded image
            image_file = serializer.validated_data['image']
            
            # Save image to temporary directory
            temp_image_path = save_image_to_temp(image_file)
            
            try:
                # Extract EXIF data
                exif_data = extract_exif_data(temp_image_path)
                
                # Debug: Log what EXIF data was found
                logger.info(f"EXIF data extracted: {exif_data}")
                logger.info(f"GPS data: {exif_data.get('gps_decimal')}")
                logger.info(f"DateTime: {exif_data.get('DateTime')}")
                logger.info(f"Model: {exif_data.get('Model')}")
                
                # Initialize AI service and analyze image
                ai_service = AIService()
                ai_results = ai_service.analyze_image(temp_image_path)
                
                # Get target language from request (default to English)
                target_language = request.data.get('target_language', 'en')
                if target_language not in ['en', 'ta']:
                    target_language = 'en'  # Default to English if invalid
                
                # Generate article from the analysis in the specified language
                try:
                    article_data = ai_service.generate_article(ai_results, exif_data, target_language)
                    logger.info(f"Generated article in {target_language}: {article_data}")
                    
                    # Save article to database
                    try:
                        # Save the actual file path for the uploaded image
                        # In production, you'd upload to cloud storage and get a real URL
                        article_id = ai_service.save_article(article_data, ai_results, exif_data, target_language, temp_image_path)
                        logger.info(f"Article saved to database with ID: {article_id}")
                        # Add article ID to response for PDF generation
                        article_data['article_id'] = article_id
                    except Exception as save_error:
                        logger.warning(f"Failed to save article to database: {save_error}")
                        # Continue without saving - article generation was successful
                        
                except Exception as e:
                    logger.warning(f"Article generation failed: {e}")
                    # Create fallback article structure
                    if target_language == 'ta':
                        article_data = {
                            'title': 'பட பகுப்பாய்வு கட்டுரை',
                            'subtitle': 'கட்டுரை உருவாக்கம் கிடைக்கவில்லை',
                            'body': 'இந்த படத்திற்கான கட்டுரை உருவாக்கம் கிடைக்கவில்லை.',
                            'image_caption': ai_results.get('img_caption', ''),
                            'alt_text': ai_results.get('img_caption', ''),
                            'tags': ai_results.get('objects', [])[:5]
                        }
                    else:
                        article_data = {
                            'title': 'Image Analysis Article',
                            'subtitle': 'Article generation unavailable',
                            'body': 'Article generation unavailable for this image.',
                            'image_caption': ai_results.get('img_caption', ''),
                            'alt_text': ai_results.get('img_caption', ''),
                            'tags': ai_results.get('objects', [])[:5]
                        }
                
                # Clean EXIF data to remove null characters and invalid data
                def clean_exif_value(value):
                    if value is None:
                        return None
                    # Convert to string and remove null characters
                    cleaned = str(value).replace('\x00', '').strip()
                    return cleaned if cleaned else None
                
                # Prepare response data with new structure
                response_data = {
                    'img_caption': ai_results['img_caption'],
                    'objects': ai_results['objects'],
                    'ocr_text': ai_results['ocr_text'],
                    'gps': exif_data.get('gps_decimal'),
                    'datetime': clean_exif_value(exif_data.get('DateTime')),
                    'camera_model': clean_exif_value(exif_data.get('Model')),
                    'article': article_data,  # Now contains the full JSON structure
                    'target_language': target_language
                }
                
                # Log response data for debugging
                logger.info(f"Response data before validation: {response_data}")
                
                # Validate response data
                response_serializer = ImageAnalysisResponseSerializer(data=response_data)
                if response_serializer.is_valid():
                    # Ensure proper content type header
                    response = Response(response_data, status=status.HTTP_200_OK)
                    response['Content-Type'] = 'application/json'
                    logger.info(f"Returning successful response with content type: {response['Content-Type']}")
                    return response
                else:
                    logger.error(f"Response validation failed: {response_serializer.errors}")
                    logger.error(f"Response data that failed validation: {response_data}")
                    return Response(
                        {'error': 'Response validation failed', 'details': response_serializer.errors},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
            finally:
                # Clean up temporary file
                cleanup_temp_file(temp_image_path)
                
        except Exception as e:
            logger.error(f"Error processing image analysis request: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return Response(
                {'error': 'Internal server error', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GeocodeSearchView(APIView):
    """Handle geocoding search requests"""
    
    def post(self, request):
        serializer = GeocodeSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        
        try:
            # Search for places
            candidates = geocoding_provider.search(query)
            
            # Serialize results
            results = [PlaceCandidateSerializer(candidate).data for candidate in candidates]
            
            return Response(results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Geocoding search error: {e}")
            return Response(
                {'error': 'Geocoding service temporarily unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

class GeocodeReverseView(APIView):
    """Handle reverse geocoding requests"""
    
    def post(self, request):
        serializer = GeocodeReverseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        lat = serializer.validated_data['lat']
        lon = serializer.validated_data['lon']
        
        try:
            # Reverse geocode coordinates
            candidate = geocoding_provider.reverse(lat, lon)
            
            if not candidate:
                return Response(
                    {'error': 'No location found for these coordinates'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Serialize result
            result = PlaceCandidateSerializer(candidate).data
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return Response(
                {'error': 'Geocoding service temporarily unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

class StoryLocationView(APIView):
    """Handle story location updates and retrieval"""
    
    def get(self, request, story_id):
        """Get current location for a story"""
        try:
            story_place = StoryPlace.objects.get(story_id=story_id)
            serializer = StoryPlaceSerializer(story_place)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except StoryPlace.DoesNotExist:
            return Response(
                {'error': 'No location found for this story'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, story_id):
        """Update or create location for a story"""
        serializer = LocationUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        lat = data.get('lat')
        lon = data.get('lon')
        city = data.get('city', '').strip()
        country = data.get('country', '').strip()
        
        try:
            # Get or create StoryPlace
            story_place, created = StoryPlace.objects.get_or_create(
                story_id=story_id,
                defaults={
                    'lat': 0.0,
                    'lon': 0.0,
                    'source': 'user_form'
                }
            )
            
            # If only city/country provided, forward geocode to get coordinates
            if not lat and not lon and city and country:
                candidate = geocoding_provider.forward(city, country)
                if candidate:
                    lat = candidate.lat
                    lon = candidate.lon
                    # Update fields with geocoded data
                    data.update({
                        'place_name': candidate.place_name,
                        'city': candidate.city,
                        'admin': candidate.admin,
                        'country': candidate.country,
                        'country_code': candidate.country_code,
                        'provider': candidate.provider,
                        'provider_place_id': candidate.provider_place_id,
                    })
                    confidence = 0.7  # Base confidence for forward geocoding
                else:
                    return Response(
                        {'error': 'Could not find coordinates for the specified city and country'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif lat and lon and city and country:
                # Both coordinates and city/country provided - cross-check
                candidate = geocoding_provider.forward(city, country)
                if candidate:
                    # Calculate distance between provided coords and geocoded coords
                    distance = story_place.distance_to(candidate.lat, candidate.lon)
                    if distance > 20:  # 20km threshold
                        return Response(
                            {'error': 'Location text does not match coordinates, please adjust'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    confidence = 0.85  # High confidence for cross-checked data
                else:
                    confidence = 0.8  # Medium confidence if forward geocoding fails
            elif lat and lon:
                # Only coordinates provided - reverse geocode for place details
                candidate = geocoding_provider.reverse(lat, lon)
                if candidate:
                    data.update({
                        'place_name': candidate.place_name,
                        'city': candidate.city,
                        'admin': candidate.admin,
                        'country': candidate.country,
                        'country_code': candidate.country_code,
                        'provider': candidate.provider,
                        'provider_place_id': candidate.provider_place_id,
                    })
                    confidence = 0.85  # High confidence for reverse geocoding
                else:
                    confidence = 0.8  # Medium confidence if reverse geocoding fails
            else:
                confidence = 0.7  # Base confidence
            
            # Update the StoryPlace object
            for field, value in data.items():
                if value is not None:
                    setattr(story_place, field, value)
            
            story_place.confidence = confidence
            story_place.save()
            
            # Prepare response
            response_data = {
                'place_str': story_place.place_str,
                'lat': story_place.lat,
                'lon': story_place.lon,
                'city': story_place.city,
                'admin': story_place.admin,
                'country': story_place.country,
                'country_code': story_place.country_code,
                'confidence': story_place.confidence,
                'source': story_place.source,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Location update error: {e}")
            return Response(
                {'error': 'Failed to update location'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SwitchLanguageView(APIView):
    """
    API view for switching article language without re-uploading image.
    """
    
    def post(self, request):
        try:
            data = request.data
            target_language = data.get('target_language')
            
            if not target_language or target_language not in ['en', 'ta']:
                return Response(
                    {'error': 'Invalid target language. Must be "en" or "ta"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the analysis data from request
            analysis_data = {
                'img_caption': data.get('img_caption', ''),
                'objects': data.get('objects', []),
                'attributes': data.get('attributes', []),
                'ocr_text': data.get('ocr_text', ''),
                'place': data.get('place', ''),
                'local_time': data.get('local_time', ''),
                'season': data.get('season', ''),
                'merged_notes_transcript': data.get('merged_notes_transcript', ''),
                'gps': data.get('gps', None)
            }
            
            # Initialize AI service
            ai_service = AIService()
            
            # Generate article in new language
            article = ai_service.generate_article(
                analysis_data, 
                {},  # Empty exif data since we're not using image
                target_language=target_language
            )
            
            if not article:
                return Response(
                    {'error': 'Failed to generate article in new language'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Prepare response
            response_data = {
                'article': article,
                'target_language': target_language,
                'img_caption': analysis_data['img_caption'],
                'objects': analysis_data['objects'],
                'attributes': analysis_data['attributes'],
                'ocr_text': analysis_data['ocr_text'],
                'place': analysis_data['place'],
                'local_time': analysis_data['local_time'],
                'season': analysis_data['season'],
                'merged_notes_transcript': analysis_data['merged_notes_transcript'],
                'gps': analysis_data['gps']
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Language switch error: {e}")
            return Response(
                {'error': f'Failed to switch language: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
