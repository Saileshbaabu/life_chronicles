"""
Writer prompts service for generating day stories using LLM
"""
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Story generation prompt template
STORY_GENERATION_PROMPT = """
SYSTEM:
You are a careful nonfiction writer. Write ONLY in {lang}.
Use ONLY the data in STORY_INPUT. Do NOT invent places, people, events, brands, times, or numbers not present.
If a field is missing, omit it. No external facts or web knowledge.
Style: plain, observational, specific. No poetry unless present in captions/notes.
Language rule: if {lang} == "ta", translate descriptive English to Tamil; keep proper nouns in original script (Tamil transliteration optional once).
Place rule: If place_confidence < 0.8 or place_str is empty, do NOT mention a place name or local facts.

Structure & Order (hard constraints):
- Follow STORY_INPUT.dayparts_order exactly (e.g., morning → afternoon → evening → night).
- Intro: 2–3 sentences summarizing the day's visible arc only.
- Each section (per photo): 2–4 short sentences, grounded in that photo's fields only.
- Section heading: ≤ 5 words.
- Outro: 1–2 sentences to close the day; no new facts.

OUTPUT_SCHEMA (return ONLY valid JSON in this shape):
{
  "title": "string (≤ 8 words)",
  "subtitle": "string (≤ 15 words)",
  "intro_md": "string",
  "sections": [
    {
      "media_id": "string",
      "section_heading": "string",
      "body_md": "string",
      "image_caption": "string (1–2 sentences; visible details only)",
      "alt_text": "string (20–40 words; descriptive)",
      "tags": ["string","string","string"]
    }
  ],
  "outro_md": "string"
}

USER:
Write the story in {lang} using ONLY STORY_INPUT below. Keep sections ordered by daypart; keep language consistent.

STORY_INPUT:
{STORY_INPUT_JSON}
"""

# Story verification prompt template
STORY_VERIFIER_PROMPT = """
SYSTEM:
You remove hallucinations. Return ONLY corrected JSON in the same schema as the generator output.

USER:
Given STORY_INPUT and MODEL_OUTPUT:
1) Remove any detail not present in STORY_INPUT (no added places/people/brands/history/times).
2) If place_confidence < 0.8, remove place mentions.
3) Ensure sections are in STORY_INPUT.dayparts_order and mapped to the correct media_id.
4) Ensure the language is {lang} throughout.
5) Keep schema exactly the same.

STORY_INPUT:
{STORY_INPUT_JSON}

MODEL_OUTPUT:
{MODEL_OUTPUT_JSON}
"""

def llm_generate(prompt: str, payload: Dict[str, Any]) -> str:
    """
    Stub function for LLM generation. This will be replaced with actual LLM integration.
    
    Args:
        prompt: Prompt template string
        payload: Dictionary with values to format into the prompt
        
    Returns:
        Generated text response
    """
    try:
        # Format the prompt with payload values
        formatted_prompt = prompt.format(**payload)
        
        # For now, return a mock response
        # In production, this would call the actual LLM API
        logger.info("LLM generation called with prompt template")
        
        # Mock response for testing
        if "STORY_GENERATION_PROMPT" in prompt:
            return _generate_mock_story(payload.get('lang', 'en'))
        elif "STORY_VERIFIER_PROMPT" in prompt:
            return _generate_mock_verification(payload.get('MODEL_OUTPUT_JSON', '{}'))
        else:
            return "Mock LLM response"
            
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}")
        raise

def generate_story(story_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a story using the two-pass approach (generation + verification).
    
    Args:
        story_input: Story input dictionary
        
    Returns:
        Generated story JSON
    """
    try:
        # Step 1: Generate initial story
        gen_payload = {
            "lang": story_input["lang"],
            "STORY_INPUT_JSON": json.dumps(story_input, ensure_ascii=False, indent=2)
        }
        
        gen_response = llm_generate(STORY_GENERATION_PROMPT, gen_payload)
        logger.info("Initial story generation completed")
        
        # Step 2: Verify and correct the story
        verifier_payload = {
            "lang": story_input["lang"],
            "STORY_INPUT_JSON": json.dumps(story_input, ensure_ascii=False, indent=2),
            "MODEL_OUTPUT_JSON": gen_response
        }
        
        verified_response = llm_generate(STORY_VERIFIER_PROMPT, verifier_payload)
        logger.info("Story verification completed")
        
        # Parse the verified response
        try:
            story_json = json.loads(verified_response)
            return story_json
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse verified story JSON: {e}")
            # Fallback to parsing the original generation
            try:
                story_json = json.loads(gen_response)
                return story_json
            except json.JSONDecodeError:
                logger.error("Both generation and verification failed to produce valid JSON")
                raise
                
    except Exception as e:
        logger.error(f"Error in story generation: {e}")
        raise

def _generate_mock_story(lang: str) -> str:
    """Generate a mock story for testing purposes."""
    if lang == 'ta':
        return json.dumps({
            "title": "ஒரு நாள் பயணம்",
            "subtitle": "புகைப்படங்களில் பதிவு செய்யப்பட்ட நினைவுகள்",
            "intro_md": "இந்த நாள் நாம் பல இடங்களுக்கு சென்றோம். ஒவ்வொரு புகைப்படமும் ஒரு கதையை சொல்கிறது.",
            "sections": [
                {
                    "media_id": "mock-1",
                    "section_heading": "காலை நேரம்",
                    "body_md": "காலை 7 மணிக்கு நாம் வீட்டை விட்டு புறப்பட்டோம்.",
                    "image_caption": "காலை வெயில் படிந்த வீடு",
                    "alt_text": "காலை நேரத்தில் எடுக்கப்பட்ட வீட்டின் புகைப்படம்",
                    "tags": ["காலை", "வீடு", "வெயில்"]
                }
            ],
            "outro_md": "இந்த நாள் முழுவதும் நாம் அனுபவித்தவை மறக்க முடியாதவை."
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "title": "A Day's Journey",
            "subtitle": "Memories captured in photographs",
            "intro_md": "Today we traveled to many places. Each photograph tells a story.",
            "sections": [
                {
                    "media_id": "mock-1",
                    "section_heading": "Morning Time",
                    "body_md": "At 7 AM we left home to begin our journey.",
                    "image_caption": "House in morning sunlight",
                    "alt_text": "Photograph of house taken in the morning",
                    "tags": ["morning", "house", "sunlight"]
                }
            ],
            "outro_md": "What we experienced throughout this day is unforgettable."
        })

def _generate_mock_verification(model_output: str) -> str:
    """Generate a mock verification response for testing."""
    try:
        # Try to parse the model output and return it as-is for now
        parsed = json.loads(model_output)
        return json.dumps(parsed, ensure_ascii=False)
    except:
        # Return a simple mock if parsing fails
        return json.dumps({
            "title": "Verified Story",
            "subtitle": "Verified subtitle",
            "intro_md": "Verified introduction",
            "sections": [],
            "outro_md": "Verified conclusion"
        })
