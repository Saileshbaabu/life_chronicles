"""
Stories API endpoints for creating and managing day stories
"""
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from ..models import Story, StoryItem, Media, ImageAnalysis
from ..services.story_input import build_story_input
from ..services.writer_prompts import generate_story

logger = logging.getLogger(__name__)

class StoriesView(APIView):
    """
    API view for creating and managing stories
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create a new story from multiple media items
        """
        try:
            # Extract request data
            media_ids = request.data.get('media_ids', [])
            lang = request.data.get('lang', 'en')
            tone = request.data.get('tone', 'diary')
            length = request.data.get('length', 'medium')
            place_override = request.data.get('place_override')
            
            # Validate required fields
            if not media_ids:
                return Response(
                    {'error': 'media_ids is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate choices
            valid_langs = ['en', 'ta']
            valid_tones = ['reportage', 'travelogue', 'diary']
            valid_lengths = ['short', 'medium', 'long']
            
            if lang not in valid_langs:
                return Response(
                    {'error': f'Invalid lang. Must be one of: {valid_langs}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if tone not in valid_tones:
                return Response(
                    {'error': f'Invalid tone. Must be one of: {valid_tones}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if length not in valid_lengths:
                return Response(
                    {'error': f'Invalid length. Must be one of: {valid_lengths}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Fetch media and analysis data
            media_list = self._fetch_media_with_analysis(media_ids, request.user)
            
            if not media_list:
                return Response(
                    {'error': 'No valid media found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Build place context
            place_ctx = self._build_place_context(media_list, place_override)
            
            # Build story input
            story_input = build_story_input(media_list, place_ctx, lang, tone, length)
            
            # Generate story using LLM
            story_json = generate_story(story_input)
            
            # Create story and story items in database
            with transaction.atomic():
                story = self._create_story(request.user, story_input, story_json)
                self._create_story_items(story, media_list, story_input)
            
            logger.info(f"Created story {story.id} with {len(media_list)} photos")
            
            return Response({
                'story_id': str(story.id),
                'story_json': story_json,
                'message': 'Story created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating story: {e}")
            return Response(
                {'error': f'Failed to create story: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _fetch_media_with_analysis(self, media_ids: List[str], user: User) -> List[Dict[str, Any]]:
        """
        Fetch media items with their analysis data
        """
        media_list = []
        
        for media_id in media_ids:
            try:
                # Get media item
                media = get_object_or_404(Media, id=media_id, user=user)
                
                # Get analysis if it exists
                try:
                    analysis = ImageAnalysis.objects.get(media=media)
                    analysis_data = {
                        'img_caption': analysis.img_caption,
                        'detected_objects': analysis.detected_objects,
                        'attributes': analysis.attributes,
                        'ocr_text': analysis.ocr_text,
                        'place': analysis.place,
                        'place_confidence': analysis.place_confidence,
                        'local_time': analysis.local_time,
                        'season': analysis.season,
                        'user_notes': analysis.user_notes,
                        'merged_notes_transcript': analysis.merged_notes_transcript,
                    }
                except ImageAnalysis.DoesNotExist:
                    analysis_data = {}
                
                # Build media item with analysis
                media_item = {
                    'id': str(media.id),
                    'image_url': media.image.url if media.image else '',
                    'alt_text': media.original_filename,
                    'exif_datetime': media.exif_datetime,
                    'uploaded_at': media.uploaded_at,
                    'analysis': analysis_data
                }
                
                media_list.append(media_item)
                
            except Exception as e:
                logger.warning(f"Failed to fetch media {media_id}: {e}")
                continue
        
        return media_list
    
    def _build_place_context(self, media_list: List[Dict[str, Any]], place_override: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Build place context from media analysis or override
        """
        if place_override:
            return {
                'place_str': place_override.get('place_str', ''),
                'confidence': place_override.get('confidence', 0.0),
                'lat': place_override.get('lat'),
                'lon': place_override.get('lon'),
                'timezone': place_override.get('timezone')
            }
        
        # Find the media item with highest place confidence
        best_place = None
        best_confidence = 0.0
        
        for media_item in media_list:
            analysis = media_item.get('analysis', {})
            confidence = analysis.get('place_confidence', 0.0)
            
            if confidence > best_confidence and analysis.get('place'):
                best_confidence = confidence
                best_place = analysis.get('place')
        
        if best_place and best_confidence > 0.0:
            return {
                'place_str': best_place,
                'confidence': best_confidence,
                'lat': None,  # Would need to extract from analysis if available
                'lon': None,
                'timezone': None
            }
        
        # Default place context
        return {
            'place_str': '',
            'confidence': 0.0,
            'lat': None,
            'lon': None,
            'timezone': None
        }
    
    def _create_story(self, user: User, story_input: Dict[str, Any], story_json: Dict[str, Any]) -> Story:
        """
        Create a Story object in the database
        """
        story_date = None
        if story_input.get('story_date'):
            try:
                story_date = date.fromisoformat(story_input['story_date'])
            except ValueError:
                logger.warning(f"Invalid story date: {story_input['story_date']}")
        
        story = Story.objects.create(
            user=user,
            lang=story_input['lang'],
            tone=story_input['tone'],
            length=story_input['length'],
            story_date=story_date,
            place_str=story_input['place_str'],
            place_confidence=story_input['place_confidence'],
            json=story_json
        )
        
        return story
    
    def _create_story_items(self, story: Story, media_list: List[Dict[str, Any]], story_input: Dict[str, Any]):
        """
        Create StoryItem objects for each media item
        """
        for idx, media_item in enumerate(media_list):
            # Find corresponding photo data from story input
            photo_data = next(
                (p for p in story_input['photos'] if p['media_id'] == media_item['id']), 
                None
            )
            
            if photo_data:
                StoryItem.objects.create(
                    story=story,
                    media_id=media_item['id'],
                    order_idx=idx,
                    local_time=photo_data.get('local_time', ''),
                    daypart=photo_data.get('daypart', '')
                )

class StoryDetailView(APIView):
    """
    API view for retrieving individual stories
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, story_id):
        """
        Get a story by ID
        """
        try:
            story = get_object_or_404(Story, id=story_id, user=request.user)
            
            return Response({
                'story_id': str(story.id),
                'story_json': story.json,
                'created_at': story.created_at,
                'updated_at': story.updated_at
            })
            
        except Exception as e:
            logger.error(f"Error retrieving story {story_id}: {e}")
            return Response(
                {'error': f'Failed to retrieve story: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StoryShareView(APIView):
    """
    API view for sharing stories
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, story_id):
        """
        Share a story and return share token
        """
        try:
            story = get_object_or_404(Story, id=story_id, user=request.user)
            
            # Make story public
            story.is_public = True
            story.save()
            
            return Response({
                'share_token': story.share_token,
                'share_url': f"/share/{story.share_token}",
                'message': 'Story shared successfully'
            })
            
        except Exception as e:
            logger.error(f"Error sharing story {story_id}: {e}")
            return Response(
                {'error': f'Failed to share story: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
