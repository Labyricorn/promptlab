"""
Tests for PromptLab Configuration API Endpoints
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from backend.app import create_app
from backend.config import AppConfig


class TestConfigAPI:
    """Test configuration API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_get_config_success(self, client):
        """Test successful configuration retrieval"""
        with patch('backend.api.config.OllamaService') as mock_ollama:
            mock_service = MagicMock()
            mock_service.check_connection.return_value = True
            mock_ollama.return_value = mock_service
            
            response = client.get('/api/config')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'config' in data
            assert 'ollama_status' in data
            assert data['ollama_status']['connected'] is True
    
    def test_get_config_ollama_disconnected(self, client):
        """Test configuration retrieval with Ollama disconnected"""
        with patch('backend.api.config.OllamaService') as mock_ollama:
            mock_service = MagicMock()
            mock_service.check_connection.return_value = False
            mock_ollama.return_value = mock_service
            
            response = client.get('/api/config')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['ollama_status']['connected'] is False
    
    def test_update_config_success(self, client):
        """Test successful configuration update"""
        with patch('backend.api.config.OllamaService') as mock_ollama:
            mock_service = MagicMock()
            mock_service.check_connection.return_value = True
            mock_ollama.return_value = mock_service
            
            update_data = {
                'ollama_endpoint': 'http://localhost:11435',
                'default_temperature': 0.8
            }
            
            response = client.put('/api/config', 
                                json=update_data,
                                content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['config']['ollama_endpoint'] == 'http://localhost:11435'
            assert data['config']['default_temperature'] == 0.8
    
    def test_update_config_validation_error(self, client):
        """Test configuration update with validation errors"""
        update_data = {
            'default_temperature': 5.0,  # Invalid temperature
            'flask_port': 70000  # Invalid port
        }
        
        response = client.put('/api/config', 
                            json=update_data,
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'details' in data
    
    def test_update_config_invalid_json(self, client):
        """Test configuration update with invalid JSON"""
        response = client.put('/api/config', 
                            data='invalid json',
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'INVALID_JSON'
    
    def test_test_connection_success(self, client):
        """Test successful Ollama connection test"""
        with patch('backend.api.config.OllamaService') as mock_ollama:
            mock_service = MagicMock()
            mock_service.check_connection.return_value = True
            mock_service.get_available_models.return_value = [
                {'name': 'llama2', 'size': 1000000},
                {'name': 'codellama', 'size': 2000000}
            ]
            mock_ollama.return_value = mock_service
            
            test_data = {'endpoint': 'http://localhost:11434'}
            
            response = client.post('/api/config/test-connection',
                                 json=test_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['connected'] is True
            assert data['models_available'] == 2
    
    def test_test_connection_invalid_endpoint(self, client):
        """Test connection test with invalid endpoint"""
        test_data = {'endpoint': 'invalid-url'}
        
        response = client.post('/api/config/test-connection',
                             json=test_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'INVALID_ENDPOINT'
    
    def test_save_config_to_file_json(self, client):
        """Test saving configuration to JSON file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.json')
            
            save_data = {
                'path': config_path,
                'format': 'json'
            }
            
            response = client.post('/api/config/save',
                                 json=save_data,
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert os.path.exists(config_path)
            
            # Verify file content
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                assert 'ollama_endpoint' in saved_config
    
    def test_save_config_invalid_format(self, client):
        """Test saving configuration with invalid format"""
        save_data = {
            'path': 'test.txt',
            'format': 'xml'  # Invalid format
        }
        
        response = client.post('/api/config/save',
                             json=save_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'INVALID_FORMAT'
    
    def test_load_config_from_file_success(self, client):
        """Test loading configuration from file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.json')
            test_config = {
                'ollama_endpoint': 'http://test:11434',
                'default_model': 'test-model',
                'default_temperature': 0.9
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            with patch('backend.api.config.OllamaService') as mock_ollama:
                mock_service = MagicMock()
                mock_service.check_connection.return_value = True
                mock_ollama.return_value = mock_service
                
                load_data = {'path': config_path}
                
                response = client.post('/api/config/load',
                                     json=load_data,
                                     content_type='application/json')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['config']['ollama_endpoint'] == 'http://test:11434'
                assert data['config']['default_model'] == 'test-model'
                assert data['config']['default_temperature'] == 0.9
    
    def test_load_config_file_not_found(self, client):
        """Test loading configuration from non-existent file"""
        load_data = {'path': '/nonexistent/config.json'}
        
        response = client.post('/api/config/load',
                             json=load_data,
                             content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'FILE_NOT_FOUND'
    
    def test_load_config_missing_path(self, client):
        """Test loading configuration without path"""
        response = client.post('/api/config/load',
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'MISSING_PATH'
    
    def test_get_models_with_config_success(self, client):
        """Test getting models with configuration context"""
        with patch('backend.api.config.OllamaService') as mock_ollama_class:
            mock_service = MagicMock()
            mock_service.get_available_models.return_value = [
                {'name': 'llama2', 'size': 1000000},
                {'name': 'codellama', 'size': 2000000}
            ]
            mock_service.get_cache_info.return_value = {
                'cached': True,
                'cache_valid': True,
                'models_count': 2
            }
            mock_ollama_class.return_value = mock_service
            
            response = client.get('/api/config/models')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['models']) == 2
            assert 'default_model' in data
            assert 'cache_info' in data
    
    def test_get_models_with_refresh(self, client):
        """Test getting models with cache refresh"""
        with patch('backend.api.config.OllamaService') as mock_ollama_class:
            mock_service = MagicMock()
            mock_service.refresh_models_cache.return_value = [
                {'name': 'llama2', 'size': 1000000}
            ]
            mock_service.get_cache_info.return_value = {
                'cached': True,
                'cache_valid': True,
                'models_count': 1
            }
            mock_ollama_class.return_value = mock_service
            
            response = client.get('/api/config/models?refresh=true')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            mock_service.refresh_models_cache.assert_called_once()


class TestAppConfig:
    """Test AppConfig class functionality"""
    
    def test_config_validation_success(self):
        """Test successful configuration validation"""
        config = AppConfig()
        errors = config.validate()
        assert len(errors) == 0
    
    def test_config_validation_errors(self):
        """Test configuration validation with errors"""
        config = AppConfig(
            ollama_endpoint="invalid-url",
            default_temperature=5.0,
            flask_port=70000
        )
        errors = config.validate()
        
        assert 'ollama_endpoint' in errors
        assert 'default_temperature' in errors
        assert 'flask_port' in errors
    
    def test_config_from_dict(self):
        """Test creating configuration from dictionary"""
        data = {
            'ollama_endpoint': 'http://test:11434',
            'default_model': 'test-model',
            'default_temperature': '0.8',  # String that should be converted
            'flask_port': '8080'  # String that should be converted
        }
        
        config = AppConfig.from_dict(data)
        
        assert config.ollama_endpoint == 'http://test:11434'
        assert config.default_model == 'test-model'
        assert config.default_temperature == 0.8
        assert config.flask_port == 8080
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary"""
        config = AppConfig(
            ollama_endpoint='http://test:11434',
            default_model='test-model'
        )
        
        data = config.to_dict()
        
        assert data['ollama_endpoint'] == 'http://test:11434'
        assert data['default_model'] == 'test-model'
        assert isinstance(data, dict)
    
    def test_config_from_file_json(self):
        """Test loading configuration from JSON file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.json')
            test_config = {
                'ollama_endpoint': 'http://test:11434',
                'default_model': 'test-model'
            }
            
            with open(config_path, 'w') as f:
                json.dump(test_config, f)
            
            config = AppConfig.from_file(config_path)
            assert config.ollama_endpoint == 'http://test:11434'
            assert config.default_model == 'test-model'
    
    def test_config_from_file_not_found(self):
        """Test loading configuration from non-existent file"""
        with pytest.raises(FileNotFoundError):
            AppConfig.from_file('/nonexistent/config.json')
    
    def test_config_from_file_invalid_json(self):
        """Test loading configuration from invalid JSON file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'invalid_config.json')
            
            with open(config_path, 'w') as f:
                f.write('invalid json content')
            
            with pytest.raises(ValueError, match="Invalid configuration file format"):
                AppConfig.from_file(config_path)