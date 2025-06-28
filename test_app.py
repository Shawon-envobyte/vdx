import unittest
import json
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock
from app import app
from config import TestingConfig

class TikTokDownloaderTestCase(unittest.TestCase):
    """Test cases for TikTok Downloader application"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app
        self.app.config.from_object(TestingConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.test_dir
    
    def tearDown(self):
        """Clean up after tests"""
        self.ctx.pop()
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_home_page_web_interface(self):
        """Test home page returns web interface"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TikTok Video Downloader', response.data)
    
    def test_home_page_api_response(self):
        """Test home page returns API info for JSON requests"""
        response = self.client.get('/', 
                                 headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('endpoints', data)
    
    def test_api_info_endpoint(self):
        """Test API info endpoint"""
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('version', data)
        self.assertIn('endpoints', data)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_health_check_detailed(self):
        """Test detailed health check"""
        response = self.client.get('/health?detailed=true')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('system_metrics', data)
    
    def test_download_missing_url(self):
        """Test download endpoint with missing URL"""
        response = self.client.post('/download',
                                  data=json.dumps({}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_download_invalid_url(self):
        """Test download endpoint with invalid URL"""
        response = self.client.post('/download',
                                  data=json.dumps({'url': ''}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_download_non_json_request(self):
        """Test download endpoint with non-JSON request"""
        response = self.client.post('/download',
                                  data='not json',
                                  content_type='text/plain')
        self.assertEqual(response.status_code, 400)
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_success(self, mock_yt_dlp):
        """Test successful download"""
        # Mock yt-dlp behavior
        mock_instance = MagicMock()
        mock_yt_dlp.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'ext': 'mp4',
            'filesize': 1024000
        }
        
        # Create a mock downloaded file
        test_file_path = os.path.join(self.test_dir, 'test_download', 'Test Video.mp4')
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write('test content')
        
        response = self.client.post('/download',
                                  data=json.dumps({'url': 'https://www.tiktok.com/@test/video/123'}),
                                  content_type='application/json')
        
        # Should return success response
        self.assertEqual(response.status_code, 200)
    
    def test_metadata_missing_url(self):
        """Test metadata endpoint with missing URL"""
        response = self.client.post('/metadata',
                                  data=json.dumps({}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('yt_dlp.YoutubeDL')
    def test_metadata_success(self, mock_yt_dlp):
        """Test successful metadata extraction"""
        # Mock yt-dlp behavior
        mock_instance = MagicMock()
        mock_yt_dlp.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'description': 'Test Description',
            'duration': 30,
            'view_count': 1000
        }
        
        response = self.client.post('/metadata',
                                  data=json.dumps({'url': 'https://www.tiktok.com/@test/video/123'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('metadata', data)
    
    def test_formats_missing_url(self):
        """Test formats endpoint with missing URL"""
        response = self.client.get('/formats')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('yt_dlp.YoutubeDL')
    def test_formats_success(self, mock_yt_dlp):
        """Test successful formats extraction"""
        # Mock yt-dlp behavior
        mock_instance = MagicMock()
        mock_yt_dlp.return_value = mock_instance
        mock_instance.extract_info.return_value = {
            'formats': [
                {'format_id': '1', 'ext': 'mp4', 'quality': 'high'},
                {'format_id': '2', 'ext': 'webm', 'quality': 'medium'}
            ]
        }
        
        response = self.client.get('/formats?url=https://www.tiktok.com/@test/video/123')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('formats', data)
    
    def test_404_error_handler(self):
        """Test 404 error handler"""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_405_error_handler(self):
        """Test 405 error handler"""
        response = self.client.put('/download')
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'text/plain; charset=utf-8')
        self.assertIn(b'app_', response.data)

class ConfigTestCase(unittest.TestCase):
    """Test cases for configuration"""
    
    def test_development_config(self):
        """Test development configuration"""
        from config import DevelopmentConfig
        config = DevelopmentConfig()
        self.assertTrue(config.DEBUG)
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
    
    def test_production_config(self):
        """Test production configuration"""
        from config import ProductionConfig
        config = ProductionConfig()
        self.assertFalse(config.DEBUG)
        self.assertEqual(config.LOG_LEVEL, 'WARNING')
    
    def test_testing_config(self):
        """Test testing configuration"""
        from config import TestingConfig
        config = TestingConfig()
        self.assertTrue(config.TESTING)
        self.assertTrue(config.DEBUG)
    
    def test_get_config(self):
        """Test get_config function"""
        from config import get_config, ProductionConfig
        config = get_config('production')
        self.assertEqual(config, ProductionConfig)
    
    def test_yt_dlp_options(self):
        """Test yt-dlp options generation"""
        from config import Config
        options = Config.get_yt_dlp_options('/test/dir')
        self.assertIn('outtmpl', options)
        self.assertIn('http_headers', options)
        self.assertIn('User-Agent', options['http_headers'])

if __name__ == '__main__':
    unittest.main()