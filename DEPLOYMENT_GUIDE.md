# Google Cloud Deployment Guide

## Flight Booking Application - Google App Engine Deployment

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed ([Download here](https://cloud.google.com/sdk/docs/install))
3. **Python 3.9+** installed

---

## Step 1: Install Google Cloud SDK

```powershell
# Download and install from:
https://cloud.google.com/sdk/docs/install

# After installation, initialize:
gcloud init
```

---

## Step 2: Create a GCP Project

```powershell
# Create new project (replace YOUR_PROJECT_ID with your choice)
gcloud projects create flight-booking-app --name="Flight Booking App"

# Set as active project
gcloud config set project flight-booking-app
```

---

## Step 3: Enable Required APIs

```powershell
# Enable App Engine
gcloud services enable appengine.googleapis.com

# Enable Cloud Build (required for deployment)
gcloud services enable cloudbuild.googleapis.com
```

---

## Step 4: Initialize App Engine

```powershell
# Initialize App Engine in your region
gcloud app create --region=asia-south1
```

**Available regions:**

- `asia-south1` (Mumbai)
- `us-central1` (Iowa)
- `europe-west1` (Belgium)

---

## Step 5: Collect Static Files

```powershell
# From your project directory
cd "d:\Python Scripts\Flight-master\Flight-master"

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Collect static files
python manage.py collectstatic --noinput
```

---

## Step 6: Deploy to App Engine

```powershell
# Deploy the application
gcloud app deploy app.yaml --quiet

# This will:
# 1. Upload your code
# 2. Build the application
# 3. Deploy to App Engine
# 4. Return your app URL
```

---

## Step 7: Access Your Application

```powershell
# Open your app in browser
gcloud app browse

# Your app URL will be:
# https://flight-booking-app.appspot.com
```

---

## Important Notes

### Database

The current deployment uses SQLite which is **not persistent** on App Engine. For production, consider:

1. **Cloud SQL (PostgreSQL)** - Recommended for production
2. **Firestore** - NoSQL alternative

### Environment Variables

Set production secrets:

```powershell
# Set secret key (do this before deploying)
gcloud app deploy app.yaml --set-env-vars DJANGO_SECRET_KEY="your-super-secret-key"
```

### Viewing Logs

```powershell
# View application logs
gcloud app logs tail -s default
```

### Costs

- **Free tier**: 28 instance hours/day
- **F2 instance**: ~$0.05/hour when running
- With auto-scaling (min_instances: 0), you only pay when there's traffic

---

## Quick Deploy Commands

```powershell
# Full deployment sequence:
cd "d:\Python Scripts\Flight-master\Flight-master"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py collectstatic --noinput
gcloud app deploy app.yaml --quiet
gcloud app browse
```

---

## Troubleshooting

### Error: "No module named 'flight'"

Ensure all files are uploaded. Check `.gcloudignore` doesn't exclude necessary files.

### Static files not loading

Run `python manage.py collectstatic` before deployment.

### 500 Internal Server Error

Check logs: `gcloud app logs tail -s default`
