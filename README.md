# DriveSight - AI-Powered Road Risk Assessment Agent

![DriveSight](https://img.shields.io/badge/DriveSight-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview

**DriveSight** is an AI-powered road risk assessment agent that analyzes dashcam/road images to identify driving hazards and compute risk scores. It uses **Gemini Vision** for multimodal image analysis and the **ADK (Autonomous Driving Knowledge) Agent** for intelligent risk assessment and natural language summaries.

### Key Features

✅ **Gemini Vision API Integration** - Advanced multimodal image understanding  
✅ **Real-time Risk Scoring** - Instant hazard detection and risk quantification  
✅ **Firestore Backend** - Persistent storage and historical analytics  
✅ **Cloud Run Deployment** - Serverless, scalable infrastructure  
✅ **Mobile-Friendly UI** - Responsive design for all devices  
✅ **Intelligent Caching** - Hash-based result caching for duplicate images  
✅ **Production-Grade Error Handling** - Graceful fallbacks and guardrails  
✅ **Comprehensive Logging** - Structured logging for debugging and monitoring  

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (HTML/JS)                      │
│              Mobile-Friendly Web Interface                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌─────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                           │
│                  (Cloud Run Service)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ main.py - API Endpoints & Request Orchestration     │   │
│  │ • POST /analyze - Image analysis entry point        │   │
│  │ • GET /history - Analysis history retrieval         │   │
│  │ • GET /stats - Risk aggregation & insights          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Gemini Vision (model.py)                             │   │
│  │ • Image preprocessing & validation                  │   │
│  │ • Multimodal object detection & scene analysis      │   │
│  │ • Structured JSON response parsing                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ADK Agent (adk_agent.py)                             │   │
│  │ • Risk score computation (0-100)                    │   │
│  │ • Gemini text-based summary generation              │   │
│  │ • Output guardrails & validation                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MCP Toolbox (mcp_toolbox.py)                         │   │
│  │ • GCS image upload                                  │   │
│  │ • Firestore document storage                        │   │
│  │ • Historical data retrieval & aggregation           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Cache Manager (cache_manager.py)                     │   │
│  │ • Image hash-based caching (TTL: 1 hour)            │   │
│  │ • Fast duplicate detection                          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────┬──────────────────┬────────────────────────┬────────────┘
      │                  │                        │
      ▼                  ▼                        ▼
┌──────────────┐  ┌──────────────┐    ┌──────────────────┐
│ Gemini API   │  │  GCS Storage │    │  Firestore       │
│ (Text & Vision)  │  (Images)    │    │  (Analytics)     │
└──────────────┘  └──────────────┘    └──────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- GCP Account with billing enabled
- `gcloud` CLI installed and configured
- Docker (for containerization)

### 1. Clone & Setup

```bash
# Navigate to project
cd drivesight

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt
```

### 2. Configure GCP Resources

```bash
# Run setup script (replace with your GCP Project ID)
bash setup.sh YOUR_GCP_PROJECT_ID

# This will:
# ✓ Enable required APIs (Cloud Run, Firestore, GCS, AI Platform)
# ✓ Create Cloud Storage bucket
# ✓ Initialize Firestore database
# ✓ Create service account with proper IAM roles
# ✓ Generate service account key (key.json)
# ✓ Create .env file with configuration
```

### 3. Set Environment Variables

```bash
# Activate service account credentials (already done by setup.sh)
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"

# Verify project configuration
cat .env
```

### 4. Run Locally

```bash
# Start development server
python -m uvicorn app.main:app --reload --port 8080

# Open browser
# http://localhost:8080/frontend/index.html
```

### 5. Deploy to Cloud Run

```bash
# Option A: Using gcloud (recommended for testing)
gcloud run deploy drivesight \
    --source . \
    --region europe-west1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300

# Option B: Using Docker (manual build)
docker build -t gcr.io/YOUR_PROJECT_ID/drivesight:latest .
docker push gcr.io/YOUR_PROJECT_ID/drivesight:latest
gcloud run deploy drivesight \
    --image gcr.io/YOUR_PROJECT_ID/drivesight:latest \
    --region europe-west1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2
```

### 6. Access Deployed Service

Once deployed, you'll receive a URL like:
```
https://drivesight-xxxxx-uc.a.run.app
```

Access the frontend:
```
https://drivesight-xxxxx-uc.a.run.app/frontend/index.html
```

---

## API Documentation

### Endpoints

#### 1. Analyze Image
```http
POST /analyze
Content-Type: multipart/form-data

Request:
- image: [binary] Image file (JPEG, PNG, WebP, GIF, max 20MB)

Response:
{
  "risk_score": 65.5,
  "risk_label": "MODERATE",
  "summary": "Risk level MODERATE: Pedestrian detected at 4 o'clock position, moderate traffic density in urban setting with daylight conditions.",
  "detections": {
    "detected_objects": [...],
    "scene_analysis": {...},
    "visibility_issues": [...],
    "risk_factors": [...]
  },
  "image_id": "uuid-string",
  "processing_time_ms": 1234,
  "cached": false
}
```

#### 2. Get Analysis History
```http
GET /history?limit=10

Response:
{
  "count": 5,
  "analyses": [
    { "image_id": "...", "risk_score": 45.0, "created_at": "2025-01-15T10:30:00", ... }
  ]
}
```

#### 3. Get Risk Statistics
```http
GET /stats

Response:
{
  "statistics": {
    "total_analyses": 42,
    "high_risk_count": 8,
    "moderate_risk_count": 18,
    "low_risk_count": 16,
    "average_risk_score": 52.3,
    "common_risks": {
      "pedestrian": 12,
      "vehicle": 35,
      "bicycle": 3
    }
  },
  "timestamp": 1705316400
}
```

#### 4. Get Specific Analysis
```http
GET /analysis/{doc_id}

Response:
{ Full analysis document from Firestore }
```

#### 5. Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "service": "DriveSight",
  "version": "1.0.0"
}
```

---

## Configuration

### Environment Variables (.env)

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket-name
FIRESTORE_COLLECTION=analyses

# Model Configuration
GEMINI_MODEL=gemini-2.0-flash-exp
MAX_IMAGE_SIZE=20971520  # 20MB in bytes
ALLOWED_FORMATS=image/jpeg,image/png,image/webp,image/gif

# API Configuration
REQUEST_TIMEOUT=60
CACHE_TTL=3600  # 1 hour

# Logging
LOG_LEVEL=INFO
```

---

## Project Structure

```
drivesight/
├── app/
│   ├── main.py              # FastAPI application & endpoints
│   ├── model.py             # Gemini Vision integration
│   ├── adk_agent.py         # Risk scoring & workflow orchestration
│   ├── mcp_toolbox.py       # Firestore & GCS helpers
│   ├── cache_manager.py     # In-memory caching with TTL
│   ├── config.py            # Configuration management
│   ├── logger.py            # Structured logging setup
│   └── requirements.txt      # Python dependencies
├── frontend/
│   └── index.html           # Mobile-friendly React-like UI
├── Dockerfile               # Container configuration
├── cloudbuild.yaml          # Cloud Build CI/CD pipeline
├── setup.sh                 # GCP resource initialization
├── README.md                # This file
└── .env                     # Environment variables (generated)
```

---

## Features Deep Dive

### 1. Gemini Vision Integration

The `model.py` module leverages **Gemini 2.0 Flash** for multimodal image analysis:

- **Object Detection**: Identifies vehicles, pedestrians, cyclists, animals
- **Scene Understanding**: Recognizes road type, lighting, weather, traffic density
- **Hazard Identification**: Detects specific risk factors (construction, oncoming traffic, etc.)
- **Structured Output**: Returns JSON-formatted detections for downstream processing

**Prompt Engineering Strategy:**
```
- Temperature: 0.3 (low creativity, high consistency)
- Max tokens: 1024 (concise responses)
- Strict JSON format enforcement
- Fallback detection on parse errors
```

### 2. ADK Agent Workflow

The `adk_agent.py` implements intelligent risk assessment:

**Step 1: Risk Score Computation**
- Object-based scoring (high-risk: pedestrians, animals; medium: vehicles)
- Lighting factors (night: +15, dusk: +10)
- Weather factors (rain/snow: +20, fog: +15)
- Traffic density modifiers (+15 for heavy, +5 for moderate)
- Visibility issues and specific risk factors

**Step 2: Natural Language Generation**
- Gemini text model generates contextual, actionable summaries
- Temperature 0.7 for balanced creativity and consistency
- 150 token limit for concise output

**Step 3: Guardrails**
- Content sanitization (removes harmful patterns)
- Length validation (max 500 chars)
- Empty response fallback

### 3. Intelligent Caching

`cache_manager.py` provides hash-based caching:

- **Image Hash**: SHA-256 of image bytes
- **TTL**: 1 hour (configurable)
- **Benefits**: 
  - Duplicate image detection (99.99% collision resistance)
  - Reduced API calls and latency (~50ms vs 1500ms)
  - Cost savings on Gemini API usage

### 4. Firestore Integration

`mcp_toolbox.py` manages data persistence:

- **Collections**: `analyses` - all analysis results
- **Fields**: 
  - `image_id`, `gcs_uri`, `filename`
  - `risk_score`, `risk_label`, `summary`
  - `detections`, `created_at`, `doc_id`
- **Queries**: 
  - Historical retrieval (ordered by timestamp)
  - Aggregation (risk statistics, common hazards)

### 5. Production Error Handling

- **Graceful Fallbacks**: Returns valid responses even on partial failures
- **Comprehensive Logging**: All operations logged with context
- **Input Validation**: File size, format, and content checks
- **Timeout Protection**: 60-second request timeout
- **Circuit Breaker Pattern**: Ready for integration with external services

---

## Performance Optimization

| Metric | Value | Notes |
|--------|-------|-------|
| **Cache Hit Time** | ~50ms | SHA-256 lookup |
| **Vision Analysis** | ~1.2s | Gemini Vision API |
| **Risk Scoring** | ~200ms | Local computation |
| **Summary Generation** | ~300ms | Gemini text API |
| **Firestore Write** | ~500ms | Background task |
| **Total P95 Latency** | ~2.5s | First request, no cache |
| **Cached Response** | ~100ms | Hash-based lookup |

---

## Monitoring & Logging

All operations are logged with structured format:

```
2025-01-15 10:30:45 - app.main - INFO - Analysis completed for abc123 in 1234ms
2025-01-15 10:30:45 - app.model - INFO - Gemini Vision analysis completed
2025-01-15 10:30:46 - app.adk_agent - INFO - ADK workflow completed - Risk: MODERATE, Score: 65.5
2025-01-15 10:30:46 - app.mcp_toolbox - INFO - Analysis stored in Firestore: doc-uuid
```

**View Cloud Run logs:**
```bash
gcloud run logs read drivesight --region europe-west1 --limit 50
```

---

## Demo Walkthrough

### 1. Upload Image
- Open frontend: `https://drivesight-xxxxx.run.app/frontend/index.html`
- Drag/drop or click to upload dashcam image
- See image preview with filename

### 2. Analyze
- Click "Analyze Image" button
- Watch spinner during processing (~1-2s)
- Results appear with:
  - Risk score (0-100)
  - Risk label (HIGH/MODERATE/LOW)
  - AI-generated summary
  - Detected objects
  - Scene analysis

### 3. Explore History
- Scroll down to see recent analyses
- View aggregate risk statistics
- Processing time displayed

### 4. Firestore Dashboard
```bash
# View all analyses
gcloud firestore databases describe

# Query recent results (from Cloud Console)
```

### 5. Cloud Run Monitoring
```bash
# View deployment
gcloud run services describe drivesight --region europe-west1

# Monitor metrics
gcloud run metrics describe drivesight --region europe-west1

# View logs
gcloud run logs read drivesight --region europe-west1 --tail
```

---

## Blog Post Structure (For Event Submission)

### Title
"Building a Serverless Road Risk Assessment Agent with Google Cloud"

### Sections
1. **Introduction** - Problem statement (road safety, insurance)
2. **Architecture Overview** - Cloud Run, Firestore, Gemini Vision
3. **Gemini Vision Integration** - Multimodal analysis capability
4. **ADK Agent Design** - Risk scoring heuristics
5. **Prompt Engineering Techniques** - JSON constraints, guardrails
6. **Production Considerations** - Caching, error handling, logging
7. **Results & Metrics** - Performance, cost, impact
8. **Future Enhancements** - Real-time streaming, dashboard
9. **Code Snippets** - Key implementations
10. **Conclusion** - Summary & call-to-action

---

## Troubleshooting

### Issue: "GCP_PROJECT_ID not configured"
```bash
# Solution: Update .env file or run setup.sh
source .env
echo $GCP_PROJECT_ID
```

### Issue: Firestore permission denied
```bash
# Solution: Check service account IAM roles
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:drivesight-sa*"
```

### Issue: Image upload fails (413 Payload Too Large)
```bash
# Solution: Max size is 20MB; compress image
# Recommended: 5-10MB JPEG images
```

### Issue: Gemini API errors
```bash
# Solution: Verify API is enabled and quota available
gcloud services list --enabled | grep aiplatform
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

### Issue: Cache not working
```bash
# Cache is in-memory; restarts will clear it (expected behavior)
# For persistent cache, integrate Redis: see Phase J extras
```

---

## Future Enhancements (Phase J)

- [ ] **Real-Time Streaming**: WebSocket support for continuous video analysis
- [ ] **Dashboard**: React dashboard with analytics and historical trends
- [ ] **Image Annotation**: Return images with bounding boxes overlaid
- [ ] **Pub/Sub Integration**: Asynchronous processing for large batches
- [ ] **Redis Caching**: Persistent, distributed cache
- [ ] **Advanced Analytics**: Machine learning for pattern detection
- [ ] **Mobile App**: Native iOS/Android application
- [ ] **API Authentication**: OAuth2 / API keys for production

---

## License

MIT - Free to use and modify for personal/commercial projects

---

## Contact & Support

For issues, questions, or contributions:
- **GitHub Issues**: [Create an issue]
- **Email**: support@drivesight.dev
- **Documentation**: [Full API docs](http://localhost:8080/docs)

---

## Acknowledgments

- **Google Cloud** for Cloud Run, Firestore, and Gemini APIs
- **FastAPI** for elegant API framework
- **Gaia Hack** event organizers

---

**🚗 Drive Safer. Analyze Smarter. DriveSight.**
# DriveSight-ai-agent
