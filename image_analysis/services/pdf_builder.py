"""
PDF Builder Service for generating article PDFs.
Handles layout, fonts, images, and multilingual support.
"""
import os
import logging
import requests
from io import BytesIO
from datetime import datetime
from typing import Dict, Optional, Tuple

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from ..utils.md_to_paragraphs import convert_markdown_to_paragraphs, create_tamil_style

logger = logging.getLogger(__name__)

# Visual constants
COLORS = {
    'INK': HexColor('#111111'),
    'MUTED': HexColor('#6B6B6B'),
    'ACCENT': HexColor('#B30D0D'),
    'CHIP_BG': HexColor('#EEE'),
    'RULE': HexColor('#B30D0D'),
}

SPACING = {
    'gap_small': 6,
    'gap': 10,
    'gap_large': 16,
    'gap_xl': 24,
}

FONTS = {
    'title': 22,
    'subtitle': 14,
    'body': 11.5,
    'caption': 9.5,
    'header': 10,
    'tag': 9,
}

# Page sizes
PAGE_SIZES = {
    'letter': letter,
    'a4': A4,
}

# Font paths (relative to app directory)
FONT_PATHS = {
    'PlayfairDisplay': 'static/fonts/PlayfairDisplay-Regular.ttf',
    'PlayfairDisplayBold': 'static/fonts/PlayfairDisplay-Bold.ttf',
    'NotoSerifTamil': 'static/fonts/NotoSerifTamil-Regular.ttf',
}


class TagChip(Flowable):
    """Custom flowable for rendering tag chips."""
    
    def __init__(self, text, width=0, height=0):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height
    
    def draw(self):
        canvas = self.canv
        # Draw rounded rectangle background
        canvas.setFillColor(COLORS['CHIP_BG'])
        canvas.roundRect(0, 0, self.width, self.height, radius=4, fill=1)
        # Draw text
        canvas.setFillColor(COLORS['INK'])
        canvas.setFont('Helvetica', FONTS['tag'])
        canvas.drawCentredString(self.width/2, self.height/2 - 3, self.text)


class PDFBuilder:
    """PDF Builder for generating article PDFs."""
    
    def __init__(self):
        self.fonts_registered = False
        self._register_fonts()
    
    def _register_fonts(self):
        """Register custom fonts."""
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Get app directory
            from django.conf import settings
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Register Playfair Display
            playfair_path = os.path.join(app_dir, FONT_PATHS['PlayfairDisplay'])
            if os.path.exists(playfair_path):
                pdfmetrics.registerFont(TTFont('PlayfairDisplay', playfair_path))
                logger.info("PlayfairDisplay font registered successfully")
            else:
                logger.warning("PlayfairDisplay font not found, using fallback")
            
            # Register Playfair Display Bold
            playfair_bold_path = os.path.join(app_dir, FONT_PATHS['PlayfairDisplayBold'])
            if os.path.exists(playfair_bold_path):
                pdfmetrics.registerFont(TTFont('PlayfairDisplayBold', playfair_bold_path))
                logger.info("PlayfairDisplayBold font registered successfully")
            else:
                logger.warning("PlayfairDisplayBold font not found, using fallback")
            
            # Register Noto Serif Tamil
            tamil_path = os.path.join(app_dir, FONT_PATHS['NotoSerifTamil'])
            if os.path.exists(tamil_path):
                pdfmetrics.registerFont(TTFont('NotoSerifTamil', tamil_path))
                logger.info("Noto Serif Tamil font registered successfully")
            else:
                logger.warning("Noto Serif Tamil font not found, using fallback")
            
            # Only mark as registered if at least some fonts were found
            if any(os.path.exists(os.path.join(app_dir, path)) for path in FONT_PATHS.values()):
                self.fonts_registered = True
            else:
                self.fonts_registered = False
                logger.warning("No custom fonts found, using system fallbacks")
            
        except Exception as e:
            logger.error(f"Font registration failed: {e}")
            self.fonts_registered = False
    
    def _get_font_name(self, element_type: str, language: str) -> str:
        """Get appropriate font name based on element type and language."""
        if language == 'ta':
            if element_type == 'title':
                return 'NotoSerifTamil' if self.fonts_registered else 'Helvetica-Bold'
            elif element_type in ['subtitle', 'body', 'caption']:
                return 'NotoSerifTamil' if self.fonts_registered else 'Helvetica'
            else:
                return 'Helvetica'
        else:
            if element_type == 'title':
                return 'PlayfairDisplayBold' if self.fonts_registered else 'Helvetica-Bold'
            elif element_type == 'subtitle':
                return 'PlayfairDisplay' if self.fonts_registered else 'Helvetica'
            else:
                return 'PlayfairDisplay' if self.fonts_registered else 'Helvetica'
    
    def _download_image(self, image_url: str, timeout: int = 10) -> Optional[BytesIO]:
        """Download image from URL or load from local file."""
        try:
            # Handle local file paths (direct paths) - check first
            if os.path.exists(image_url):
                logger.info(f"Loading local file: {image_url}")
                with open(image_url, 'rb') as f:
                    image_data = BytesIO(f.read())
                    image_data.seek(0)
                    return image_data
            
            # Handle local file URLs (file:// protocol)
            if image_url.startswith('file://'):
                file_path = image_url.replace('file://', '')
                if os.path.exists(file_path):
                    logger.info(f"Loading local file from file:// URL: {file_path}")
                    with open(file_path, 'rb') as f:
                        image_data = BytesIO(f.read())
                        image_data.seek(0)
                        return image_data
                else:
                    logger.warning(f"Local file not found: {file_path}")
                    return None
            
            # Handle regular HTTP URLs - only if it looks like a URL
            if image_url.startswith(('http://', 'https://')):
                logger.info(f"Downloading from URL: {image_url}")
                response = requests.get(image_url, stream=True, timeout=timeout)
                response.raise_for_status()

                image_data = BytesIO()
                for chunk in response.iter_content(chunk_size=8192):
                    image_data.write(chunk)
                image_data.seek(0)

                return image_data
            else:
                logger.warning(f"Invalid URL format: {image_url}")
                return None

        except Exception as e:
            logger.error(f"Failed to download/load image {image_url}: {e}")
            return None
    
    def _create_header(self, canvas_obj, article: Dict, page_width: float, margin: float):
        """Create the header with brand, dateline, and section."""
        y_position = page_width - margin - 20
        
        # Brand (left)
        canvas_obj.setFont('Helvetica-Bold', FONTS['header'])
        canvas_obj.setFillColor(COLORS['INK'])
        canvas_obj.drawString(margin, y_position, article.get('brand', 'LifeChronicles'))
        
        # Dateline (center)
        dateline = article.get('dateline', datetime.now().strftime('%A, %d %B %Y'))
        canvas_obj.setFont('Helvetica', FONTS['header'])
        canvas_obj.setFillColor(COLORS['MUTED'])
        canvas_obj.drawCentredString(page_width / 2, y_position, dateline)
        
        # Section (right)
        section = article.get('section', 'Photo Feature')
        canvas_obj.setFont('Helvetica', FONTS['header'])
        canvas_obj.setFillColor(COLORS['ACCENT'])
        canvas_obj.drawRightString(page_width - margin, y_position, section)
        
        # Accent line
        canvas_obj.setStrokeColor(COLORS['RULE'])
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(margin, y_position - 5, page_width - margin, y_position - 5)
        
        return y_position - 25  # Return next Y position
    
    def _create_title_subtitle(self, story, article: Dict, language: str, margin: float, page_width: float, y_start: float):
        """Create title and subtitle."""
        elements = []
        
        # Title
        title_font = self._get_font_name('title', language)
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=title_font,
            fontSize=FONTS['title'],
            alignment=TA_CENTER,
            spaceAfter=SPACING['gap_small'],
            textColor=COLORS['INK'],
        )
        
        title = Paragraph(article.get('title', 'Untitled'), title_style)
        elements.append(title)
        elements.append(Spacer(1, SPACING['gap_small']))
        
        # Subtitle
        subtitle_font = self._get_font_name('subtitle', language)
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            fontName=subtitle_font,
            fontSize=FONTS['subtitle'],
            alignment=TA_CENTER,
            spaceAfter=SPACING['gap_large'],
            textColor=COLORS['MUTED'],
        )
        
        subtitle = article.get('subtitle', '')
        if subtitle:
            subtitle_para = Paragraph(subtitle, subtitle_style)
            elements.append(subtitle_para)
            elements.append(Spacer(1, SPACING['gap_large']))
        
        return elements, y_start - 60  # Approximate height
    
    def _create_body_content(self, story, article: Dict, language: str, margin: float, page_width: float, y_start: float, image_height: float):
        """Create body content with proper frame sizing."""
        elements = []
        
        # Calculate available height for body (reserve space for image)
        available_height = y_start - margin - image_height - 100  # 100 for caption + footer
        
        # Body text
        body_font = self._get_font_name('body', language)
        body_text = article.get('body', '')
        
        if body_text:
            # Convert markdown to paragraphs
            if language == 'ta':
                body_paragraphs = convert_markdown_to_paragraphs(
                    body_text, 'Normal', body_font, FONTS['body']
                )
            else:
                body_paragraphs = convert_markdown_to_paragraphs(
                    body_text, 'Normal', body_font, FONTS['body']
                )
            
            elements.extend(body_paragraphs)
        
        return elements
    
    def _create_tags(self, story, article: Dict, language: str, margin: float, page_width: float):
        """Create tags row."""
        elements = []
        
        tags = article.get('tags', [])
        if not tags:
            return elements
        
        # Tags label
        label_style = ParagraphStyle(
            'TagsLabel',
            fontName='Helvetica',
            fontSize=FONTS['tag'],
            textColor=COLORS['MUTED'],
            spaceAfter=SPACING['gap_small'],
        )
        
        label = Paragraph("Tags:", label_style)
        elements.append(label)
        
        # Tag chips
        chip_width = 80
        chip_height = 20
        x_position = margin
        y_spacing = 25
        
        for tag in tags[:5]:  # Max 5 tags
            if x_position + chip_width > page_width - margin:
                # Move to next row
                x_position = margin
                y_spacing += 30
            
            chip = TagChip(tag, chip_width, chip_height)
            chip.x = x_position
            chip.y = y_spacing
            elements.append(chip)
            
            x_position += chip_width + 10
        
        elements.append(Spacer(1, SPACING['gap_large']))
        return elements
    
    def _create_image_and_caption(self, story, article: Dict, language: str, margin: float, page_width: float, page_height: float):
        """Create image and caption at the bottom."""
        elements = []
        
        # Image
        image_url = article.get('image_url')
        image_data = None
        
        if image_url:
            image_data = self._download_image(image_url)
        
        if image_data:
            try:
                # Calculate image dimensions
                img_width = page_width - (2 * margin)
                img_height = img_width * 0.75  # Approximate aspect ratio
                
                # Create image
                img = Image(image_data, width=img_width, height=img_height)
                img.hAlign = 'CENTER'
                elements.append(img)
                
                # Caption
                caption_font = self._get_font_name('caption', language)
                caption_style = ParagraphStyle(
                    'Caption',
                    fontName=caption_font,
                    fontSize=FONTS['caption'],
                    alignment=TA_CENTER,
                    textColor=COLORS['MUTED'],
                    spaceAfter=SPACING['gap'],
                )
                
                caption = article.get('image_caption', '')
                if caption:
                    caption_para = Paragraph(caption, caption_style)
                    elements.append(caption_para)
                
                return elements, img_height
                
            except Exception as e:
                logger.error(f"Failed to process image: {e}")
                # Fall through to placeholder
        
        # Placeholder if image fails
        placeholder_height = 200
        elements.append(Spacer(1, placeholder_height))
        
        # Placeholder text
        placeholder_style = ParagraphStyle(
            'Placeholder',
            fontName='Helvetica',
            fontSize=FONTS['caption'],
            alignment=TA_CENTER,
            textColor=COLORS['MUTED'],
        )
        
        placeholder = Paragraph("Image unavailable", placeholder_style)
        elements.append(placeholder)
        
        return elements, placeholder_height
    
    def _create_footer(self, canvas_obj, article: Dict, page_width: float, page_height: float, margin: float):
        """Create footer with URL/QR and page number."""
        y_position = margin + 20
        
        # Left side: URL or QR code
        share_url = article.get('share_url', '')
        if share_url:
            try:
                # Try to generate QR code
                import qrcode
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(share_url)
                qr.make(fit=True)
                
                # Create QR image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                # Draw QR code
                canvas_obj.drawImage(qr_buffer, margin, y_position - 80, width=80, height=80)
                
            except ImportError:
                # Fallback to text
                canvas_obj.setFont('Helvetica', 8)
                canvas_obj.setFillColor(COLORS['MUTED'])
                canvas_obj.drawString(margin, y_position, f"Share: {share_url}")
        else:
            # App URL
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.setFillColor(COLORS['MUTED'])
            canvas_obj.drawString(margin, y_position, "LifeChronicles")
        
        # Right side: Page number
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(COLORS['MUTED'])
        canvas_obj.drawRightString(page_width - margin, y_position, "Page 1")
    
    def generate_article_pdf(self, article: Dict, page_size: str = 'letter') -> bytes:
        """
        Generate PDF for a single article.
        
        Args:
            article (Dict): Article data dictionary
            page_size (str): Page size ('letter' or 'a4')
        
        Returns:
            bytes: PDF content as bytes
        """
        try:
            # Validate page size
            if page_size not in PAGE_SIZES:
                page_size = 'letter'
            
            # Get page dimensions
            page_width, page_height = PAGE_SIZES[page_size]
            margin = 0.75 * inch
            
            # Create buffer for PDF
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=PAGE_SIZES[page_size],
                leftMargin=margin,
                rightMargin=margin,
                topMargin=margin,
                bottomMargin=margin
            )
            
            # Get language
            language = article.get('lang', 'en')
            
            # Ensure fonts are properly registered before proceeding
            if not self.fonts_registered:
                logger.warning("Custom fonts not available, using system fallbacks")
            
            # Calculate image height first (reserve space at bottom)
            image_url = article.get('image_url')
            image_height = 0
            if image_url:
                image_data = self._download_image(image_url)
                if image_data:
                    img_width = page_width - (2 * margin)
                    image_height = img_width * 0.75  # Approximate aspect ratio
            
            # Build story elements
            story = []
            
            # Title and Subtitle
            title_elements, y_position = self._create_title_subtitle(
                story, article, language, margin, page_width, page_height - margin - 20
            )
            story.extend(title_elements)
            
            # Body content
            body_elements = self._create_body_content(
                story, article, language, margin, page_width, y_position, image_height
            )
            story.extend(body_elements)
            
            # Tags
            tag_elements = self._create_tags(story, article, language, margin, page_width)
            story.extend(tag_elements)
            
            # Image and caption (at bottom)
            image_elements, actual_image_height = self._create_image_and_caption(
                story, article, language, margin, page_width, page_height
            )
            story.extend(image_elements)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise


# Global instance
pdf_builder = PDFBuilder()
