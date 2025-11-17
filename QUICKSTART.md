# DriveSight - Quick Start Guide (Marathon Edition)

**Build Time: ~30 minutes to fully deployed**  
**Demo Ready: ~2 hours with testing**

---

## 🚀 Phase 1: Local Setup (10 minutes)

```bash
# 1. Navigate to project
cd drivesight

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r app/requirements.txt

# 4. Verify installation
python -c "import google; import fastapi; print('✓ Dependencies OK')"
```

---

## 🔧 Phase 2: GCP Configuration (5 minutes)

```bash
# 1. Run automated setup (replace YOUR_PROJECT_ID)
bash setup.sh YOUR_PROJECT_ID

# This will:
# ✓ Enable APIs (Cloud Run, Firestore, GCS, AI Platform)
# ✓ Create Firestore database
# ✓ Create service account & key
# ✓ Set up bucket
# ✓ Generate .env file

# 2. Verify setup
cat .env
ls -la key.json  # Should exist
```

---

## 💻 Phase 3: Test Locally (5 minutes)

```bash
# 1. Start development server
python -m uvicorn app.main:app --reload --port 8080

# 2. In another terminal, test API
curl http://localhost:8080/health

# Output should be:
# {"status":"healthy","service":"DriveSight","version":"1.0.0"}

# 3. Open frontend in browser
# http://localhost:8080/frontend/index.html

# 4. Try uploading a test image
# - Drag/drop or click to select image
# - Click "Analyze Image"
# - Should see results with risk score
```

---

## 🐳 Phase 4: Containerize (5 minutes)

```bash
# 1. Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/drivesight:latest .

# 2. Test container locally
docker run \
  -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/key.json \
  -v "$(pwd)/key.json:/app/key.json:ro" \
  gcr.io/YOUR_PROJECT_ID/drivesight:latest

# 3. Test from browser
# http://localhost:8080/frontend/index.html

# 4. Stop container (Ctrl+C)
```

---

## ☁️ Phase 5: Deploy to Cloud Run (5 minutes)

```bash
# OPTION A: Fastest (recommended for marathon)
gcloud run deploy drivesight \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --quiet

# OPTION B: From pre-built image
# (After pushing image to gcr.io)
gcloud run deploy drivesight \
  --image gcr.io/YOUR_PROJECT_ID/drivesight:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --quiet

# 3. Get service URL
SERVICE_URL=$(gcloud run services describe drivesight \
  --region us-central1 --format='value(status.url)')
echo "Deployed at: $SERVICE_URL"

# 4. Test deployed service
curl $SERVICE_URL/health

# 5. Open frontend in browser
# $SERVICE_URL/frontend/index.html
```

---

## 📊 Phase 6: Demo Script (30 seconds)

```
1. Open browser to deployed service frontend
2. Upload sample dashcam image
3. Show results:
   - Risk Score: [0-100]
   - Risk Label: HIGH/MODERATE/LOW
   - Summary: Natural language analysis
   - Detected objects
   - Scene details (lighting, weather, traffic)
4. Click "Recent Analyses" to show history
5. Open Firestore console to show stored data:
   gcloud firestore databases list
6. Show Cloud Run metrics:
   gcloud run services describe drivesight --region us-central1
```

---

## 📋 Quick Reference

### File Structure
```
drivesight/
├── app/
│   ├── main.py          (FastAPI endpoints)
│   ├── model.py         (Gemini Vision)
│   ├── adk_agent.py     (Risk scoring)
│   ├── mcp_toolbox.py   (Firestore/GCS)
│   └── ...
├── frontend/
│   └── index.html       (Mobile UI)
├── Dockerfile
├── setup.sh
└── README.md
```

### Key Endpoints
```
GET  /health              - Health check
POST /analyze             - Analyze image
GET  /history?limit=10    - Get history
GET  /stats               - Get statistics
GET  /                    - API info
```

### Environment Variables
```bash
GCP_PROJECT_ID=your-project-id
GCS_BUCKET=your-bucket-name
FIRESTORE_COLLECTION=analyses
LOG_LEVEL=INFO
CACHE_TTL=3600
```

---

## ✅ Verification Checklist

- [ ] Local setup complete (`pip install` successful)
- [ ] GCP setup complete (`setup.sh` ran without errors)
- [ ] Local server running (`/health` responds)
- [ ] Frontend loads (`/frontend/index.html` accessible)
- [ ] Image analysis works (upload → analyze → results)
- [ ] Docker image builds (`docker build` successful)
- [ ] Container runs locally (`docker run` successful)
- [ ] Cloud Run deployed (`gcloud run deploy` successful)
- [ ] Deployed service responds (`curl $SERVICE_URL/health`)
- [ ] Frontend accessible on deployed URL

---

## 🐛 Troubleshooting (30 seconds)

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'google'` | Run `pip install -r app/requirements.txt` |
| `"GCP_PROJECT_ID not configured"` | Run `source .env` and verify `echo $GCP_PROJECT_ID` |
| `Permission denied: key.json` | Run `bash setup.sh YOUR_PROJECT_ID` again |
| `Docker image won't build` | Ensure Docker desktop is running |
| `Cloud Run deployment hangs` | Use `gcloud run deploy --source .` instead |
| `Blank results from analysis` | Check logs: `gcloud run logs read drivesight --tail` |

---

## 📈 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Local startup** | <5s | Uvicorn reload |
| **First analysis** | 1-2s | Gemini API latency |
| **Cached analysis** | <100ms | Hash lookup |
| **Cloud Run cold start** | <15s | First request after deploy |
| **Cloud Run warm start** | 1-2s | Subsequent requests |

---

## 🎯 Demo Impact Points

1. **Serverless Architecture** - Show Cloud Run URL
2. **Gemini Vision** - Explain multimodal analysis
3. **Risk Scoring** - Show score computation
4. **Firestore** - Open console, show stored data
5. **Mobile UI** - Responsive design on phone browser
6. **Caching** - Upload same image twice, show speed improvement
7. **Error Handling** - Try invalid image, show graceful error
8. **Logs** - `gcloud run logs read` to show processing details

---

## 🔗 Useful Links

- **Cloud Console**: https://console.cloud.google.com
- **Cloud Run**: https://console.cloud.google.com/run
- **Firestore**: https://console.cloud.google.com/firestore
- **API Docs**: `http://localhost:8080/docs` (local)
- **FastAPI**: https://fastapi.tiangolo.com
- **Gemini API**: https://ai.google.dev

---

## ⏱️ Timeline (Typical)

| Phase | Time | Cumulative |
|-------|------|-----------|
| Local setup | 10 min | 10 min |
| GCP config | 5 min | 15 min |
| Local testing | 5 min | 20 min |
| Docker build | 5 min | 25 min |
| Cloud Run deploy | 5 min | 30 min |
| **Demo ready** | | **~30 min** |
| Testing & refinement | 1-2 hr | 2-2.5 hr |
| Blog writing | 1-2 hr | 3-4 hr |

---

## 💡 Pro Tips

1. **Use `--source .`** - Cloud Build automatically handles Docker build
2. **Cache aggressively** - Same image analyzed twice = instant results
3. **Monitor costs** - Set billing alert for Cloud Run usage
4. **Test endpoints with curl** - Faster iteration than UI
5. **Use `gcloud logs` command** - For debugging issues
6. **Set `LOG_LEVEL=DEBUG`** - For detailed troubleshooting
7. **Save service URL** - Bookmark it after deployment

---

## 📞 Need Help?

1. **Check README.md** - Comprehensive documentation
2. **Check DEPLOYMENT.md** - Detailed deployment guide
3. **Review logs** - `gcloud run logs read drivesight --follow`
4. **Test locally first** - Easier to debug locally than on Cloud Run
5. **Verify IAM permissions** - Most errors are permission-related

---

**You're ready! Start with `bash setup.sh YOUR_PROJECT_ID` 🚀**
