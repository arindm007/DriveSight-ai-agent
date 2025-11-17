"""
Configuration management for DriveSight application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from app directory or parent
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    """Application configuration"""
    GEMINI_VISION_MODEL = "gemini-2.5-flash"
    GEMINI_TEXT_MODEL = "gemini-2.5-flash"


    
    # GCP Settings
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "").strip()
    GCS_BUCKET = os.getenv("GCS_BUCKET", "drivesight-images").strip()
    
    # Firestore Settings
    FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", "analyses")
    
    # Model Settings
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp") #original working


    # GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-preview")
    # GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-preview-image-generation")
    # GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 20 * 1024 * 1024))
    ALLOWED_FORMATS = set(os.getenv("ALLOWED_FORMATS", "image/jpeg,image/png,image/webp,image/gif").split(","))
    
    # API Settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 60))
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def validate():
        """Validate critical configuration"""
        if not Config.PROJECT_ID:
            raise ValueError(
                "GCP_PROJECT_ID not configured. "
                "Please set GCP_PROJECT_ID in .env file or environment variables."
            )
        if not Config.GCS_BUCKET:
            raise ValueError(
                "GCS_BUCKET not configured. "
                "Please set GCS_BUCKET in .env file or environment variables."
            )
