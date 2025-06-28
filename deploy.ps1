# TikTok Downloader - Google Cloud Run Deployment Script (PowerShell)
# This script builds and deploys the application to Google Cloud Run

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "your-project-id"
)

# Configuration
$SERVICE_NAME = "tiktok-downloader"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$ProjectId/$SERVICE_NAME"

# Colors for output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"

Write-Host "🚀 Starting deployment to Google Cloud Run" -ForegroundColor $Green

# Check if gcloud is installed
try {
    gcloud version | Out-Null
} catch {
    Write-Host "❌ gcloud CLI is not installed. Please install it first." -ForegroundColor $Red
    Write-Host "Download from: https://cloud.google.com/sdk/docs/install" -ForegroundColor $Yellow
    exit 1
}

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker is not installed. Please install it first." -ForegroundColor $Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor $Yellow
    exit 1
}

# Prompt for project ID if not set
if ($ProjectId -eq "your-project-id") {
    Write-Host "⚠️  Please provide your PROJECT_ID as a parameter" -ForegroundColor $Yellow
    Write-Host "Usage: .\deploy.ps1 -ProjectId 'your-actual-project-id'" -ForegroundColor $Yellow
    exit 1
}

$IMAGE_NAME = "gcr.io/$ProjectId/$SERVICE_NAME"

Write-Host "📋 Project ID: $ProjectId" -ForegroundColor $Green
Write-Host "🏷️  Service Name: $SERVICE_NAME" -ForegroundColor $Green
Write-Host "🌍 Region: $REGION" -ForegroundColor $Green

# Set the project
Write-Host "🔧 Setting gcloud project..." -ForegroundColor $Yellow
gcloud config set project $ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set project. Please check your project ID." -ForegroundColor $Red
    exit 1
}

# Enable required APIs
Write-Host "🔌 Enabling required APIs..." -ForegroundColor $Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to enable APIs." -ForegroundColor $Red
    exit 1
}

# Build the Docker image
Write-Host "🏗️  Building Docker image..." -ForegroundColor $Yellow
docker build -t $IMAGE_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build Docker image." -ForegroundColor $Red
    exit 1
}

# Configure Docker to use gcloud as a credential helper
Write-Host "🔑 Configuring Docker authentication..." -ForegroundColor $Yellow
gcloud auth configure-docker

# Push the image to Google Container Registry
Write-Host "📤 Pushing image to Container Registry..." -ForegroundColor $Yellow
docker push $IMAGE_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to push image." -ForegroundColor $Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor $Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --memory 2Gi `
    --cpu 2 `
    --timeout 3600 `
    --max-instances 10 `
    --min-instances 0 `
    --concurrency 80

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to deploy to Cloud Run." -ForegroundColor $Red
    exit 1
}

# Get the service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"

Write-Host "✅ Deployment completed successfully!" -ForegroundColor $Green
Write-Host "🌐 Service URL: $SERVICE_URL" -ForegroundColor $Green
Write-Host "📱 You can now access your TikTok downloader at the URL above" -ForegroundColor $Green

# Optional: Open the URL in browser
Write-Host "🌐 Opening service URL in browser..." -ForegroundColor $Yellow
Start-Process $SERVICE_URL