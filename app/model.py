"""
Vision model integration with Gemini Vision API
"""
import base64
import json
import re
from typing import Dict, Any, Optional
import google.generativeai as genai
from PIL import Image
import io
from .config import Config
from .logger import setup_logger

logger = setup_logger(__name__)

class VisionModel:
    """Wrapper for Gemini Vision multimodal API"""
    
    def __init__(self):
        """Initialize Gemini API client"""
        try:
            genai.configure()  # Uses GOOGLE_APPLICATION_CREDENTIALS
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            logger.info(f"Gemini Vision model initialized: {Config.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def analyze_image_local(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image using Gemini Vision API (local file)
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Structured detection results
        """
        try:
            # Convert bytes to PIL Image for validation
            image = Image.open(io.BytesIO(image_data))
            
            logger.info(f"Image loaded - Size: {image.size}, Format: {image.format}")
            
            # Prepare prompt for Gemini
            prompt = self._build_analysis_prompt()
            
            # Call Gemini Vision API with image data
            response = self.model.generate_content(
                [
                    prompt,
                    image
                ],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1024,
                }
            )
            
            logger.info("Gemini Vision analysis completed")
            
            # Parse response
            return self._parse_gemini_response(response.text)
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            # Return graceful fallback
            return self._get_fallback_detection()

    def analyze_image_gcs(self, gcs_uri: str) -> Dict[str, Any]:
        """
        Analyze image from GCS URI
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            
        Returns:
            Structured detection results
        """
        try:
            logger.info(f"Analyzing image from GCS: {gcs_uri}")
            
            # Prepare prompt
            prompt = self._build_analysis_prompt()
            
            # Call Gemini with GCS URI
            response = self.model.generate_content(
                [
                    prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": gcs_uri  # Gemini supports gs:// URIs directly
                    }
                ],
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1024,
                }
            )
            
            logger.info("Gemini Vision GCS analysis completed")
            return self._parse_gemini_response(response.text)
            
        except Exception as e:
            logger.error(f"GCS image analysis failed: {str(e)}")
            return self._get_fallback_detection()

    def _build_analysis_prompt(self) -> str:
        """Build prompt for Gemini Vision analysis"""
        return """Analyze this dashcam/road scene image for driving hazards and risk assessment.

Respond ONLY with valid JSON (no markdown, no extra text) in this exact format:
{
  "detected_objects": [
    {"label": "person", "confidence": 0.95, "position": "center-right"},
    {"label": "vehicle", "confidence": 0.92, "position": "ahead"}
  ],
  "scene_analysis": {
    "road_type": "city_street",
    "lighting": "daylight",
    "weather": "clear",
    "traffic_density": "moderate"
  },
  "visibility_issues": ["none"],
  "risk_factors": [
    "pedestrian_detected",
    "oncoming_traffic"
  ]
}

Guidelines:
- Detected objects: list person, vehicle, bicycle, motorcycle, animal, etc.
- Road types: highway, city_street, rural_road, parking_lot, unknown
- Lighting: daylight, dawn_dusk, night, artificial_light
- Weather: clear, rain, fog, snow, cloudy
- Traffic density: light, moderate, heavy
- Visibility: no_issues, weather_related, lighting_related, obstructed_view
- Risk factors: identify specific hazards (e.g., pedestrian_detected, speeding_zone, construction, wet_road)
- Be concise and factual. Do not hallucinate objects not visible."""

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response into structured format
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed detection results
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            # Parse JSON
            data = json.loads(text.strip())
            
            logger.info(f"Successfully parsed Gemini response with {len(data.get('detected_objects', []))} objects")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:200]}")
            return self._get_fallback_detection()

    def _get_fallback_detection(self) -> Dict[str, Any]:
        """Return fallback detection when API fails"""
        logger.warning("Using fallback detection")
        return {
            "detected_objects": [],
            "scene_analysis": {
                "road_type": "unknown",
                "lighting": "unknown",
                "weather": "unknown",
                "traffic_density": "unknown"
            },
            "visibility_issues": ["analysis_failed"],
            "risk_factors": []
        }


# Singleton instance
_model = None

def get_vision_model() -> VisionModel:
    """Get or create vision model singleton"""
    global _model
    if _model is None:
        _model = VisionModel()
    return _model
