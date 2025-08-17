import base64
import logging
import uuid
from typing import Dict, Any, Optional
from django.conf import settings
from openai import OpenAI
from .models import Article

logger = logging.getLogger(__name__)


class AIService:
    """Service class for AI image analysis using OpenAI GPT-4o."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    def encode_image_to_base64(self, image_path):
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            raise
    
    def analyze_image(self, image_path):
        """
        Analyze image using OpenAI GPT-4o Vision API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: Analysis results containing caption, objects, and OCR text
        """
        try:
            # Encode image to base64
            base64_image = self.encode_image_to_base64(image_path)
            
            # Prepare the prompt for the AI model
            prompt = """
            IMPORTANT: Analyze ONLY what you can actually see in this image. Do NOT make up or imagine content that is not visible.
            
            Look carefully at the image and provide:
            
            1. A POETIC and evocative caption (1-2 sentences) that captures the mood, atmosphere, and essence of what you see
            2. A list of ALL visible objects, people, animals, buildings, or items you can identify
            3. Any text that is visible in the image (OCR)
            
            CAPTION REQUIREMENTS - Make it POETIC and ARTISTIC:
            - Write in a lyrical, poetic style
            - Use vivid, descriptive language and imagery
            - Capture the emotional tone and atmosphere
            - Make it engaging and evocative
            - Focus on visual beauty, colors, light, and composition
            - Use metaphors and artistic descriptions when appropriate
            - Keep it grounded in what you actually see
            
            EXAMPLES of poetic style:
            - "Golden hour paints the cityscape in warm amber hues, where shadows dance between skyscrapers"
            - "A solitary tree stands sentinel against the vast expanse of rolling hills"
            - "Morning mist weaves through ancient stone, whispering secrets of centuries past"
            - "Sunlight filters through leaves, creating a mosaic of light and shadow on the forest floor"
            
            CRITICAL RULES:
            - Base your poetic description ONLY on what is actually visible
            - Do NOT invent fictional elements or contexts
            - Use artistic language to describe REAL visual elements
            - If you cannot clearly see something, say "unclear" or "not visible"
            - Be specific about colors, shapes, light, and visible elements
            
            Please format your response as:
            Caption: [your poetic caption here]
            Objects: [list only visible objects]
            OCR Text: [any visible text, or "No text visible" if none]
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            
            # Extract information from AI response
            caption = ""
            objects = []
            ocr_text = ""
            
            # Log the raw AI response for debugging
            logger.info(f"Raw AI response: {ai_response}")
            
            lines = ai_response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Caption:'):
                    caption = line.replace('Caption:', '').strip()
                elif line.startswith('Objects:'):
                    objects_str = line.replace('Objects:', '').strip()
                    objects = [obj.strip() for obj in objects_str.split(',') if obj.strip()]
                elif line.startswith('OCR Text:'):
                    ocr_text = line.replace('OCR Text:', '').strip()
                    if ocr_text == "No text visible":
                        ocr_text = ""
            
            # Ensure we have at least some content, but be more specific
            if not caption or caption == "Image analysis completed":
                caption = "Unable to generate specific caption - image content unclear"
            if not objects or objects == ["image"] or objects == ["content unclear"]:
                # Generate descriptive objects based on the caption
                if "dusk" in caption.lower() or "twilight" in caption.lower():
                    objects = ["sky", "twilight", "atmosphere", "lighting", "mood"]
                elif "branch" in caption.lower() or "tree" in caption.lower():
                    objects = ["tree", "branch", "nature", "outdoors", "landscape"]
                elif "cityscape" in caption.lower() or "city" in caption.lower():
                    objects = ["city", "buildings", "urban", "architecture", "skyline"]
                else:
                    objects = ["visual elements", "composition", "atmosphere", "mood", "scene"]
            if not ocr_text:
                ocr_text = ""
            
            result = {
                'img_caption': caption,
                'objects': objects,
                'ocr_text': ocr_text
            }
            
            logger.info(f"Parsed AI result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image with AI: {e}")
            raise
    
    def generate_article(self, image_analysis, exif_data, target_language='en', retry_count=0):
        """
        Generate a comprehensive multilingual article from image analysis and EXIF data.
        
        Args:
            image_analysis: Dict containing img_caption, objects, ocr_text
            exif_data: Dict containing GPS, datetime, camera_model
            target_language: Language code ('en' for English, 'ta' for Tamil)
            retry_count: Number of retry attempts (internal use)
            
        Returns:
            dict: JSON with title, subtitle, body_md, image_caption, alt_text, tags
        """
        try:
            # Pre-process and sanitize input data to prevent language mixing
            sanitized_analysis = self._sanitize_input_data(image_analysis, target_language)
            
            # Use sanitized data for article generation
            image_analysis = sanitized_analysis
            # Prepare context information
            location_context = ""
            if exif_data.get('gps_decimal'):
                lat = exif_data['gps_decimal']['lat']
                lon = exif_data['gps_decimal']['lon']
                location_context = f"Location: {lat}°{'N' if lat >= 0 else 'S'}, {lon}°{'E' if lon >= 0 else 'W'}"
            
            time_context = ""
            if exif_data.get('DateTime'):
                time_context = f"Date: {exif_data['DateTime']}"
            
            camera_context = ""
            if exif_data.get('Model'):
                camera_context = f"Camera: {exif_data['Model']}"
            
            # Language consistency is now handled in the main prompt
            
            # Build the prompt with new structured constraints
            prompt = f"""
            SYSTEM:
            You are a careful nonfiction writer. Write ONLY in {target_language}.
            Use ONLY the details in INPUT. Do NOT invent places, people, events, brands, or dates.
            If something is missing, omit it. No external facts or web knowledge.

            Style rules:
            - Observational, vivid, and specific—but factual.
            - Do NOT copy the caption verbatim; do not reuse more than 6 consecutive words from it.
            - Weave in 2–4 concrete visual elements from Objects/Attributes naturally.
            - Smooth narrative paragraphs (no lists, no headings inside body).
            - Tone: reportage  (e.g., reportage | travelogue | diary)
            - Target length: 100–150 words total.

            Place guard:
            If {image_analysis.get('place_confidence', 0.0)} < 0.8 or Place is empty → do NOT mention a location name or local facts.

            Language rules:
            - Keep the entire output in {target_language}.
            - If {target_language} == "ta" (Tamil), translate any English descriptive text into Tamil;
              keep proper nouns in their original script (optionally add a Tamil transliteration once).

            OUTPUT_SCHEMA (return ONLY valid JSON exactly like this):
            {{
              "title": "string (4–8 words)",
              "subtitle": "string (10–15 words, 1 sentence)",
              "body": "string (2–4 paragraphs; plain prose; **bold**/*italic* allowed)",
              "image_caption": "string (1–2 sentences, 15–30 words; describe only visible elements)",
              "alt_text": "string (20–40 words; purely descriptive for accessibility)",
              "tags": ["string", "string", "string"]   // 3–5 grounded tags
            }}

            USER:
            Write an article that respects all rules above.

            INPUT:
            - Visual caption: {image_analysis.get('img_caption', 'N/A')}
            - Objects: {image_analysis.get('objects', [])}
            - Attributes: {image_analysis.get('attributes', [])}
            - OCR text: {image_analysis.get('ocr_text', 'N/A')}
            - Place: {image_analysis.get('place', 'N/A')} (confidence: {image_analysis.get('place_confidence', 0.0)})
            - Local time: {image_analysis.get('local_time', 'N/A')}
            - Season: {image_analysis.get('season', 'N/A')}
            - User context (optional): {image_analysis.get('merged_notes_transcript', 'N/A')}

            Additional constraints:
            - If User context is provided, prioritize those facts; otherwise stay purely observational.
            - Avoid clichés and repetition; vary sentence openings.
            - Tags must come from Objects/Attributes/clearly visible details.
            Return ONLY the JSON specified in OUTPUT_SCHEMA.
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,  # Increased for longer articles
                temperature=0.7
            )
            
            # Get the response
            article_json = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                import json
                article_data = json.loads(article_json)
                
                # Validate required fields
                required_fields = ['title', 'subtitle', 'body', 'image_caption', 'alt_text', 'tags']
                for field in required_fields:
                    if field not in article_data:
                        logger.warning(f"Missing required field: {field}")
                        if field == 'tags':
                            article_data[field] = []
                        elif field == 'body':
                            article_data[field] = "Content generation failed."
                        else:
                            article_data[field] = f"Missing {field}"
                
                # Language validation - ensure consistency
                if target_language == 'ta':
                    # Check if any field contains English content
                    english_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'like', 'against', 'fading', 'blush', 'day', 'whispers', 'across', 'horizon', 'cityscape', 'glimmers', 'jeweled', 'tapestry']
                    for field_name, field_value in article_data.items():
                        if isinstance(field_value, str):
                            # Check for English words
                            field_lower = field_value.lower()
                            if any(word in field_lower for word in english_words):
                                logger.warning(f"Field {field_name} contains English content: {field_value}")
                                # Force regeneration in Tamil
                                if retry_count < 2:  # Allow up to 2 retries
                                    logger.info(f"Retrying article generation (attempt {retry_count + 1})")
                                    return self.generate_article(image_analysis, exif_data, target_language, retry_count + 1)
                                else:
                                    raise Exception(f"Language mixing detected in {field_name} after {retry_count} retries")
                        elif isinstance(field_value, list):
                            # Check tags for English
                            for tag in field_value:
                                if isinstance(tag, str) and any(word in tag.lower() for word in english_words):
                                    logger.warning(f"Tags contain English content: {tag}")
                                    if retry_count < 2:  # Allow up to 2 retries
                                        logger.info(f"Retrying article generation (attempt {retry_count + 1})")
                                        return self.generate_article(image_analysis, exif_data, target_language, retry_count + 1)
                                    else:
                                        raise Exception("Language mixing detected in tags after {retry_count} retries")
                
                logger.info(f"Generated article successfully in {target_language}: {article_data}")
                return article_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Raw response: {article_json}")
                
                # Return fallback structure with generated content
                if target_language == 'ta':
                    # Translate English caption to Tamil for consistency
                    tamil_caption = image_analysis.get('img_caption', 'வர்ணிக்கப்பட்ட காட்சி')
                    if tamil_caption and not any(word in ['வர்ணிக்கப்பட்ட', 'காட்சி', 'படம்', 'இந்த', 'ஒரு'] for word in tamil_caption.lower().split()):
                        # If caption is in English, translate key concepts to Tamil
                        tamil_caption = (tamil_caption.replace('twilight', 'அந்தி நேரம்')
                                                   .replace('horizon', 'அடிவானம்')
                                                   .replace('city', 'நகரம்')
                                                   .replace('lights', 'விளக்குகள்')
                                                   .replace('buildings', 'கட்டிடங்கள்')
                                                   .replace('trees', 'மரங்கள்')
                                                   .replace('clouds', 'மேகங்கள்')
                                                   .replace('sky', 'வானம்')
                                                   .replace('sunset', 'சூரிய அஸ்தமனம்'))
                    
                    return {
                        'title': 'பட பகுப்பாய்வு கட்டுரை',
                        'subtitle': 'படத்தின் காட்சி விளக்கத்தின் அடிப்படையில்',
                        'body': f"""இந்த படத்தில் {tamil_caption} காணப்படுகிறது. படத்தின் காட்சி மற்றும் சூழ்நிலை கவனிக்கப்படுகிறது. இது ஒரு காட்சியை வழங்குகிறது.

படத்தின் காட்சி அமைப்பு காணப்படுகிறது. ஒவ்வொரு கூறும் காட்சியில் உள்ளது. வெளிச்சம், நிழல் மற்றும் வடிவங்கள் காட்சியில் காணப்படுகின்றன.

இந்த படம் ஒரு காட்சியை காட்டுகிறது. இது காட்சியை கைப்பற்றுகிறது. இது காட்சியை வழங்குகிறது.""",
                        'image_caption': tamil_caption,
                        'alt_text': tamil_caption,
                        'tags': ['காட்சி', 'படம்', 'வர்ணனை']
                    }
                else:
                    return {
                        'title': 'Image Analysis Article',
                        'subtitle': 'Based on visual description',
                        'body': f"""This image shows {image_analysis.get('img_caption', 'a visual scene')}. The visual elements and atmosphere are observed in the image. This provides a view of the scene.

The visual composition is present in the image. Each element is visible in the scene. Light, shadow, and forms are observed in the scene.

This image displays a scene. It captures the scene. It provides the scene.""",
                        'image_caption': image_analysis.get('img_caption', ''),
                        'alt_text': image_analysis.get('img_caption', ''),
                        'tags': ['visual', 'image', 'description']
                    }
                    
        except Exception as e:
            logger.error(f"Error generating article: {e}")
            raise
    
    def _sanitize_input_data(self, image_analysis, target_language):
        """
        Pre-process input data to prevent language mixing and clean OCR errors.
        Translates descriptive English content to Tamil while preserving proper nouns.
        """
        sanitized = image_analysis.copy()
        
        if target_language == 'ta':
            # Clean and translate English captions to Tamil
            caption = sanitized.get('img_caption', '')
            if caption:
                # Remove gibberish and nonsensical fragments
                caption = self._clean_gibberish(caption)
                
                # Translate descriptive English words while preserving proper nouns
                caption = self._translate_to_tamil_preserving_proper_nouns(caption)
                
                if caption.strip():
                    sanitized['img_caption'] = caption
                else:
                    sanitized['img_caption'] = 'காட்சி விளக்கம்'
            
            # Clean and translate OCR text
            ocr_text = sanitized.get('ocr_text', '')
            if ocr_text:
                ocr_text = self._clean_gibberish(ocr_text)
                ocr_text = self._translate_to_tamil_preserving_proper_nouns(ocr_text)
                sanitized['ocr_text'] = ocr_text
            
            # Translate English objects to Tamil
            objects = sanitized.get('objects', [])
            if objects:
                tamil_objects = []
                for obj in objects:
                    if isinstance(obj, str):
                        tamil_obj = self._translate_to_tamil_preserving_proper_nouns(obj)
                        tamil_objects.append(tamil_obj)
                    else:
                        tamil_objects.append(obj)
                sanitized['objects'] = tamil_objects
        
        return sanitized
    
    def _clean_gibberish(self, text):
        """
        Remove gibberish, nonsensical fragments, and OCR errors from text.
        """
        if not text:
            return text
        
        # Common OCR errors and gibberish patterns
        gibberish_patterns = [
            r'\b[a-z]{1,2}\b',  # Single or double letter fragments
            r'\b[a-z]{15,}\b',  # Very long nonsense words
            r'\b[a-z]*[0-9]+[a-z]*\b',  # Mixed alphanumeric nonsense
            r'\b[a-z]*[!@#$%^&*()]+[a-z]*\b',  # Mixed with symbols
        ]
        
        import re
        cleaned_text = text
        
        for pattern in gibberish_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Remove extra spaces and clean up
        cleaned_text = ' '.join(cleaned_text.split())
        return cleaned_text.strip()
    
    def _translate_to_tamil_preserving_proper_nouns(self, text):
        """
        Use deterministic translator system to convert English to Tamil.
        First masks proper nouns, then translates, then restores proper nouns.
        """
        if not text:
            return text
        
        # Step 1: Identify and mask proper nouns
        masked_text, proper_nouns = self._mask_proper_nouns(text)
        
        # Step 2: Use AI translator to convert masked text to Tamil
        tamil_text = self._ai_translate_masked_text(masked_text)
        
        # Step 3: Restore proper nouns from masks
        final_text = self._restore_proper_nouns(tamil_text, proper_nouns)
        
        return final_text
    
    def _mask_proper_nouns(self, text):
        """
        Identify and mask proper nouns in English text.
        Returns (masked_text, proper_nouns_dict)
        """
        import re
        
        # Patterns for proper nouns
        proper_noun_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized words (e.g., "New York")
            r'\b[A-Z]{2,}\b',  # All caps (e.g., "USA", "NASA")
            r'\b\d+[A-Za-z]+\b',  # Numbers + letters (e.g., "iPhone 14")
            r'\b[A-Za-z]+\d+\b',  # Letters + numbers (e.g., "Windows 11")
        ]
        
        masked_text = text
        proper_nouns = {}
        mask_counter = 0
        
        for pattern in proper_noun_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                proper_noun = match.group()
                mask = f"§§PN{mask_counter}§§"
                proper_nouns[mask] = proper_noun
                masked_text = masked_text.replace(proper_noun, mask)
                mask_counter += 1
        
        return masked_text, proper_nouns
    
    def _ai_translate_masked_text(self, masked_text):
        """
        Use AI to translate masked English text to Tamil.
        """
        try:
            prompt = f"""
            SYSTEM:
            You are a deterministic translator. Translate English → Tamil.
            Rules:
            - Do NOT add, remove, or embellish information.
            - Keep only proper nouns in English; everything else must be Tamil.
            - Leave any masked tokens exactly as-is (format: §§PN0§§, §§PN1§§ …).
            - Return plain Tamil text only.

            USER:
            Translate this to Tamil, preserving masks:
            {masked_text}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for deterministic translation
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI translation failed: {e}")
            # Fallback: basic word replacement
            return self._basic_english_to_tamil_fallback(masked_text)
    
    def _basic_english_to_tamil_fallback(self, text):
        """
        Basic fallback translation if AI fails.
        """
        # Common English to Tamil translations
        basic_translations = {
            'the': '', 'a': '', 'an': '', 'and': 'மற்றும்', 'or': 'அல்லது',
            'but': 'ஆனால்', 'in': 'இல்', 'on': 'மேல்', 'at': 'இல்',
            'to': 'க்கு', 'for': 'க்காக', 'of': 'ஆன', 'with': 'உடன்',
            'by': 'மூலம்', 'as': 'போல', 'like': 'போன்ற', 'against': 'எதிராக',
            'twilight': 'அந்தி நேரம்', 'horizon': 'அடிவானம்', 'cityscape': 'நகரக் காட்சி',
            'glimmers': 'மின்னுகிறது', 'jeweled': 'நவரத்தின', 'tapestry': 'துணி',
            'fading': 'மங்கும்', 'blush': 'சிவப்பு', 'day': 'பகல்',
            'whispers': 'மெதுவாக பரவுகிறது', 'across': 'முழுவதும்',
            'city': 'நகரம்', 'buildings': 'கட்டிடங்கள்', 'lights': 'விளக்குகள்',
            'sky': 'வானம்', 'clouds': 'மேகங்கள்', 'trees': 'மரங்கள்',
            'grass': 'புல்', 'water': 'நீர்', 'mountains': 'மலைகள்',
            'road': 'சாலை', 'car': 'கார்', 'people': 'மக்கள்',
            'sun': 'சூரியன்', 'moon': 'சந்திரன்', 'stars': 'நட்சத்திரங்கள்'
        }
        
        # Simple word replacement
        result = text
        for english, tamil in basic_translations.items():
            result = result.replace(f' {english} ', f' {tamil} ')
            result = result.replace(f'{english} ', f'{tamil} ')
            result = result.replace(f' {english}', f' {tamil}')
            result = result.replace(english, tamil)
        
        return result
    
    def _restore_proper_nouns(self, tamil_text, proper_nouns):
        """
        Restore proper nouns from masks in Tamil text.
        """
        result = tamil_text
        
        for mask, proper_noun in proper_nouns.items():
            result = result.replace(mask, proper_noun)
        
        return result
    
    def save_article(self, article_data: Dict[str, Any], image_analysis: Dict[str, Any], exif_data: Dict[str, Any], target_language: str, image_url: str = None) -> str:
        """
        Save generated article to database.
        
        Args:
            article_data: Generated article data
            image_analysis: Image analysis results
            exif_data: EXIF metadata
            target_language: Target language for the article
            image_url: URL or path to the uploaded image
            
        Returns:
            str: Article ID
        """
        try:
            # Generate unique article ID
            article_id = str(uuid.uuid4())
            
            # Create article object
            article = Article(
                article_id=article_id,
                title=article_data.get('title', ''),
                subtitle=article_data.get('subtitle', ''),
                body=article_data.get('body', ''),
                image_caption=article_data.get('image_caption', ''),
                alt_text=article_data.get('alt_text', ''),
                tags=article_data.get('tags', []),
                language=target_language,
                target_language=target_language,
                image_url=image_url or '',  # Save the actual image URL
                image_alt=article_data.get('alt_text', ''),
                img_caption=image_analysis.get('img_caption', ''),
                detected_objects=image_analysis.get('objects', []),
                attributes=image_analysis.get('attributes', []),
                ocr_text=image_analysis.get('ocr_text', ''),
                place=image_analysis.get('place', ''),
                place_confidence=image_analysis.get('place_confidence', 0.0),
                local_time=image_analysis.get('local_time', ''),
                season=image_analysis.get('season', ''),
                merged_notes_transcript=image_analysis.get('merged_notes_transcript', ''),
                exif_data=exif_data
            )
            
            # Save to database
            article.save()
            
            logger.info(f"Article saved successfully with ID: {article_id}")
            return article_id
            
        except Exception as e:
            logger.error(f"Failed to save article: {e}")
            raise
