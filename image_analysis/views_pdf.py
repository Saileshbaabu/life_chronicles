"""
PDF Views for generating article PDFs.
"""
import logging
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.text import slugify
from urllib.parse import urlparse

from .models import StoryPlace, Article
from .services.pdf_builder import pdf_builder

logger = logging.getLogger(__name__)


class ArticlePDFView(APIView):
    """
    API view for generating PDFs from articles.
    """
    # permission_classes = [IsAuthenticated]  # Temporarily disabled for testing
    
    def get(self, request, story_id):
        """
        Generate PDF for a story/article.
        
        Query parameters:
        - size: 'a4' or 'letter' (default: 'letter')
        - inline: '1' to view in browser, otherwise download
        
        Returns:
        - PDF file as attachment or inline
        - 404 if story not found
        - 400 if required fields missing
        """
        try:
            # Get page size from query params
            page_size = request.query_params.get('size', 'letter')
            if page_size not in ['a4', 'letter']:
                page_size = 'letter'
            
            # Check if inline view is requested
            inline = request.query_params.get('inline', '0') == '1'
            
            # For now, we'll create a sample article since we don't have the full article model
            # In production, you'd fetch this from your database
            article_data = self._get_article_data(story_id, request.user)
            
            if not article_data:
                return Response(
                    {'error': 'Story not found or access denied'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate required fields
            required_fields = ['title', 'body', 'lang']
            missing_fields = [field for field in required_fields if not article_data.get(field)]
            
            if missing_fields:
                return Response(
                    {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate PDF
            pdf_content = pdf_builder.generate_article_pdf(article_data, page_size)
            
            # Create filename
            title = article_data.get('title', 'Untitled')
            filename = f"{slugify(title)}.pdf"
            
            # Create response
            response = HttpResponse(pdf_content, content_type='application/pdf')
            
            if inline:
                response['Content-Disposition'] = f'inline; filename="{filename}"'
            else:
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Set cache headers
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
            
        except Exception as e:
            logger.error(f"PDF generation failed for story {story_id}: {e}")
            return Response(
                {'error': 'Failed to generate PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_article_data(self, story_id, user):
        """
        Get article data for PDF generation.
        """
        try:
            # Try to fetch article by article_id first
            article = Article.objects.filter(article_id=story_id).first()
            
            if article:
                # Convert to PDF format
                return article.to_pdf_data()
            
            # If not found by article_id, try to find by title (for backward compatibility)
            article = Article.objects.filter(title__icontains=story_id).first()
            
            if article:
                return article.to_pdf_data()
            
            # If still not found, return None (will trigger 404)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get article data for {story_id}: {e}")
            return None


class ArticlePDFViewTamil(ArticlePDFView):
    """
    Tamil version of the PDF view for testing.
    """
    
    def _get_article_data(self, story_id, user):
        """
        Get Tamil article data for PDF generation.
        """
        try:
            # Try to fetch Tamil article by article_id first
            article = Article.objects.filter(article_id=story_id, language='ta').first()
            
            if article:
                # Convert to PDF format
                return article.to_pdf_data()
            
            # If not found by article_id, try to find by title (for backward compatibility)
            article = Article.objects.filter(title__icontains=story_id, language='ta').first()
            
            if article:
                return article.to_pdf_data()
            
            # If still not found, return None (will trigger 404)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get Tamil article data for {story_id}: {e}")
            return None
