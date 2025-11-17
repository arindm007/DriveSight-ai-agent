# DriveSight - Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Setup](#docker-setup)
3. [Cloud Run Deployment](#cloud-run-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring & Debugging](#monitoring--debugging)
6. [Cost Optimization](#cost-optimization)

---

## Local Development

### Prerequisites
- Python 3.11+
- pip package manager
- Virtual environment (recommended)

### Setup Steps

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r app/requirements.txt

# 3. Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
source .env  # or manually set variables

# 4. Run development server
python -m uvicorn app.main:app --reload --port 8080

# 5. Access application
# Backend: http://localhost:8080
# Frontend: http://localhost:8080/frontend/index.html
# API Docs: http://localhost:8080/docs
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Analyze image
curl -X POST -F "image=@sample.jpg" http://localhost:8080/analyze

# Get history
curl http://localhost:8080/history

# Get statistics
curl http://localhost:8080/stats
```

### Development Tips

- **Auto-reload**: Enabled by default with `--reload`
- **Debug logging**: Set `LOG_LEVEL=DEBUG` in .env
- **API documentation**: Visit `http://localhost:8080/docs` for interactive Swagger UI
- **Performance**: Run without `--reload` for production-like testing

---

## Docker Setup

### Build Image

```bash
# Build locally
docker build -t drivesight:latest .

# Build with Google Cloud project
docker build -t gcr.io/YOUR_PROJECT_ID/drivesight:latest .
```

### Run Container

```bash
# Local testing
docker run \
  -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v "$(pwd)/key.json:/app/key.json:ro" \
  drivesight:latest

# With environment file
docker run \
  -p 8080:8080 \
  --env-file .env \
  -v "$(pwd)/key.json:/app/key.json:ro" \
  drivesight:latest
```

### Push to Artifact Registry

```bash
# Configure Docker authentication
gcloud auth configure-docker gcr.io

# Push image
docker push gcr.io/YOUR_PROJECT_ID/drivesight:latest

# Tag additional versions
docker tag gcr.io/YOUR_PROJECT_ID/drivesight:latest \
            gcr.io/YOUR_PROJECT_ID/drivesight:v1.0.0
docker push gcr.io/YOUR_PROJECT_ID/drivesight:v1.0.0
```

---

## Cloud Run Deployment

### Quick Deploy (Recommended for Marathon)

```bash
# Deploy directly from source
gcloud run deploy drivesight \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT_ID,GCS_BUCKET=your-bucket" \
  --service-account drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# After deployment
SERVICE_URL=$(gcloud run services describe drivesight \
  --region europe-west1 --format='value(status.url)')
echo "Service deployed at: $SERVICE_URL"
```

### Deploy Pre-Built Image

```bash
# Deploy existing image
gcloud run deploy drivesight \
  --image gcr.io/YOUR_PROJECT_ID/drivesight:latest \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2
```

### Deploy with Cloud Build

```bash
# Automatic build and deploy
gcloud run deploy drivesight \
  --source . \
  --region europe-west1 \
  --build-service-account drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Or use cloudbuild.yaml
gcloud builds submit --config=cloudbuild.yaml
```

### Configuration Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Memory** | 4Gi | Sufficient for Gemini API calls + caching |
| **CPU** | 2 | 2 vCPU for concurrent requests |
| **Timeout** | 300s | 5 minutes for vision + analysis |
| **Min Instances** | 0 | Scale to zero for cost (will cold start) |
| **Max Instances** | 10 | Prevent runaway costs |
| **Region** | europe-west1 | Closest to US (change as needed) |

---

## Environment Configuration

### GCP Resource Permissions

Service account needs these IAM roles:

```bash
# Required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin" \
  --role="roles/firestore.admin" \
  --role="roles/aiplatform.user"

# For Cloud Run itself (if not using service account auth)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_ID@cloudrun.gserviceaccount.com" \
  --role="roles/firestore.admin" \
  --role="roles/storage.admin"
```

### Environment Variables

Set on Cloud Run service:

```bash
gcloud run services update drivesight \
  --region europe-west1 \
  --set-env-vars "
    GCP_PROJECT_ID=YOUR_PROJECT_ID,
    GCS_BUCKET=your-drivesight-images,
    FIRESTORE_COLLECTION=analyses,
    LOG_LEVEL=INFO,
    CACHE_TTL=3600
  "
```

### Secrets (for sensitive data)

```bash
# Create secret
echo -n "your-secret-value" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Use in Cloud Run
gcloud run services update drivesight \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

---

## Monitoring & Debugging

### Cloud Run Logs

```bash
# View recent logs
gcloud run logs read drivesight --region europe-west1 --limit 50

# Follow logs in real-time
gcloud run logs read drivesight --region europe-west1 --follow

# Filter by severity
gcloud run logs read drivesight --region europe-west1 \
  --filter='severity >= ERROR'

# Search for specific text
gcloud run logs read drivesight --region europe-west1 \
  --filter='textPayload =~ "error.*analysis"'
```

### Cloud Run Metrics

```bash
# View service details
gcloud run services describe drivesight --region europe-west1

# Get request statistics
gcloud monitoring time-series list --filter='resource.type="cloud_run_revision"'

# View using Cloud Console
# https://console.cloud.google.com/run?project=YOUR_PROJECT_ID
```

### Firestore Monitoring

```bash
# View database statistics
gcloud firestore databases describe --location europe-west1

# Query read/write statistics
gcloud logging read 'resource.type="cloud_firestore"' --limit 10

# Monitor from Console
# https://console.cloud.google.com/firestore?project=YOUR_PROJECT_ID
```

### Debugging Failed Requests

```bash
# Enable Cloud Trace
gcloud run services update drivesight \
  --set-env-vars "LOG_LEVEL=DEBUG"

# View traces
gcloud trace list --limit 10

# Export logs for analysis
gcloud run logs read drivesight --limit 1000 > logs.txt
```

---

## Cost Optimization

### Cost Breakdown (Estimated Monthly)

| Service | Usage | Cost | Notes |
|---------|-------|------|-------|
| **Cloud Run** | 10K req/day | $2-5 | Pay per 100ms |
| **Firestore** | 100K doc reads | $3-5 | First 50K free |
| **Cloud Storage** | 1GB images | $0.02 | Regional storage |
| **Gemini API** | 100K requests | $5-10 | Pricing varies |
| **Total** | | **$10-25** | Rough estimate |

### Optimization Strategies

1. **Image Compression**
   ```bash
   # Compress JPEG before upload (max 10MB recommended)
   # Reduces GCS costs and API latency
   ```

2. **Caching**
   - Hash-based caching prevents duplicate analysis
   - Saves ~$0.005 per duplicate request
   - TTL: 1 hour (configurable in config.py)

3. **Firestore**
   - Use collection groups for queries
   - Batch writes for bulk operations
   - Archive old data to BigQuery

4. **Cloud Run**
   - Set Min Instances to 0 (scale to zero)
   - Optimize memory allocation (4GB is sufficient)
   - Use request batching for high volume

5. **Monitoring**
   ```bash
   # Set budget alert
   gcloud billing budgets create \
     --billing-account BILLING_ACCOUNT_ID \
     --display-name "DriveSight Monthly" \
     --budget-amount 50
   ```

---

## Scaling Considerations

### Expected Performance

- **Latency**: 1-2 seconds (first request), 50-100ms (cached)
- **Throughput**: 10-20 req/sec per instance
- **Concurrency**: 1000+ concurrent requests with auto-scaling

### When to Scale

```bash
# Increase CPU/Memory for faster processing
gcloud run services update drivesight \
  --cpu 4 \
  --memory 8Gi

# Increase timeout for large batches
gcloud run services update drivesight \
  --timeout 600

# Configure concurrency limits
gcloud run services update drivesight \
  --concurrency 100
```

### Load Testing

```bash
# Install Apache Bench
# apt-get install apache2-utils

# Simple load test (100 requests, 10 concurrent)
ab -n 100 -c 10 https://drivesight-xxxxx.run.app/health

# Using Apache JMeter for complex scenarios
jmeter -n -t test_plan.jmx -l results.jtl
```

---

## Disaster Recovery

### Backup Strategy

```bash
# Backup Firestore
gcloud firestore export gs://YOUR_BUCKET/backups/$(date +%Y%m%d)

# Restore from backup
gcloud firestore import gs://YOUR_BUCKET/backups/20250115
```

### Rollback Procedure

```bash
# Rollback to previous revision
gcloud run deploy drivesight \
  --image gcr.io/YOUR_PROJECT_ID/drivesight:v0.9.0 \
  --region europe-west1

# Or using revisions
gcloud run revisions list --service drivesight --region europe-west1
gcloud run services update-traffic drivesight \
  --to-revisions drivesight-00001=100
```

---

## Post-Deployment Checklist

- [ ] Service deployed and responding at URL
- [ ] Frontend accessible and functional
- [ ] Test image upload and analysis
- [ ] Verify Firestore contains analysis documents
- [ ] Check Cloud Run logs for errors
- [ ] Monitor error rate (target: <1%)
- [ ] Set up billing alerts
- [ ] Configure log retention
- [ ] Document service URL and credentials
- [ ] Share demo link with stakeholders

---

## Support & Troubleshooting

See main [README.md](./README.md) for detailed troubleshooting.

**Quick Links:**
- Cloud Console: https://console.cloud.google.com
- Cloud Run: https://console.cloud.google.com/run
- Firestore: https://console.cloud.google.com/firestore
- Logs: https://console.cloud.google.com/logs

