#!/bin/bash
# DriveSight GCP Setup Script
# Run this once to initialize all required GCP resources

set -e

# Configuration
PROJECT_ID="${1:-your-project-id}"
REGION="us-central1"
BUCKET_NAME="${PROJECT_ID}-drivesight-images"
FIRESTORE_COLLECTION="analyses"
SA_NAME="drivesight-sa"

echo "🚀 Starting DriveSight GCP Setup"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Validate project ID
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Please provide your GCP Project ID as argument"
    echo "Usage: ./setup.sh <PROJECT_ID>"
    exit 1
fi

# Step 1: Set project
echo "📋 Setting GCP project..."
gcloud config set project "$PROJECT_ID"

# Step 2: Enable APIs
echo "🔌 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    iam.googleapis.com

# Step 3: Create Cloud Storage bucket
echo "📦 Creating Cloud Storage bucket..."
if gsutil ls "gs://${BUCKET_NAME}" &>/dev/null; then
    echo "   ✓ Bucket already exists: gs://${BUCKET_NAME}"
else
    gsutil mb -l "$REGION" "gs://${BUCKET_NAME}"
    echo "   ✓ Created bucket: gs://${BUCKET_NAME}"
fi

# Step 4: Initialize Firestore (Native mode)
echo "🔥 Setting up Firestore..."
if gcloud firestore databases list --format="value(name)" | grep -q "default"; then
    echo "   ✓ Firestore database already exists"
else
    gcloud firestore databases create --region "$REGION" --type=firestore-native
    echo "   ✓ Created Firestore database"
fi

# Step 5: Create service account
echo "👤 Setting up service account..."
if gcloud iam service-accounts describe "${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" &>/dev/null; then
    echo "   ✓ Service account already exists"
else
    gcloud iam service-accounts create "$SA_NAME" --display-name "DriveSight Service Account"
    echo "   ✓ Created service account"
fi

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Step 6: Grant IAM roles
echo "🔐 Granting IAM roles..."

ROLES=(
    "roles/storage.objectAdmin"
    "roles/firestore.admin"
    "roles/aiplatform.user"
)

for role in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$role" \
        --condition=None \
        2>/dev/null || echo "   ✓ Role $role already assigned"
done

# Step 7: Create service account key (for local development)
echo "🔑 Creating service account key..."
KEY_FILE="key.json"
if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL"
    echo "   ✓ Created key: $KEY_FILE"
else
    echo "   ℹ️  Key file already exists: $KEY_FILE"
fi

# Step 8: Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
GCP_PROJECT_ID=$PROJECT_ID
GCS_BUCKET=$BUCKET_NAME
FIRESTORE_COLLECTION=$FIRESTORE_COLLECTION
LOG_LEVEL=INFO
EOF
echo "   ✓ Created .env file"

# Step 9: Export credentials
echo "🔓 Setting up credentials for local development..."
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
echo "   ✓ GOOGLE_APPLICATION_CREDENTIALS set"

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📌 Next Steps:"
echo "   1. Update .env file with any custom values (if needed)"
echo "   2. Install Python dependencies: pip install -r app/requirements.txt"
echo "   3. Run local server: python -m uvicorn app.main:app --reload --port 8080"
echo "   4. Open frontend: http://localhost:8080/frontend/index.html"
echo "   5. Deploy to Cloud Run:"
echo "      gcloud run deploy drivesight --source . --region $REGION --allow-unauthenticated"
echo ""
echo "🔗 Resources:"
echo "   Cloud Console: https://console.cloud.google.com/welcome?project=$PROJECT_ID"
echo "   Firestore: https://console.cloud.google.com/firestore?project=$PROJECT_ID"
echo "   Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "   Cloud Storage: https://console.cloud.google.com/storage?project=$PROJECT_ID"
echo ""
