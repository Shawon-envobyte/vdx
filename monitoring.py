import logging
import time
import functools
from typing import Dict, Any, Optional
from flask import request, g, jsonify
import psutil
import os
from datetime import datetime

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_available_mb': psutil.virtual_memory().available / (1024 * 1024),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting system metrics: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def log_request_metrics():
        """Log request performance metrics"""
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                g.start_time = start_time
                
                try:
                    result = f(*args, **kwargs)
                    status_code = getattr(result, 'status_code', 200)
                except Exception as e:
                    status_code = 500
                    logging.error(f"Request failed: {e}")
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    # Log request metrics
                    logging.info(
                        f"Request: {request.method} {request.path} - "
                        f"Status: {status_code} - "
                        f"Duration: {duration:.3f}s - "
                        f"IP: {request.remote_addr}"
                    )
                    
                    # Log slow requests
                    if duration > 5.0:  # 5 seconds threshold
                        logging.warning(
                            f"Slow request detected: {request.method} {request.path} - "
                            f"Duration: {duration:.3f}s"
                        )
                
                return result
            return wrapper
        return decorator

class StructuredLogger:
    """Structured logging for better observability"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_download_start(self, url: str, download_id: str, user_ip: str):
        """Log download start event"""
        self.logger.info(
            "Download started",
            extra={
                'event_type': 'download_start',
                'download_id': download_id,
                'url': url,
                'user_ip': user_ip,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_download_success(self, download_id: str, file_size: int, duration: float):
        """Log successful download"""
        self.logger.info(
            "Download completed successfully",
            extra={
                'event_type': 'download_success',
                'download_id': download_id,
                'file_size_bytes': file_size,
                'duration_seconds': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_download_error(self, download_id: str, error: str, duration: float):
        """Log download error"""
        self.logger.error(
            "Download failed",
            extra={
                'event_type': 'download_error',
                'download_id': download_id,
                'error': error,
                'duration_seconds': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                'event_type': 'security_event',
                'security_event_type': event_type,
                'details': details,
                'user_ip': request.remote_addr if request else 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }
        )

def setup_logging(log_level: str = 'INFO', log_format: str = None):
    """Setup application logging"""
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output for Cloud Run
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('yt_dlp').setLevel(logging.WARNING)

def create_health_check_endpoint(app):
    """Create comprehensive health check endpoint"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Comprehensive health check"""
        try:
            # Basic health check
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0'
            }
            
            # Add system metrics if requested
            if request.args.get('detailed') == 'true':
                health_status['system_metrics'] = PerformanceMonitor.get_system_metrics()
                
                # Check disk space
                downloads_dir = app.config.get('UPLOAD_FOLDER', 'downloads')
                if os.path.exists(downloads_dir):
                    disk_usage = psutil.disk_usage(downloads_dir)
                    health_status['disk_space'] = {
                        'total_gb': disk_usage.total / (1024**3),
                        'used_gb': disk_usage.used / (1024**3),
                        'free_gb': disk_usage.free / (1024**3),
                        'percent_used': (disk_usage.used / disk_usage.total) * 100
                    }
            
            return jsonify(health_status), 200
            
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503
    
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Prometheus-style metrics endpoint"""
        try:
            metrics_data = PerformanceMonitor.get_system_metrics()
            
            # Convert to Prometheus format
            prometheus_metrics = []
            for key, value in metrics_data.items():
                if isinstance(value, (int, float)):
                    prometheus_metrics.append(f"app_{key} {value}")
            
            return '\n'.join(prometheus_metrics), 200, {'Content-Type': 'text/plain'}
            
        except Exception as e:
            logging.error(f"Metrics endpoint failed: {e}")
            return f"# Error: {e}", 500, {'Content-Type': 'text/plain'}

def add_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response):
        security_headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in security_headers.items():
            response.headers[header] = value
        return response

def setup_error_handlers(app):
    """Setup comprehensive error handling"""
    
    @app.errorhandler(404)
    def not_found(error):
        logging.warning(f"404 error: {request.url} - IP: {request.remote_addr}")
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        logging.warning(f"405 error: {request.method} {request.url} - IP: {request.remote_addr}")
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        logging.warning(f"413 error: Request too large - IP: {request.remote_addr}")
        return jsonify({'error': 'Request entity too large'}), 413
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        logging.warning(f"Rate limit exceeded - IP: {request.remote_addr}")
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"500 error: {error} - URL: {request.url} - IP: {request.remote_addr}")
        return jsonify({'error': 'Internal server error'}), 500