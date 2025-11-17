# DriveSight - Command Reference Card

Print this page for quick reference during development!

---

## 🔧 Local Development

```bash
# Setup environment
cd drivesight
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt

# Run local server
python -m uvicorn app.main:app --reload --port 8080

# Open in browser
# http://localhost:8080/frontend/index.html

# Test API
curl http://localhost:8080/health
curl http://localhost:8080/docs       # Swagger UI
```

---

## 🐳 Docker Commands

```bash
# Build image
docker build -t drivesight:latest .
docker build -t gcr.io/YOUR_PROJECT_ID/drivesight:latest .

# Run container
docker run -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v "$(pwd)/key.json:/app/key.json:ro" \
  drivesight:latest

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/drivesight:latest
```

---

## ☁️ GCP Commands

```bash
# Initialize GCP
gcloud config set project YOUR_PROJECT_ID
bash setup.sh YOUR_PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy drivesight \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 4Gi --cpu 2 --timeout 300

# Get service URL
gcloud run services describe drivesight --region europe-west1
gcloud run services describe drivesight \
  --region europe-west1 --format='value(status.url)'

# View logs
gcloud run logs read drivesight --region europe-west1
gcloud run logs read drivesight --region europe-west1 --follow
gcloud run logs read drivesight --region europe-west1 --limit 100

# Monitor service
gcloud run services describe drivesight --region europe-west1
```

---

## 🔥 Firestore Commands

```bash
# List databases
gcloud firestore databases list

# Query from console
gcloud firestore databases describe

# Export data
gcloud firestore export gs://BUCKET_NAME/backups/$(date +%Y%m%d)

# Restore data
gcloud firestore import gs://BUCKET_NAME/backups/20250115
```

---

## 📦 Cloud Storage Commands

```bash
# List buckets
gsutil ls

# Upload file
gsutil cp file.jpg gs://BUCKET_NAME/

# List files in bucket
gsutil ls gs://BUCKET_NAME/

# Remove file
gsutil rm gs://BUCKET_NAME/file.jpg
```

---

## 🧪 Testing Commands

```bash
# Run local integration tests
bash test-local.sh
bash test-local.sh http://localhost:8080 sample.jpg

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/history
curl http://localhost:8080/stats
curl http://localhost:8080/docs

# Upload test image
curl -X POST -F "image=@test.jpg" \
  http://localhost:8080/analyze

# Load testing
ab -n 100 -c 10 http://localhost:8080/health
```

---

## 📝 Environment Variables

```bash
# Set for local dev
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
source .env

# View current config
echo $GCP_PROJECT_ID
echo $GCS_BUCKET
```

---

## 🔐 IAM & Security

```bash
# Check service account
gcloud iam service-accounts list
gcloud iam service-accounts describe drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Add IAM role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com

# List keys
gcloud iam service-accounts keys list \
  --iam-account=drivesight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

---

## 🔌 API Endpoints

```bash
# Health Check
curl http://localhost:8080/health

# Analyze Image
curl -X POST -F "image=@image.jpg" \
  http://localhost:8080/analyze

# Get History
curl http://localhost:8080/history?limit=10

# Get Statistics
curl http://localhost:8080/stats

# Get Specific Analysis
curl http://localhost:8080/analysis/doc-id-here

# API Documentation
curl http://localhost:8080/docs       # Swagger UI
curl http://localhost:8080/redoc      # ReDoc UI
curl http://localhost:8080/openapi.json
```

---

## 📊 Monitoring Commands

```bash
# View metrics
gcloud run metrics describe drivesight --region europe-west1

# List revisions
gcloud run revisions list --service drivesight --region europe-west1

# Traffic distribution
gcloud run services describe drivesight --region europe-west1 \
  --format='value(status.traffic[].revisionName)'

# Set billing alert
gcloud billing budgets create \
  --billing-account ACCOUNT_ID \
  --display-name "DriveSight Budget" \
  --budget-amount 50
```

---

## 🐛 Debugging

```bash
# Check configuration
cat .env
ls -la key.json

# Test GCP credentials
gcloud auth list
gcloud config get-value project

# Verify Python packages
pip list | grep -E "fastapi|google|pil"

# Check Python version
python --version

# View local logs
tail -f logs/*.log

# Export Cloud Run logs
gcloud run logs read drivesight --limit 1000 > logs.txt
```

---

## 🚀 Quick Deploy Checklist

```bash
# Pre-deployment
[ ] bash setup.sh YOUR_PROJECT_ID
[ ] source .env
[ ] python -m venv .venv && source .venv/bin/activate
[ ] pip install -r app/requirements.txt
[ ] python -m uvicorn app.main:app --reload --port 8080
[ ] curl http://localhost:8080/health

# Build & Deploy
[ ] docker build -t gcr.io/YOUR_PROJECT_ID/drivesight:latest .
[ ] gcloud run deploy drivesight --source .

# Post-deployment
[ ] Get service URL from output
[ ] Test health endpoint
[ ] Open frontend in browser
[ ] Upload test image
[ ] Check Firestore for results
```

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| **Cloud Console** | https://console.cloud.google.com |
| **Cloud Run** | https://console.cloud.google.com/run |
| **Firestore** | https://console.cloud.google.com/firestore |
| **GCS** | https://console.cloud.google.com/storage |
| **API Docs** | http://localhost:8080/docs |
| **FastAPI** | https://fastapi.tiangolo.com |
| **Gemini API** | https://ai.google.dev |
| **Cloud Build** | https://console.cloud.google.com/cloud-build |

---

## 💡 Pro Tips

```bash
# Faster deploy (uses Cloud Build)
gcloud run deploy drivesight --source . --region europe-west1

# Deploy without waiting
gcloud run deploy drivesight --source . --no-wait

# View all recent commands
history | grep "gcloud run"

# Auto-complete gcloud commands
gcloud beta interactive

# Pretty print JSON responses
curl http://localhost:8080/stats | python -m json.tool

# Watch logs in real-time
watch -n 1 "gcloud run logs read drivesight --limit 10"
```

---

## ⏱️ Typical Times

| Task | Time |
|------|------|
| `pip install` | ~30s |
| `gcloud setup.sh` | ~2 min |
| `docker build` | ~1 min |
| `gcloud run deploy` | ~2-3 min |
| First API request | ~1-2s |
| Cached request | ~50ms |
| Full demo cycle | ~5 min |

---

## 🔍 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Module not found | `pip install -r app/requirements.txt` |
| Permission denied | `bash setup.sh YOUR_PROJECT_ID` |
| Port 8080 in use | `lsof -i :8080` then kill process |
| Docker build fails | `docker system prune` then retry |
| Deploy hangs | `Ctrl+C` then use `--source .` flag |
| Empty results | `gcloud run logs read drivesight --tail` |
| Firestore errors | Check IAM roles: `gcloud projects get-iam-policy YOUR_PROJECT_ID` |

---

**Save this page for quick reference! Print or bookmark it during development.**

