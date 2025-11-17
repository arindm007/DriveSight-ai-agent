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
import os

# Configure API key FIRST, before any model initialization
gemini_key = os.getenv("GEMINI_API_KEY")
if not gemini_key:
    raise ValueError("GEMINI_API_KEY not set")

genai.configure(api_key=gemini_key)

logger = setup_logger(__name__)

class VisionModel:
    """Wrapper for Gemini Vision multimodal API"""
        
    def __init__(self):
        """Initialize Gemini API client"""
        try:
            # Always force API key usage (NEVER OAuth in Cloud Run)
            gemini_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=gemini_key)

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


# """
# Vision model integration with Gemini Vision API (v1) -- modern code but sucks --- rate limit problem
# """

# import base64
# import json
# import re
# from typing import Dict, Any, Optional
# from google import genai   # ✅ NEW SDK
# from PIL import Image
# import io
# from .config import Config
# from .logger import setup_logger
# import os
# import time

# logger = setup_logger(__name__)

# # Configure client (v1 API, correct SDK)
# GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_KEY:
#     raise ValueError("GEMINI_API_KEY not set")

# client = genai.Client(api_key=GEMINI_KEY)   # ✅ v1 client


# # ---------- Retry Wrapper (prevents 429 crashes) ----------
# def safe_generate_content(model, contents, generation_config):
#     for i in range(4):  # retry 4 times
#         try:
#             return client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 generation_config=generation_config
#             )
#         except Exception as e:
#             if "429" in str(e) or "rate" in str(e).lower():
#                 wait = min(2 ** i, 8)
#                 logger.warning(f"Rate limit hit. Retrying in {wait}s ...")
#                 time.sleep(wait)
#             else:
#                 raise
#     raise RuntimeError("Max retries exceeded for Gemini generate_content()")


# class VisionModel:
#     """Wrapper for Gemini Vision multimodal API"""

#     def __init__(self):
#         """Initialize model name from config"""
#         # 💡 IMPORTANT:
#         # Config.GEMINI_MODEL MUST be "gemini-2.0-flash" (not preview)
#         self.model_name = Config.GEMINI_VISION_MODEL

#         logger.info(f"Using Gemini model: {self.model_name}")


#     # --------------------------------------------------------
#     # LOCAL IMAGE ANALYSIS
#     # --------------------------------------------------------
#     def analyze_image_local(self, image_data: bytes) -> Dict[str, Any]:

#         try:
#             # Validate image
#             image = Image.open(io.BytesIO(image_data))
#             logger.info(f"Image loaded - Size: {image.size}, Format: {image.format}")

#             prompt = self._build_analysis_prompt()

#             # Gemini v1 multimodal format → wrap bytes!!
#             image_part = {
#                 "mime_type": f"image/{image.format.lower()}",
#                 "data": image_data
#             }

#             # Order matters → image FIRST
#             contents = [
#                 image_part,
#                 prompt
#             ]

#             response = safe_generate_content(
#                 model=self.model_name,
#                 contents=contents,
#                 generation_config={
#                     "temperature": 0.2,
#                     "max_output_tokens": 1024,
#                 }
#             )

#             logger.info("Gemini Vision analysis completed")
#             return self._parse_gemini_response(response.text)

#         except Exception as e:
#             logger.error(f"Image analysis failed: {str(e)}")
#             return self._get_fallback_detection()


#     # --------------------------------------------------------
#     # GCS IMAGE ANALYSIS
#     # --------------------------------------------------------
#     def analyze_image_gcs(self, gcs_uri: str) -> Dict[str, Any]:

#         try:
#             logger.info(f"Analyzing image from GCS: {gcs_uri}")

#             prompt = self._build_analysis_prompt()

#             image_part = {
#                 "mime_type": "image/jpeg",
#                 "data": gcs_uri     # Gemini v1 DOES support gs:// directly
#             }

#             contents = [
#                 image_part,
#                 prompt
#             ]

#             response = safe_generate_content(
#                 model=self.model_name,
#                 contents=contents,
#                 generation_config={
#                     "temperature": 0.2,
#                     "max_output_tokens": 1024,
#                 }
#             )

#             logger.info("Gemini Vision GCS analysis completed")
#             return self._parse_gemini_response(response.text)

#         except Exception as e:
#             logger.error(f"GCS image analysis failed: {str(e)}")
#             return self._get_fallback_detection()


#     # --------------------------------------------------------
#     # PROMPT BUILDER
#     # --------------------------------------------------------
#     def _build_analysis_prompt(self) -> str:
#         return """Analyze this dashcam/road scene image for driving hazards and risk assessment.

# Respond ONLY with valid JSON (no markdown, no extra text) in this exact format:
# {
#   "detected_objects": [
#     {"label": "person", "confidence": 0.95, "position": "center-right"}
#   ],
#   "scene_analysis": {
#     "road_type": "city_street",
#     "lighting": "daylight",
#     "weather": "clear",
#     "traffic_density": "moderate"
#   },
#   "visibility_issues": ["none"],
#   "risk_factors": ["pedestrian_detected"]
# }
# """


#     # --------------------------------------------------------
#     # RESPONSE PARSER
#     # --------------------------------------------------------
#     def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:

#         try:
#             text = response_text.strip()

#             # Remove code fences if Gemini adds them
#             if text.startswith("```"):
#                 text = re.sub(r"```[a-zA-Z]*", "", text)
#                 text = text.replace("```", "")

#             data = json.loads(text)
#             logger.info(f"Parsed Gemini response with {len(data.get('detected_objects', []))} objects")
#             return data

#         except Exception as e:
#             logger.warning(f"Failed to parse Gemini JSON: {str(e)}")
#             logger.debug(f"Raw text: {response_text[:200]}")
#             return self._get_fallback_detection()


#     # --------------------------------------------------------
#     # FALLBACK
#     # --------------------------------------------------------
#     def _get_fallback_detection(self) -> Dict[str, Any]:
#         logger.warning("Using fallback detection")
#         return {
#             "detected_objects": [],
#             "scene_analysis": {
#                 "road_type": "unknown",
#                 "lighting": "unknown",
#                 "weather": "unknown",
#                 "traffic_density": "unknown"
#             },
#             "visibility_issues": ["analysis_failed"],
#             "risk_factors": []
#         }


# # Singleton instance
# _model = None

# def get_vision_model() -> VisionModel:
#     global _model
#     if _model is None:
#         _model = VisionModel()
#     return _model
