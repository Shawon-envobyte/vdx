# TikTok Video Downloader - Google Cloud Run

A Flask-based TikTok video downloader API deployed on Google Cloud Run with Ubuntu 22.04 and Python 3.12.

## Features

- 🎥 Download TikTok videos in various formats
- 🌐 Web interface and REST API
- 📱 Mobile-friendly responsive design
- ☁️ Cloud-native deployment on Google Cloud Run
- 🐳 Containerized with Docker
- 🚀 Auto-scaling and serverless

## Architecture

- **Base Image**: Ubuntu 22.04
- **Python Version**: 3.12
- **Web Framework**: Flask
- **WSGI Server**: Gunicorn
- **Video Downloader**: yt-dlp
- **Platform**: Google Cloud Run

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed and configured
3. **Docker** installed on your local machine
4. **Git** for version control

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd "cloud run"
```

### 2. Set Up Google Cloud Project

```bash
# Create a new project (optional)
gcloud projects create your-project-id

# Set the project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Deploy to Cloud Run

#### Option A: Using PowerShell (Windows)

```powershell
.\deploy.ps1 -ProjectId "your-actual-project-id"
```

#### Option B: Using Bash (Linux/macOS)

```bash
chmod +x deploy.sh
./deploy.sh your-actual-project-id
```

#### Option C: Using Google Cloud Build

```bash
gcloud builds submit --config cloudbuild.yaml
```

#### Option D: Manual Deployment

```bash
# Build and push the image
docker build -t gcr.io/your-project-id/tiktok-downloader .
docker push gcr.io/your-project-id/tiktok-downloader

# Deploy to Cloud Run
gcloud run deploy tiktok-downloader \
    --image gcr.io/your-project-id/tiktok-downloader \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 80
```

## API Endpoints

### Web Interface
- `GET /` - Web interface for downloading videos

### API Endpoints
- `GET /api` - API information
- `GET /health` - Health check
- `POST /download` - Download TikTok video
- `POST /metadata` - Get video metadata
- `GET /formats` - Get available formats

### Example API Usage

```bash
# Download a video
curl -X POST https://your-service-url/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@username/video/1234567890"}'

# Get video metadata
curl -X POST https://your-service-url/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@username/video/1234567890"}'
```

## Configuration

### Environment Variables

- `PORT`: Server port (default: 8080)
- `PYTHONUNBUFFERED`: Python output buffering (set to 1)

### Cloud Run Configuration

- **Memory**: 2 GiB
- **CPU**: 2 vCPU
- **Timeout**: 3600 seconds (1 hour)
- **Max Instances**: 10
- **Min Instances**: 0 (scales to zero)
- **Concurrency**: 80 requests per instance

## File Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .dockerignore         # Docker ignore file
├── cloudbuild.yaml       # Google Cloud Build configuration
├── deploy.sh             # Bash deployment script
├── deploy.ps1            # PowerShell deployment script
├── README.md             # This file
├── templates/
│   └── index.html        # Web interface template
└── downloads/            # Downloaded files directory
```

## Dependencies

- **Flask 2.3.3** - Web framework
- **yt-dlp** - Video downloader
- **gunicorn 21.2.0** - WSGI server
- **requests** - HTTP library
- **Other dependencies** - See requirements.txt

## Security Features

- ✅ No hardcoded secrets
- ✅ Proper error handling
- ✅ Input validation
- ✅ Rate limiting via Cloud Run
- ✅ HTTPS by default
- ✅ Container security best practices

## Monitoring and Logging

- **Cloud Logging**: Automatic log collection
- **Cloud Monitoring**: Built-in metrics
- **Health Checks**: `/health` endpoint
- **Error Tracking**: Automatic error reporting

## Troubleshooting

### Common Issues

1. **403 Forbidden Errors**
   - The app includes proper headers and user agents to avoid TikTok blocking
   - If issues persist, check TikTok's rate limiting

2. **Memory Issues**
   - Increase memory allocation in Cloud Run settings
   - Current setting: 2 GiB should handle most videos

3. **Timeout Issues**
   - Large videos may take time to download
   - Current timeout: 3600 seconds (1 hour)

4. **Build Failures**
   - Ensure Docker is running
   - Check internet connection for package downloads
   - Verify Google Cloud permissions

### Viewing Logs

```bash
# View recent logs
gcloud logs read --service=tiktok-downloader --limit=50

# Stream logs in real-time
gcloud logs tail --service=tiktok-downloader
```

## Cost Optimization

- **Scales to Zero**: No charges when not in use
- **Pay per Request**: Only pay for actual usage
- **Efficient Resource Usage**: Optimized container size
- **Auto-scaling**: Handles traffic spikes efficiently

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Google Cloud Run documentation
3. Open an issue in the repository

---

**Note**: This application is for educational purposes. Please respect TikTok's terms of service and copyright laws when using this tool.