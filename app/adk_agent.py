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
