from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile
import uuid
from datetime import datetime
import shutil
import json

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create downloads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET'])
def home():
    """Home page with web interface"""
    # Check if request wants JSON (API call)
    if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'message': 'TikTok Video Downloader API',
            'version': '1.0',
            'endpoints': {
                'POST /download': 'Download TikTok video',
                'POST /metadata': 'Get video metadata',
                'GET /formats': 'Get all available video formats and metadata (use ?url=<tiktok_url>)',
                'GET /health': 'Health check'
            }
        })
    # Otherwise serve the web interface
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        'message': 'TikTok Video Downloader API',
        'version': '1.0',
        'endpoints': {
            'POST /download': 'Download TikTok video',
            'POST /metadata': 'Get video metadata',
            'GET /formats': 'Get all available video formats and metadata (use ?url=<tiktok_url>)',
            'GET /health': 'Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/download', methods=['POST'])
def download_video():
    """Download TikTok video endpoint"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required parameter: url'
            }), 400
        
        video_url = data['url']
        
        # Validate URL
        if not video_url or not isinstance(video_url, str):
            return jsonify({
                'error': 'Invalid URL provided'
            }), 400
        
        # Create unique directory for this download
        download_id = str(uuid.uuid4())
        download_dir = os.path.join(app.config['UPLOAD_FOLDER'], download_id)
        os.makedirs(download_dir, exist_ok=True)
        
        # Configure yt-dlp options with headers and user agent to avoid 403 errors
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'format': 'best/mp4/any',  # Try best quality, fallback to mp4, then any available format
            'noplaylist': True,
            'extract_flat': False,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
            'retry_sleep_functions': {'http': lambda n: min(4 ** n, 60)},
        }
        
        # Download the video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_title = info.get('title', 'video')
            video_ext = info.get('ext', 'mp4')
            video_path = os.path.join(download_dir, f"{video_title}.{video_ext}")
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({
                'error': 'Failed to download video'
            }), 500
        
        # Create a clean filename
        import re
        # Remove special characters and limit length
        clean_title = re.sub(r'[^\w\s-]', '', video_title)[:50]
        clean_title = re.sub(r'\s+', '_', clean_title.strip())
        if not clean_title:
            clean_title = 'tiktok_video'
        
        # Rename the downloaded video with clean filename
        new_video_name = f"tiktok_{download_id}_{clean_title}.{video_ext}"
        new_video_path = os.path.join(download_dir, new_video_name)
        os.rename(video_path, new_video_path)
        
        # Get file size
        file_size = os.path.getsize(new_video_path)
        
        return jsonify({
            'success': True,
            'message': 'Video downloaded successfully',
            'download_id': download_id,
            'filename': new_video_name,
            'file_size': file_size,
            'download_url': f'/file/{download_id}/{new_video_name}'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Download failed: {str(e)}'
        }), 500

@app.route('/metadata', methods=['POST'])
def get_metadata():
    """Get TikTok video metadata endpoint"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required parameter: url'
            }), 400
        
        video_url = data['url']
        
        # Validate URL
        if not video_url or not isinstance(video_url, str):
            return jsonify({
                'error': 'Invalid URL provided'
            }), 400
        
        # Get video metadata using yt-dlp with headers to avoid 403 errors
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            metadata = {
                'title': info.get('title', 'N/A'),
                'uploader': info.get('uploader', 'N/A'),
                'duration': info.get('duration', 'N/A'),
                'view_count': info.get('view_count', 'N/A'),
                'like_count': info.get('like_count', 'N/A'),
                'description': info.get('description', 'N/A'),
                'upload_date': info.get('upload_date', 'N/A'),
                'webpage_url': info.get('webpage_url', video_url)
            }
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get metadata: {str(e)}'
        }), 500

@app.route('/formats', methods=['GET'])
def get_video_formats():
    """Get all available video formats and metadata for a TikTok video"""
    try:
        # Get URL from query parameter
        video_url = request.args.get('url')
        
        if not video_url:
            return jsonify({
                'error': 'Missing required parameter: url'
            }), 400
        
        # Validate URL
        if not isinstance(video_url, str):
            return jsonify({
                'error': 'Invalid URL provided'
            }), 400
        
        # Get video information and formats using yt-dlp with headers to avoid 403 errors
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # Extract comprehensive metadata
            metadata = {
                'title': info.get('title', 'N/A'),
                'uploader': info.get('uploader', 'N/A'),
                'uploader_id': info.get('uploader_id', 'N/A'),
                'duration': info.get('duration', 'N/A'),
                'view_count': info.get('view_count', 'N/A'),
                'like_count': info.get('like_count', 'N/A'),
                'comment_count': info.get('comment_count', 'N/A'),
                'description': info.get('description', 'N/A'),
                'upload_date': info.get('upload_date', 'N/A'),
                'webpage_url': info.get('webpage_url', video_url),
                'thumbnail': info.get('thumbnail', 'N/A'),
                'width': info.get('width', 'N/A'),
                'height': info.get('height', 'N/A'),
                'fps': info.get('fps', 'N/A'),
                'filesize': info.get('filesize', 'N/A'),
                'ext': info.get('ext', 'N/A')
            }
            
            # Extract available formats
            formats = []
            if 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    format_info = {
                        'format_id': fmt.get('format_id', 'N/A'),
                        'ext': fmt.get('ext', 'N/A'),
                        'width': fmt.get('width', 'N/A'),
                        'height': fmt.get('height', 'N/A'),
                        'fps': fmt.get('fps', 'N/A'),
                        'filesize': fmt.get('filesize', 'N/A'),
                        'tbr': fmt.get('tbr', 'N/A'),  # Total bitrate
                        'vbr': fmt.get('vbr', 'N/A'),  # Video bitrate
                        'abr': fmt.get('abr', 'N/A'),  # Audio bitrate
                        'acodec': fmt.get('acodec', 'N/A'),
                        'vcodec': fmt.get('vcodec', 'N/A'),
                        'format_note': fmt.get('format_note', 'N/A'),
                        'quality': fmt.get('quality', 'N/A'),
                        'url': fmt.get('url', 'N/A')
                    }
                    formats.append(format_info)
            
            # Get the best format info
            best_format = None
            if 'format' in info:
                best_format = {
                    'format_id': info.get('format_id', 'N/A'),
                    'ext': info.get('ext', 'N/A'),
                    'width': info.get('width', 'N/A'),
                    'height': info.get('height', 'N/A'),
                    'fps': info.get('fps', 'N/A'),
                    'filesize': info.get('filesize', 'N/A')
                }
        
        return jsonify({
            'success': True,
            'metadata': metadata,
            'formats': formats,
            'best_format': best_format,
            'total_formats': len(formats)
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get video formats: {str(e)}'
        }), 500

@app.route('/file/<download_id>/<filename>', methods=['GET'])
def download_file(download_id, filename):
    """Serve downloaded files"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], download_id, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'error': 'File not found'
            }), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to serve file: {str(e)}'
        }), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old downloaded files"""
    try:
        data = request.get_json()
        download_id = data.get('download_id') if data else None
        
        if download_id:
            # Clean up specific download
            download_dir = os.path.join(app.config['UPLOAD_FOLDER'], download_id)
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)
                return jsonify({
                    'success': True,
                    'message': f'Cleaned up download {download_id}'
                })
            else:
                return jsonify({
                    'error': 'Download ID not found'
                }), 404
        else:
            # Clean up all downloads (use with caution)
            if os.path.exists(app.config['UPLOAD_FOLDER']):
                shutil.rmtree(app.config['UPLOAD_FOLDER'])
                os.makedirs(app.config['UPLOAD_FOLDER'])
                return jsonify({
                    'success': True,
                    'message': 'Cleaned up all downloads'
                })
        
    except Exception as e:
        return jsonify({
            'error': f'Cleanup failed: {str(e)}'
        }), 500

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear yt-dlp cache to fix download issues"""
    try:
        import subprocess
        from pathlib import Path
        
        # Try to clear cache using yt-dlp command
        try:
            result = subprocess.run(['yt-dlp', '--rm-cache-dir'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return jsonify({
                    'success': True,
                    'message': 'yt-dlp cache cleared successfully',
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to clear cache via yt-dlp command',
                    'error': result.stderr
                })
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'message': 'Cache clearing timed out'
            }), 500
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'message': 'yt-dlp command not found. Please ensure yt-dlp is installed and in PATH.'
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f'Cache clearing failed: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method not allowed'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Get port from environment variable for Cloud Run compatibility
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)