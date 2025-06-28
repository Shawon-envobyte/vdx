#!/bin/bash

# TikTok Downloader - Google Cloud Run Deployment Script
# This script builds and deploys the application to Google Cloud Run

set -e

# Configuration
PROJECT_ID="your-project-id"  # Replace with your actual project ID
SERVICE_NAME="tiktok-downloader"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting deployment to Google Cloud Run${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Prompt for project ID if not set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo -e "${YELLOW}⚠️  Please set your PROJECT_ID in this script or provide it as an argument${NC}"
    echo "Usage: ./deploy.sh [PROJECT_ID]"
    exit 1
fi

# Use provided project ID if given as argument
if [ ! -z "$1" ]; then
    PROJECT_ID="$1"
    IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
fi

echo -e "${GREEN}📋 Project ID: $PROJECT_ID${NC}"
echo -e "${GREEN}🏷️  Service Name: $SERVICE_NAME${NC}"
echo -e "${GREEN}🌍 Region: $REGION${NC}"

# Set the project
echo -e "${YELLOW}🔧 Setting gcloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the Docker image
echo -e "${YELLOW}🏗️  Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Push the image to Google Container Registry
echo -e "${YELLOW}📤 Pushing image to Container Registry...${NC}"
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 80

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}📱 You can now access your TikTok downloader at the URL above${NC}"

# Optional: Open the URL in browser (uncomment if desired)
# echo -e "${YELLOW}🌐 Opening service URL in browser...${NC}"
# open $SERVICE_URL || xdg-open $SERVICE_URL || echo "Please manually open: $SERVICE_URL"