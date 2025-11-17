"""
MCP Toolbox: Google Cloud Storage and Firestore helpers
"""
import io
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from google.cloud import storage, firestore
from google.api_core.exceptions import GoogleAPICallError
from .config import Config
from .logger import setup_logger

logger = setup_logger(__name__)

class MCPToolbox:
    """Multi-Cloud Platform toolbox for GCS and Firestore operations"""
    
    def __init__(self):
        """Initialize GCS and Firestore clients"""
        try:
            self.storage_client = storage.Client(project=Config.PROJECT_ID)
            self.firestore_client = firestore.Client(project=Config.PROJECT_ID)
            self.bucket = self.storage_client.bucket(Config.GCS_BUCKET)
            logger.info(f"MCP Toolbox initialized - Project: {Config.PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Toolbox: {str(e)}")
            raise

    def upload_image_to_gcs(self, image_data: bytes, image_id: str) -> str:
        """
        Upload image to Google Cloud Storage
        
        Args:
            image_data: Raw image bytes
            image_id: Unique image identifier
            
        Returns:
            GCS URI (gs://bucket/path)
            
        Raises:
            GoogleAPICallError: If upload fails
        """
        try:
            blob_name = f"images/{image_id}.jpg"
            blob = self.bucket.blob(blob_name)
            
            # Upload with content type
            blob.upload_from_string(
                image_data,
                content_type="image/jpeg",
                timeout=30
            )
            
            gcs_uri = f"gs://{Config.GCS_BUCKET}/{blob_name}"
            logger.info(f"Image uploaded successfully: {gcs_uri}")
            return gcs_uri
            
        except GoogleAPICallError as e:
            logger.error(f"GCS upload failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {str(e)}")
            raise

    def insert_analysis(self, analysis_result: Dict[str, Any]) -> str:
        """
        Store analysis result in Firestore
        
        Args:
            analysis_result: Complete analysis result dictionary
            
        Returns:
            Document ID
            
        Raises:
            GoogleAPICallError: If Firestore write fails
        """
        try:
            doc_id = str(uuid.uuid4())
            
            # Add metadata
            analysis_result['created_at'] = datetime.utcnow()
            analysis_result['doc_id'] = doc_id
            
            # Write to Firestore
            self.firestore_client.collection(Config.FIRESTORE_COLLECTION).document(doc_id).set(
                analysis_result,
                merge=True
            )
            
            logger.info(f"Analysis stored in Firestore: {doc_id}")
            return doc_id
            
        except GoogleAPICallError as e:
            logger.error(f"Firestore write failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Firestore write: {str(e)}")
            raise

    def get_analysis_history(self, limit: int = 10) -> list:
        """
        Retrieve recent analyses from Firestore
        
        Args:
            limit: Number of records to retrieve
            
        Returns:
            List of analysis documents
        """
        try:
            docs = (
                self.firestore_client.collection(Config.FIRESTORE_COLLECTION)
                .order_by('created_at', direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            
            results = []
            for doc in docs:
                results.append(doc.to_dict())
            
            logger.info(f"Retrieved {len(results)} analyses from history")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis history: {str(e)}")
            return []

    def get_analysis_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific analysis by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Analysis document or None if not found
        """
        try:
            doc = self.firestore_client.collection(Config.FIRESTORE_COLLECTION).document(doc_id).get()
            
            if doc.exists:
                logger.info(f"Retrieved analysis: {doc_id}")
                return doc.to_dict()
            else:
                logger.warning(f"Analysis not found: {doc_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve analysis {doc_id}: {str(e)}")
            return None

    def aggregate_risk_stats(self) -> Dict[str, Any]:
        """
        Aggregate risk statistics from all analyses
        
        Returns:
            Risk statistics dictionary
        """
        try:
            docs = self.firestore_client.collection(Config.FIRESTORE_COLLECTION).stream()
            
            stats = {
                'total_analyses': 0,
                'high_risk_count': 0,
                'moderate_risk_count': 0,
                'low_risk_count': 0,
                'average_risk_score': 0.0,
                'common_risks': {}
            }
            
            total_score = 0
            
            for doc in docs:
                data = doc.to_dict()
                stats['total_analyses'] += 1
                
                # Count by risk label
                risk_label = data.get('risk_label', 'unknown')
                if risk_label == 'HIGH':
                    stats['high_risk_count'] += 1
                elif risk_label == 'MODERATE':
                    stats['moderate_risk_count'] += 1
                else:
                    stats['low_risk_count'] += 1
                
                # Accumulate scores
                total_score += data.get('risk_score', 0)
                
                # Track common risks
                for obj in data.get('detected_objects', []):
                    obj_label = obj.get('label', 'unknown')
                    stats['common_risks'][obj_label] = stats['common_risks'].get(obj_label, 0) + 1
            
            if stats['total_analyses'] > 0:
                stats['average_risk_score'] = total_score / stats['total_analyses']
            
            logger.info("Risk statistics aggregated successfully")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to aggregate risk statistics: {str(e)}")
            return {}


# Singleton instance
_toolbox = None

def get_toolbox() -> MCPToolbox:
    """Get or create toolbox singleton"""
    global _toolbox
    if _toolbox is None:
        _toolbox = MCPToolbox()
    return _toolbox
