# DriveSight - GenArch Architecture Diagram Prompt

Use this prompt with **GenArch: GCP Architecture Diagram Generator** to generate a professional GCP architecture diagram.

---

## 🎯 Optimized GenArch Prompt

Copy and paste this entire prompt into GenArch:

```
Generate a comprehensive GCP Architecture Diagram for DriveSight - an AI-powered road risk assessment agent.

PROJECT OVERVIEW:
- Name: DriveSight
- Purpose: Real-time road/dashcam image analysis for driving hazard detection and risk assessment
- Deployment Model: Serverless (Cloud Run)
- Primary Users: Fleet managers, insurance companies, drivers

ARCHITECTURE COMPONENTS:

1. CLIENT LAYER:
   - Mobile Web Frontend: React-like HTML/CSS/JS interface
     - Features: Image upload (drag/drop), real-time analysis, risk visualization
     - Deployment: Served from Cloud Run or Firebase Hosting
     - Protocol: HTTPS/REST

2. API GATEWAY & LOAD BALANCING:
   - Cloud Run Service: DriveSight API
     - Language: Python 3.11
     - Framework: FastAPI with Uvicorn
     - Endpoints: /analyze, /history, /stats, /health, /docs
     - Configuration: 4Gi memory, 2 vCPU, 300s timeout, auto-scaling 0-10 instances
     - Region: us-central1
     - Allow unauthenticated access (prototype phase)

3. APPLICATION LAYER (Cloud Run):
   
   a) REQUEST HANDLER (main.py):
      - HTTP request processing
      - Input validation (file size, format, MIME type)
      - Multipart form-data handling
      - Response formatting
      - Error handling with proper HTTP status codes
   
   b) VISION ANALYSIS MODULE (model.py):
      - Gemini Vision 2.0 API integration
      - Multimodal image understanding
      - Object detection (person, vehicle, bicycle, animal, motorcycle)
      - Scene analysis (road type, lighting, weather, traffic density)
      - JSON response parsing
      - Graceful fallback on API failures
      - Max input: 20MB image files
   
   c) RISK ASSESSMENT AGENT (adk_agent.py):
      - Risk score computation algorithm (0-100 scale)
      - Multi-factor analysis engine:
        * Object-based scoring (HIGH/MEDIUM risk objects)
        * Lighting conditions modifier (night: +15, dusk: +10)
        * Weather factors (rain/snow: +20, fog: +15)
        * Traffic density modifiers
        * Visibility issue detection
        * Specific risk factor identification
      - Risk label classification (HIGH/MODERATE/LOW)
      - Natural language summary generation (Gemini text API)
      - Safety guardrails on LLM output
   
   d) CACHING LAYER (cache_manager.py):
      - Image hash computation (SHA-256)
      - Result caching with TTL (1 hour default)
      - In-memory cache storage
      - Duplicate detection for same images
      - Performance optimization (50ms cached responses)

4. DATA PERSISTENCE LAYER:
   
   a) FIRESTORE DATABASE:
      - Type: NoSQL document database (Native mode)
      - Region: us-central1
      - Collection: analyses
      - Document fields: image_id, gcs_uri, filename, risk_score, risk_label, summary, detections, scene_analysis, visibility_issues, risk_factors, created_at, doc_id
      - Queries: Historical retrieval, aggregation queries
      - Auto-indexing enabled
      - Real-time sync capability
   
   b) CLOUD STORAGE (GCS):
      - Bucket name: {project-id}-drivesight-images
      - Region: us-central1
      - Path structure: images/{image_id}.jpg
      - Content type: image/jpeg
      - Lifecycle policies: Archive after 90 days (optional)
      - Versioning: Disabled
      - Access: Service account (drivesight-sa)

5. AI/ML SERVICES:
   
   a) GEMINI VISION 2.0 API:
      - Purpose: Multimodal image analysis
      - Model: gemini-2.0-flash-exp
      - Input: Image data (JPEG, PNG, WebP, GIF)
      - Output: Structured JSON with objects, scene info, visibility, risk factors
      - Temperature: 0.3 (low creativity, high consistency)
      - Max tokens: 1024
   
   b) GEMINI TEXT API:
      - Purpose: Natural language summary generation
      - Model: gemini-2.0-flash-exp
      - Input: Structured detection data + risk context
      - Output: Natural language risk assessment summary
      - Temperature: 0.7 (balanced)
      - Max tokens: 150

6. SERVICE ACCOUNTS & SECURITY:
   - Service Account: drivesight-sa@{project-id}.iam.gserviceaccount.com
   - IAM Roles:
     * roles/storage.objectAdmin (GCS bucket access)
     * roles/firestore.admin (Firestore read/write)
     * roles/aiplatform.user (Gemini API access)
   - Authentication: Service account key (key.json) for local dev, Workload Identity for production

7. MONITORING & LOGGING:
   - Cloud Logging: Structured logs from all components
   - Log levels: DEBUG, INFO, WARNING, ERROR
   - Log aggregation: Cloud Console
   - Metrics: Request latency, error rate, API usage
   - Alerts: Budget alerts for Gemini API usage

8. CI/CD PIPELINE:
   - Source Control: Cloud Build triggers on code push
   - Build: Docker image build
   - Registry: Artifact Registry (gcr.io)
   - Deployment: Cloud Run automated deploy
   - Pipeline file: cloudbuild.yaml

9. CONTAINER IMAGE:
   - Base: python:3.11-slim
   - Dependencies: FastAPI, uvicorn, google-cloud libraries, Pillow, cachetools
   - Non-root user: appuser (UID 1000)
   - Health check: /health endpoint
   - Startup: uvicorn main:app --host 0.0.0.0 --port 8080

DATA FLOW:

1. USER UPLOADS IMAGE:
   Frontend → HTTPS → Cloud Run /analyze endpoint

2. IMAGE PROCESSING:
   Request Handler → Cache Manager (check for duplicate via hash)
   
3a. CACHE HIT PATH (50ms):
   Cache Manager → Return cached result → Response to frontend
   
3b. CACHE MISS PATH (2-2.5s):
   Request Handler → Vision Module (Gemini Vision API) → Object detection & scene analysis
   → ADK Agent (Risk computation) → Gemini Text API (Summary generation) → Cache Manager (store result)
   → Response to frontend

4. BACKGROUND STORAGE:
   Background Task → GCS Upload (image) → Firestore Insert (analysis result)

5. DATA RETRIEVAL:
   Frontend /history → Cloud Run → Firestore Query → Return recent analyses

6. ANALYTICS:
   Frontend /stats → Cloud Run → Firestore Aggregation → Risk statistics

PERFORMANCE CHARACTERISTICS:
- Cache hit latency: ~50ms
- First analysis latency: 1.5-2s (Gemini API dependent)
- Cloud Run cold start: 10-12s
- Concurrent capacity: 100+ users per instance
- Auto-scaling: 0-10 instances

SECURITY FEATURES:
- Service account least-privilege IAM roles
- Input validation (file size: max 20MB, MIME type checking)
- Content sanitization in LLM outputs
- Non-root container user
- Health check endpoint for monitoring
- Error message sanitization
- No credentials in container image
- Environment-based configuration

COST OPTIMIZATION:
- Cloud Run: Pay per 100ms, scale to zero
- Firestore: Free tier includes 50K reads/day
- GCS: Regional storage (cheaper than multi-region)
- Image caching: 50% reduction in API calls
- TTL-based expiration: Automatic cleanup

COLOR CODING RECOMMENDATIONS:
- Cloud Run (API): Light Blue
- Firestore (Database): Yellow/Orange
- Cloud Storage (Storage): Green
- Gemini APIs (AI/ML): Purple/Magenta
- Frontend (Client): Light Gray
- Service Accounts (Security): Red/Dark Red
- Cloud Build (CI/CD): Dark Blue
- Monitoring (Logging): Light Purple
```

---

## 📋 Component Legend for GenArch

When adding components to GenArch, use these names for best results:

| Component | GenArch Name | Type |
|-----------|--------------|------|
| Frontend | Cloud Run (Frontend) OR Firebase Hosting | Client |
| FastAPI Backend | Cloud Run | Compute |
| Gemini Vision API | Vertex AI - Gemini Vision | AI/ML |
| Gemini Text API | Vertex AI - Generative AI | AI/ML |
| Firestore | Firestore | Database |
| Cloud Storage | Cloud Storage | Storage |
| Service Account | Service Account | Security |
| Cloud Build | Cloud Build | CI/CD |
| Container Registry | Artifact Registry | Registry |
| Monitoring | Cloud Logging | Monitoring |

---

## 🎨 Visual Layout Suggestions

### Recommended Diagram Layout:

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │     Mobile Web Frontend (HTML/CSS/JS)              │ │
│  │  • Image Upload (Drag/Drop)                        │ │
│  │  • Real-time Risk Visualization                    │ │
│  │  • History & Analytics Display                     │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS/REST
          ┌────────────▼────────────┐
          │    Cloud Run Service    │ (us-central1)
          │   (4Gi, 2vCPU, 0-10)    │
          │                         │
          │  ┌──────────────────┐   │
          │  │ FastAPI Backend  │   │
          │  │ (main.py)        │   │
          │  │ • /analyze       │   │
          │  │ • /history       │   │
          │  │ • /stats         │   │
          │  │ • /health        │   │
          │  └──────────────────┘   │
          │                         │
          │  ┌──────────────────┐   │
          │  │ Vision Module    │   │
          │  │ (model.py)       │   │
          │  └────────┬─────────┘   │
          │           │             │
          │  ┌────────▼─────────┐   │
          │  │ Risk Agent       │   │
          │  │ (adk_agent.py)   │   │
          │  └────────┬─────────┘   │
          │           │             │
          │  ┌────────▼──────────┐  │
          │  │ Cache Manager     │  │
          │  │ (cache_manager.py)│  │
          │  └────────┬──────────┘  │
          └───────────┼──────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌───────────┐
   │ Gemini  │  │Firestore │  │ GCS Bucket│
   │Vision   │  │ Database │  │ (Images)  │
   │API      │  │(analyses)│  │           │
   │         │  │          │  │           │
   └─────────┘  └──────────┘  └───────────┘
```

---

## 🚀 How to Use This Prompt with GenArch

1. **Open GenArch** tool
2. **Paste the full prompt** above into GenArch
3. **GenArch will generate** a detailed GCP architecture diagram
4. **Export** the diagram as PNG/SVG
5. **Use in presentations** or documentation

---

## 📸 Expected Output

GenArch should produce a diagram showing:

✅ All GCP services with proper icons  
✅ Data flow arrows between components  
✅ Service configuration details (memory, CPU, region)  
✅ Database schema elements  
✅ Security/IAM relationships  
✅ External API connections (Gemini)  
✅ CI/CD pipeline  
✅ Monitoring connections  

---

## 💡 Pro Tips for GenArch

1. **Be Specific**: Include resource names, regions, and configurations
2. **Detail Data Flow**: Specify protocols (HTTPS, async, etc.)
3. **Include Scaling**: Mention auto-scaling ranges
4. **Security Focus**: Detail IAM roles and authentication
5. **Add Monitoring**: Include logging and alerting
6. **Specify Tiers**: Separate client, application, data layers
7. **Include Costs**: Mention cost-relevant configurations

---

## 🔄 Alternative: Simpler Version (If GenArch Struggles)

If the full prompt is too complex, use this simplified version:

```
Create a GCP Architecture Diagram for DriveSight with these components:

FRONTEND:
- Cloud Run serving HTML/CSS/JS interface for image upload

API BACKEND:
- Cloud Run FastAPI service (4Gi RAM, 2 vCPU)
- Endpoints: /analyze, /history, /stats

AI SERVICES:
- Gemini Vision 2.0 API (multimodal image analysis)
- Gemini Text API (natural language summaries)

DATA LAYER:
- Firestore NoSQL Database (analyses collection)
- Cloud Storage GCS bucket (store images)

SECURITY:
- Service Account with Storage Admin and Firestore Admin roles
- IAM authentication for GCS and Firestore

MONITORING:
- Cloud Logging for structured logs
- Cloud Build for CI/CD

Show data flow from:
1. Frontend → Cloud Run
2. Cloud Run → Gemini APIs
3. Cloud Run → Firestore
4. Cloud Run → GCS
5. Return results to Frontend
```

---

## 📊 Component Relationships

```
RELATIONSHIPS TO SHOW:

Frontend (Client)
├─► Cloud Run (via HTTPS)
    ├─► Gemini Vision API (for image analysis)
    ├─► Gemini Text API (for summary generation)
    ├─► Firestore (for storing results)
    ├─► Cloud Storage (for storing images)
    └─► Cloud Logging (for structured logs)

Service Accounts
├─► Cloud Run (execution role)
├─► Firestore (read/write permissions)
└─► Cloud Storage (upload permissions)

Cloud Build
└─► Cloud Run (automated deployments)
```

---

## 🎯 Key Metrics to Include

When GenArch generates the diagram, ensure these are visible:

- **Cloud Run**: 4Gi memory, 2 vCPU, 300s timeout, us-central1, auto-scale 0-10
- **Firestore**: Native mode, us-central1, 50K read quota included
- **GCS**: Regional (us-central1), lifecycle policies optional
- **APIs**: Gemini 2.0 Flash (Vision + Text)
- **Cache**: In-memory, 1-hour TTL, SHA-256 hashing

---

## ✅ Validation Checklist

After GenArch generates the diagram, verify it shows:

- [ ] Frontend component with image upload capability
- [ ] Cloud Run service with proper config (memory/CPU)
- [ ] Both Gemini APIs (Vision and Text) separately
- [ ] Firestore database with collection name
- [ ] GCS bucket for image storage
- [ ] Service account connections to all services
- [ ] Data flow arrows between components
- [ ] Region information (us-central1)
- [ ] Auto-scaling configuration (0-10)
- [ ] Monitoring/Logging connection
- [ ] CI/CD pipeline (Cloud Build)

---

**Now paste the main prompt into GenArch to generate your architecture diagram!** 🚀
