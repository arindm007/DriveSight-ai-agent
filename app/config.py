"""
Configuration management for DriveSight application
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # GCP Settings
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
    GCS_BUCKET = os.getenv("GCS_BUCKET", "drivesight-images")
    
    # Firestore Settings
    FIRESTORE_COLLECTION = "analyses"
    
    # Model Settings
    GEMINI_MODEL = "gemini-2.0-flash-exp"
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    
    # API Settings
    REQUEST_TIMEOUT = 60
    CACHE_TTL = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def validate():
        """Validate critical configuration"""
        if not Config.PROJECT_ID or Config.PROJECT_ID == "your-project-id":
            raise ValueError("GCP_PROJECT_ID not configured")
