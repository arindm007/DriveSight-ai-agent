"""
ADK (Autonomous Driving Knowledge) Agent - Risk assessment and workflow orchestration
"""
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import google.generativeai as genai
from .config import Config
from .logger import setup_logger
import os

# Configure API key FIRST
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
else:
    raise ValueError("GEMINI_API_KEY not set")


logger = setup_logger(__name__)

class ADKAgent:
    """Autonomous Driving Knowledge Agent for risk assessment"""
    
    def __init__(self):
        """Initialize ADK Agent"""
        # genai already configured at module import with GEMINI_API_KEY.
        logger.info("ADK Agent initialized (using configured Gemini API key)")

    def compute_risk_score(self, detections: Dict[str, Any]) -> Tuple[float, str]:
        """
        Compute risk score and label based on detections
        
        Args:
            detections: Structured detection from vision model
            
        Returns:
            Tuple of (risk_score: float 0-100, risk_label: str)
        """
        try:
            score = 0.0
            
            # Extract components
            objects = detections.get('detected_objects', [])
            scene = detections.get('scene_analysis', {})
            visibility = detections.get('visibility_issues', [])
            risk_factors = detections.get('risk_factors', [])
            
            # Object-based scoring
            HIGH_RISK_OBJECTS = {'person', 'pedestrian', 'animal', 'motorcycle'}
            MEDIUM_RISK_OBJECTS = {'vehicle', 'bicycle', 'truck'}
            
            for obj in objects:
                label = obj.get('label', '').lower()
                confidence = obj.get('confidence', 0.5)
                
                if any(risk_obj in label for risk_obj in HIGH_RISK_OBJECTS):
                    score += min(50 * confidence, 50)
                elif any(risk_obj in label for risk_obj in MEDIUM_RISK_OBJECTS):
                    score += min(20 * confidence, 20)
            
            # Lighting factors
            lighting = scene.get('lighting', '').lower()
            if 'night' in lighting:
                score += 15
            elif 'dusk' in lighting or 'dawn' in lighting:
                score += 10
            
            # Weather factors
            weather = scene.get('weather', '').lower()
            if 'rain' in weather or 'snow' in weather:
                score += 20
            elif 'fog' in weather:
                score += 15
            
            # Traffic density
            traffic = scene.get('traffic_density', '').lower()
            if 'heavy' in traffic:
                score += 15
            elif 'moderate' in traffic:
                score += 5
            
            # Visibility issues
            if visibility and visibility != ['none']:
                score += len(visibility) * 10
            
            # Specific risk factors
            RISK_FACTOR_WEIGHTS = {
                'pedestrian_detected': 30,
                'oncoming_traffic': 25,
                'construction': 20,
                'speeding_zone': 15,
                'wet_road': 15,
                'low_visibility': 20,
                'vehicle_too_close': 25
            }
            
            for factor in risk_factors:
                score += RISK_FACTOR_WEIGHTS.get(factor, 5)
            
            # Cap score at 100
            score = min(score, 100.0)
            
            # Determine label
            if score >= 70:
                label = "HIGH"
            elif score >= 40:
                label = "MODERATE"
            else:
                label = "LOW"
            
            logger.info(f"Risk computed - Score: {score:.1f}, Label: {label}")
            return score, label
            
        except Exception as e:
            logger.error(f"Risk score computation failed: {str(e)}")
            return 50.0, "MODERATE"

    def run_adk_workflow(self, detections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run full ADK workflow: risk scoring, LLM analysis, guardrails
        
        Args:
            detections: Structured detections from vision model
            
        Returns:
            Complete analysis result
        """
        try:
            # Step 1: Compute risk score
            risk_score, risk_label = self.compute_risk_score(detections)
            
            # Step 2: Generate natural language summary with Gemini
            summary = self._generate_summary(detections, risk_score, risk_label)
            
            # Step 3: Apply guardrails
            summary = self._apply_guardrails(summary)
            
            # Step 4: Prepare final result
            result = {
                'risk_score': round(risk_score, 2),
                'risk_label': risk_label,
                'summary': summary,
                'detections': detections,
                'timestamp': datetime.utcnow().isoformat(),
                'agent_version': '1.0.0'
            }
            
            logger.info(f"ADK workflow completed - Risk: {risk_label}, Score: {risk_score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"ADK workflow failed: {str(e)}")
            return self._get_fallback_result(detections)

    def _generate_summary(self, detections: Dict[str, Any], risk_score: float, risk_label: str) -> str:
        """
        Generate natural language summary using Gemini
        """
        try:
            # Always force API key config (prevents Cloud Run OAuth fallback)
            gemini_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=gemini_key)

            # Build prompt
            objects_text = ", ".join([
                f"{obj.get('label', 'unknown')} (confidence: {obj.get('confidence', 0):.0%})"
                for obj in detections.get('detected_objects', [])
            ]) or "No objects detected"

            scene = detections.get('scene_analysis', {})
            risk_factors = ", ".join(detections.get('risk_factors', ['none'])) or "none"

            prompt = f"""Based on this road scene analysis, generate a concise driving risk summary (2-3 sentences max).

    Detection Summary:
    - Objects: {objects_text}
    - Road Type: {scene.get('road_type', 'unknown')}
    - Lighting: {scene.get('lighting', 'unknown')}
    - Weather: {scene.get('weather', 'unknown')}
    - Traffic: {scene.get('traffic_density', 'unknown')}
    - Risk Factors: {risk_factors}
    - Risk Score: {risk_score:.1f}/100 ({risk_label})

    Generate a natural, actionable summary. Start with "Risk level {risk_label}:"."""

            # Force usage of the API key for summary generation
            gemini_key = os.getenv("GEMINI_API_KEY")
            genai.configure(api_key=gemini_key)

            model = genai.GenerativeModel(Config.GEMINI_MODEL)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 150,
                }
            )

            summary = response.text.strip()
            logger.info(f"Generated summary: {summary[:80]}...")
            return summary

        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return f"Risk level {risk_label}: Unable to generate detailed analysis. Please review road conditions manually."

    def _apply_guardrails(self, summary: str) -> str:
        """
        Apply safety guardrails to summary
        
        Args:
            summary: Generated summary
            
        Returns:
            Sanitized summary
        """
        try:
            # Remove any potentially harmful content
            harmful_patterns = [
                "ignore", "bypass", "disable", "hack", "exploit",
                "private", "secret", "password", "credential"
            ]
            
            sanitized = summary
            for pattern in harmful_patterns:
                sanitized = sanitized.replace(pattern.lower(), "[redacted]")
                sanitized = sanitized.replace(pattern.upper(), "[redacted]")
            
            # Ensure summary doesn't exceed reasonable length
            if len(sanitized) > 500:
                sanitized = sanitized[:497] + "..."
            
            # Verify it's not empty
            if not sanitized or sanitized.strip() == "":
                sanitized = "Risk assessment completed. Please review driving conditions."
            
            logger.debug("Guardrails applied successfully")
            return sanitized
            
        except Exception as e:
            logger.error(f"Guardrail application failed: {str(e)}")
            return "Risk assessment unavailable at this time."

    def _get_fallback_result(self, detections: Dict[str, Any]) -> Dict[str, Any]:
        """Return fallback result when workflow fails"""
        return {
            'risk_score': 50.0,
            'risk_label': 'MODERATE',
            'summary': 'Unable to complete analysis. Please ensure proper lighting and image quality.',
            'detections': detections,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_version': '1.0.0',
            'error': 'Fallback result due to processing error'
        }


# Singleton instance
_agent = None

def get_adk_agent() -> ADKAgent:
    """Get or create ADK Agent singleton"""
    global _agent
    if _agent is None:
        _agent = ADKAgent()
    return _agent


# """
# ADK (Autonomous Driving Knowledge) Agent - Risk assessment and workflow orchestration
# """
# import json
# from typing import Dict, Any, List, Tuple
# from datetime import datetime
# from google import genai   # ✅ NEW Gemini v1 SDK
# from .config import Config
# from .logger import setup_logger
# import os
# import time

# # Initialize Gemini v1 client
# GEMINI_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_KEY:
#     raise ValueError("GEMINI_API_KEY not set")

# client = genai.Client(api_key=GEMINI_KEY)   # ✅ v1 API client

# logger = setup_logger(__name__)

# # ---------- Retry wrapper (prevents 429 failures) ----------
# def safe_generate_content(model, contents, generation_config):
#     for i in range(4):
#         try:
#             return client.models.generate_content(
#                 model=model,
#                 contents=contents,
#                 generation_config=generation_config
#             )
#         except Exception as e:
#             if "429" in str(e) or "rate" in str(e).lower():
#                 wait = min(2 ** i, 10)
#                 logger.warning(f"Rate limit hit on summary. Retrying in {wait}s...")
#                 time.sleep(wait)
#             else:
#                 raise
#     raise RuntimeError("Max retries exceeded for summary generation.")


# class ADKAgent:
#     """Autonomous Driving Knowledge Agent for risk assessment"""

#     def __init__(self):
#         logger.info("ADK Agent initialized using Gemini v1 API")


#     # ------------------------------------------------------------
#     # RISK SCORE COMPUTATION
#     # ------------------------------------------------------------
#     def compute_risk_score(self, detections: Dict[str, Any]) -> Tuple[float, str]:
#         try:
#             score = 0.0

#             objects = detections.get('detected_objects', [])
#             scene = detections.get('scene_analysis', {})
#             visibility = detections.get('visibility_issues', [])
#             risk_factors = detections.get('risk_factors', [])

#             # Object-based scoring
#             HIGH_RISK_OBJECTS = {'person', 'pedestrian', 'animal', 'motorcycle'}
#             MEDIUM_RISK_OBJECTS = {'vehicle', 'bicycle', 'truck'}

#             for obj in objects:
#                 label = obj.get('label', '').lower()
#                 conf = obj.get('confidence', 0.5)

#                 if any(x in label for x in HIGH_RISK_OBJECTS):
#                     score += min(50 * conf, 50)
#                 elif any(x in label for x in MEDIUM_RISK_OBJECTS):
#                     score += min(20 * conf, 20)

#             # Lighting
#             lighting = scene.get('lighting', '').lower()
#             if 'night' in lighting:
#                 score += 15
#             elif 'dusk' in lighting or 'dawn' in lighting:
#                 score += 10

#             # Weather
#             weather = scene.get('weather', '').lower()
#             if 'rain' in weather or 'snow' in weather:
#                 score += 20
#             elif 'fog' in weather:
#                 score += 15

#             # Traffic
#             traffic = scene.get('traffic_density', '').lower()
#             if 'heavy' in traffic:
#                 score += 15
#             elif 'moderate' in traffic:
#                 score += 5

#             # Visibility issues
#             if visibility and visibility != ['none']:
#                 score += len(visibility) * 10

#             # Risk factors
#             RISK_WEIGHTS = {
#                 'pedestrian_detected': 30,
#                 'oncoming_traffic': 25,
#                 'construction': 20,
#                 'speeding_zone': 15,
#                 'wet_road': 15,
#                 'low_visibility': 20,
#                 'vehicle_too_close': 25,
#             }

#             for f in risk_factors:
#                 score += RISK_WEIGHTS.get(f, 5)

#             score = min(score, 100.0)

#             if score >= 70:
#                 label = "HIGH"
#             elif score >= 40:
#                 label = "MODERATE"
#             else:
#                 label = "LOW"

#             logger.info(f"Risk computed - Score: {score:.1f}, Label: {label}")
#             return score, label

#         except Exception as e:
#             logger.error(f"Risk score computation failed: {str(e)}")
#             return 50.0, "MODERATE"


#     # ------------------------------------------------------------
#     # FULL WORKFLOW
#     # ------------------------------------------------------------
#     def run_adk_workflow(self, detections: Dict[str, Any]) -> Dict[str, Any]:
#         try:
#             risk_score, risk_label = self.compute_risk_score(detections)

#             summary = self._generate_summary(detections, risk_score, risk_label)
#             summary = self._apply_guardrails(summary)

#             result = {
#                 "risk_score": round(risk_score, 2),
#                 "risk_label": risk_label,
#                 "summary": summary,
#                 "detections": detections,
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "agent_version": "1.0.0",
#             }

#             logger.info(
#                 f"ADK workflow completed - Risk: {risk_label}, Score: {risk_score:.1f}"
#             )
#             return result

#         except Exception as e:
#             logger.error(f"ADK workflow failed: {str(e)}")
#             return self._get_fallback_result(detections)


#     # ------------------------------------------------------------
#     # SUMMARY GENERATION (USING GEMINI v1)
#     # ------------------------------------------------------------
#     def _generate_summary(self, detections, risk_score, risk_label):
#         try:
#             # Build text prompt
#             objs = ", ".join(
#                 f"{o.get('label', 'unknown')} ({o.get('confidence', 0):.0%})"
#                 for o in detections.get("detected_objects", [])
#             ) or "No objects detected"

#             scene = detections.get("scene_analysis", {})
#             risk_factors = ", ".join(detections.get("risk_factors", [])) or "none"

#             prompt = f"""
# Generate a concise 2–3 sentence driving safety summary.

# Scene Details:
# - Objects: {objs}
# - Road Type: {scene.get('road_type', 'unknown')}
# - Lighting: {scene.get('lighting', 'unknown')}
# - Weather: {scene.get('weather', 'unknown')}
# - Traffic: {scene.get('traffic_density', 'unknown')}
# - Risk Factors: {risk_factors}
# - Risk Score: {risk_score:.1f}/100

# Start the output with: "Risk level {risk_label}:"
# """

#             # Use a text-only model (recommended)
#             text_model = Config.GEMINI_TEXT_MODEL  # e.g., "gemini-2.0-flash"

#             response = safe_generate_content(
#                 model=text_model,
#                 contents=[prompt],
#                 generation_config={
#                     "temperature": 0.7,
#                     "max_output_tokens": 150,
#                 }
#             )

#             summary = response.text.strip()
#             logger.info(f"Generated summary: {summary[:80]}...")
#             return summary

#         except Exception as e:
#             logger.error(f"Summary generation failed: {str(e)}")
#             return f"Risk level {risk_label}: Summary unavailable."


#     # ------------------------------------------------------------
#     # GUARDRAILS
#     # ------------------------------------------------------------
#     def _apply_guardrails(self, summary: str) -> str:
#         try:
#             harmful = ["ignore", "bypass", "disable", "hack", "exploit",
#                        "private", "secret", "password", "credential"]

#             sanitized = summary
#             for w in harmful:
#                 sanitized = sanitized.replace(w, "[redacted]")

#             if len(sanitized) > 500:
#                 sanitized = sanitized[:497] + "..."

#             if not sanitized.strip():
#                 sanitized = "Risk assessment completed."

#             return sanitized

#         except Exception:
#             return "Risk assessment completed."


#     # ------------------------------------------------------------
#     # FALLBACK
#     # ------------------------------------------------------------
#     def _get_fallback_result(self, detections: Dict[str, Any]) -> Dict[str, Any]:
#         return {
#             "risk_score": 50.0,
#             "risk_label": "MODERATE",
#             "summary": "Unable to complete analysis.",
#             "detections": detections,
#             "timestamp": datetime.utcnow().isoformat(),
#             "agent_version": "1.0.0",
#             "error": "Fallback result due to processing error",
#         }


# # ---------- Singleton ----------
# _agent = None

# def get_adk_agent() -> ADKAgent:
#     global _agent
#     if _agent is None:
#         _agent = ADKAgent()
#     return _agent
