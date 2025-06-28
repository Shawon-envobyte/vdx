# TikTok Downloader - Comprehensive Deployment Guide

## 🚀 Quick Fix for Current Issue

The build error you encountered is due to `python3.12-pip` not being available in the deadsnakes PPA <mcreference link="https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa" index="1">1</mcreference>. Here's the immediate solution:

### Use the Fixed Dockerfile

Replace your current `Dockerfile` with the corrected version that properly installs pip:

```dockerfile
# Use Ubuntu 22.04 as base image with Python 3.12
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Install system dependencies and Python 3.12
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3.12-distutils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.12 /usr/bin/python

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python3.12 -m pip install --no-cache-dir --upgrade pip \
    && python3.12 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Expose port
EXPOSE 8080

# Run the application
CMD ["python3.12", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "0", "app:app"]
```

## 📋 Available Dockerfile Options

I've created three Dockerfile variants for different use cases:

### 1. `Dockerfile` (Fixed Basic Version)
- ✅ **Fixed pip installation issue**
- ✅ Ubuntu 22.04 + Python 3.12
- ✅ Simple and straightforward
- 📦 **Use this for immediate deployment**

### 2. `Dockerfile.optimized` (Enhanced Version)
- ✅ All fixes from basic version
- ✅ Security improvements (non-root user)
- ✅ Better performance settings
- ✅ Health checks included
- ✅ Enhanced Gunicorn configuration
- 📦 **Recommended for production**

### 3. `Dockerfile.multistage` (Smallest Image)
- ✅ Multi-stage build for minimal image size
- ✅ Separate build and runtime environments
- ✅ Optimized for Cloud Run cost efficiency
- ✅ Best security practices
- 📦 **Best for high-traffic production**

## 🔧 Deployment Options

### Option 1: Quick Deploy (Windows PowerShell)
```powershell
.\deploy.ps1 -ProjectId "your-project-id"
```

### Option 2: Quick Deploy (Linux/macOS)
```bash
chmod +x deploy.sh
./deploy.sh your-project-id
```

### Option 3: Manual Deployment
```bash
# Build with the fixed Dockerfile
docker build -t gcr.io/your-project-id/tiktok-downloader .

# Push to Google Container Registry
docker push gcr.io/your-project-id/tiktok-downloader

# Deploy to Cloud Run
gcloud run deploy tiktok-downloader \
    --image gcr.io/your-project-id/tiktok-downloader \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2
```

### Option 4: Using Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml
```

## 🐛 Troubleshooting Common Issues

### Issue 1: `python3.12-pip` Package Not Found
**Error**: `E: Unable to locate package python3.12-pip`

**Solution**: The deadsnakes PPA doesn't provide `python3.12-pip` <mcreference link="https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa" index="1">1</mcreference>. Use the fixed Dockerfile that installs pip via `get-pip.py`.

### Issue 2: Permission Denied Errors
**Error**: Permission issues when creating directories

**Solution**: Use `Dockerfile.optimized` which includes proper user management:
```dockerfile
# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
# ... later in file ...
USER appuser
```

### Issue 3: Memory Issues
**Error**: Container killed due to memory limits

**Solutions**:
1. Increase memory allocation:
   ```bash
   --memory 4Gi
   ```
2. Use multi-stage build to reduce memory footprint
3. Optimize Gunicorn settings:
   ```bash
   --max-requests 1000 --max-requests-jitter 100
   ```

### Issue 4: Slow Build Times
**Problem**: Docker builds taking too long

**Solutions**:
1. Use `.dockerignore` to exclude unnecessary files
2. Leverage Docker layer caching
3. Use multi-stage builds
4. Consider using Cloud Build for faster builds

### Issue 5: TikTok Download Failures
**Error**: 403 Forbidden or download failures

**Solutions**:
1. The app includes proper headers to avoid blocking
2. Update yt-dlp regularly:
   ```bash
   pip install --upgrade yt-dlp
   ```
3. Monitor TikTok's rate limiting

## 🔒 Security Best Practices

### 1. Use Non-Root User
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

### 2. Security Headers
The app includes comprehensive security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`

### 3. Environment Variables
Never hardcode secrets. Use environment variables:
```bash
gcloud run deploy --set-env-vars SECRET_KEY=your-secret
```

### 4. Rate Limiting
The enhanced version includes Flask-Limiter for rate limiting:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)
```

## 📊 Monitoring and Observability

### Health Checks
- Basic: `GET /health`
- Detailed: `GET /health?detailed=true`
- Metrics: `GET /metrics` (Prometheus format)

### Logging
Structured logging is implemented for better observability:
```python
from monitoring import StructuredLogger
logger = StructuredLogger(__name__)
logger.log_download_start(url, download_id, user_ip)
```

### Performance Monitoring
```python
from monitoring import PerformanceMonitor
metrics = PerformanceMonitor.get_system_metrics()
```

## 🚀 Performance Optimization

### 1. Gunicorn Configuration
```bash
gunicorn --workers 1 --timeout 0 --preload \
         --max-requests 1000 --max-requests-jitter 100
```

### 2. Cloud Run Settings
```bash
--memory 2Gi --cpu 2 --concurrency 80 \
--max-instances 10 --min-instances 0
```

### 3. Caching Strategy
- Docker layer caching
- pip cache disabled for smaller images
- Static file caching

## 🧪 Testing

### Run Tests Locally
```bash
python -m pytest test_app.py -v
```

### Run with Coverage
```bash
pytest test_app.py --cov=. --cov-report=html
```

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test the health endpoint
ab -n 1000 -c 10 https://your-service-url/health
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Cloud Run auto-scales based on traffic
- Configure `--max-instances` based on expected load
- Use `--min-instances` for warm starts if needed

### Vertical Scaling
- Increase `--memory` for large video processing
- Increase `--cpu` for faster processing
- Monitor resource usage via Cloud Monitoring

### Cost Optimization
- Use `--min-instances 0` to scale to zero
- Monitor and adjust `--concurrency` settings
- Use multi-stage builds for smaller images

## 🔄 CI/CD Pipeline

The included GitHub Actions workflow provides:
- ✅ Automated testing
- ✅ Security scanning
- ✅ Docker builds
- ✅ Staging deployments
- ✅ Production deployments
- ✅ Cleanup of old images

### Setup CI/CD
1. Add secrets to GitHub:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY`
2. Push to `develop` branch for staging
3. Push to `main` branch for production

## 📝 Configuration Management

### Environment-Specific Configs
```python
# Development
FLASK_ENV=development

# Production
FLASK_ENV=production
SECRET_KEY=your-production-secret
```

### Feature Flags
```python
# Enable detailed health checks
HEALTH_CHECK_DETAILED=true

# Enable metrics endpoint
METRICS_ENABLED=true
```

## 🆘 Emergency Procedures

### Rollback Deployment
```bash
# List revisions
gcloud run revisions list --service=tiktok-downloader

# Rollback to previous revision
gcloud run services update-traffic tiktok-downloader \
    --to-revisions=REVISION-NAME=100
```

### Scale to Zero (Emergency Stop)
```bash
gcloud run services update tiktok-downloader \
    --max-instances=0
```

### Emergency Scaling
```bash
gcloud run services update tiktok-downloader \
    --max-instances=50 --memory=4Gi --cpu=4
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks
1. **Update Dependencies**: Monthly security updates
2. **Monitor Logs**: Check for errors and performance issues
3. **Resource Monitoring**: Adjust scaling based on usage
4. **Security Scans**: Regular vulnerability assessments

### Monitoring Dashboards
- Cloud Run metrics in Google Cloud Console
- Custom dashboards for application metrics
- Alerting for error rates and performance

---

**Need Help?** Check the troubleshooting section or open an issue in the repository.