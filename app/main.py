"""
DriveSight - Road Risk Analysis Agent
FastAPI backend with Gemini Vision and Firestore integration
"""
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from .config import Config
from .logger import setup_logger
from .model import get_vision_model
from .adk_agent import get_adk_agent
from .mcp_toolbox import get_toolbox
from .cache_manager import get_cache

# Initialize app
app = FastAPI(
    title="DriveSight",
    description="AI-powered road risk assessment agent",
    version="1.0.0"
)

# Setup logging
logger = setup_logger(__name__)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Validate configuration on startup
@app.on_event("startup")
async def startup_event():
    """Startup validation"""
    try:
        Config.validate()
        logger.info("DriveSight API started successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DriveSight",
        "version": "1.0.0"
    }


@app.post("/analyze", tags=["Analysis"])
async def analyze_image(
    image: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze dashcam/road image for driving hazards
    
    Args:
        image: Image file (JPEG, PNG, WebP, GIF)
    
    Returns:
        Analysis result with risk score and summary
    """
    start_time = time.time()
    image_id = str(uuid.uuid4())
    
    try:
        # Validate file
        if not image.content_type in Config.ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format. Allowed: {', '.join(Config.ALLOWED_FORMATS)}"
            )
        
        # Read image data
        image_data = await image.read()
        
        # Validate size
        if len(image_data) > Config.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large. Max size: {Config.MAX_IMAGE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        logger.info(f"Processing image: {image_id}, size: {len(image_data) / 1024:.1f}KB")
        
        # Check cache first
        cache = get_cache()
        cached_result = cache.get_by_image_hash(image_data)
        if cached_result:
            logger.info(f"Cache hit for image {image_id}")
            cached_result['cached'] = True
            cached_result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
            return cached_result
        
        # Step 1: Vision analysis
        logger.info(f"Starting vision analysis for {image_id}")
        vision_model = get_vision_model()
        detections = vision_model.analyze_image_local(image_data)
        
        # Step 2: ADK workflow (risk scoring + summary generation)
        logger.info(f"Running ADK workflow for {image_id}")
        adk_agent = get_adk_agent()
        analysis_result = adk_agent.run_adk_workflow(detections)
        
        # Add metadata
        analysis_result['image_id'] = image_id
        analysis_result['filename'] = image.filename
        analysis_result['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Step 3: Store in Firestore (background)
        toolbox = get_toolbox()
        background_tasks.add_task(
            _store_analysis,
            analysis_result,
            image_data,
            image_id
        )
        
        # Cache the result
        cache.set_by_image_hash(image_data, analysis_result)
        
        logger.info(f"Analysis completed for {image_id} in {analysis_result['processing_time_ms']:.0f}ms")
        
        return JSONResponse(
            status_code=200,
            content=analysis_result
        )
        
    except HTTPException as e:
        logger.warning(f"Analysis validation failed for {image_id}: {str(e.detail)}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed for {image_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/analysis/{doc_id}", tags=["Analysis"])
async def get_analysis(doc_id: str):
    """
    Retrieve specific analysis from Firestore
    
    Args:
        doc_id: Document ID from previous analysis
    
    Returns:
        Stored analysis result
    """
    try:
        toolbox = get_toolbox()
        result = toolbox.get_analysis_by_id(doc_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve analysis {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")


@app.get("/history", tags=["Analysis"])
async def get_analysis_history(limit: int = 10):
    """
    Get recent analyses
    
    Args:
        limit: Number of records to retrieve (max 100)
    
    Returns:
        List of recent analyses
    """
    try:
        if limit > 100:
            limit = 100
        
        toolbox = get_toolbox()
        history = toolbox.get_analysis_history(limit=limit)
        
        return {
            "count": len(history),
            "analyses": history
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@app.get("/stats", tags=["Analytics"])
async def get_risk_statistics():
    """
    Get aggregate risk statistics across all analyses
    
    Returns:
        Risk statistics and insights
    """
    try:
        toolbox = get_toolbox()
        stats = toolbox.aggregate_risk_stats()
        
        return {
            "statistics": stats,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to compute statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to compute statistics")


async def _store_analysis(
    analysis_result: dict,
    image_data: bytes,
    image_id: str
):
    """
    Background task: Store analysis in Firestore and upload image to GCS
    
    Args:
        analysis_result: Complete analysis result
        image_data: Raw image bytes
        image_id: Image identifier
    """
    try:
        toolbox = get_toolbox()
        
        # Upload image to GCS
        gcs_uri = toolbox.upload_image_to_gcs(image_data, image_id)
        analysis_result['gcs_uri'] = gcs_uri
        
        # Store in Firestore
        doc_id = toolbox.insert_analysis(analysis_result)
        logger.info(f"Background storage completed for {image_id} -> {doc_id}")
        
    except Exception as e:
        logger.error(f"Background storage failed for {image_id}: {str(e)}")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API documentation"""
    return {
        "service": "DriveSight",
        "version": "1.0.0",
        "description": "AI-powered road risk assessment agent",
        "endpoints": {
            "health": "/health",
            "analyze": "POST /analyze",
            "history": "GET /history?limit=10",
            "stats": "GET /stats",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
