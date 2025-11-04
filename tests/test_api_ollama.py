"""
Integration tests for Ollama API endpoints
Tests API endpoints for prompt refinement, testing, and model management
"""

import pytest
import json
from unittest.mock import patch, Mock
from flask import Flask
from backend.api.ollama import ollama_bp
from backend.services.ollama_service import OllamaConnectionError, OllamaTimeoutError


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.register_blueprint(ollama_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestRefinePromptEndpoint:
    """Test cases for /api/refine-prompt endpoint"""
    
    @patch('backend.api.ollama.ollama_service.refine_prompt')
    def test_refine_prompt_success(self, mock_refine, client):
        """Test successful prompt refinement"""
        mock_refine.return_value = "You are an expert code reviewer with 10+ years of experience."
        
        response = client.post('/api/refine-prompt', 
                             json={'objective': 'Help users review their code'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'refined_prompt' in data
        assert data['refined_prompt'] == "You are an expert code reviewer with 10+ years of experience."
        assert data['objective'] == 'Help users review their code'
        mock_refine.assert_called_once_with('Help users review their code', None)
    
    @patch('backend.api.ollama.ollama_service.refine_prompt')
    def test_refine_prompt_with_custom_model(self, mock_refine, client):
        """Test prompt refinement with custom model"""
        mock_refine.return_value = "Refined prompt text"
        
        response = client.post('/api/refine-prompt', 
                             json={
                                 'objective': 'Test objective',
                                 'target_model': 'custom-model'
                             })
        
        assert response.status_code == 200
        mock_refine.assert_called_once_with('Test objective', 'custom-model')
    
    def test_refine_prompt_missing_objective(self, client):
        """Test refinement with missing objective"""
        response = client.post('/api/refine-prompt', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'INVALID_JSON'  # Empty dict is treated as invalid JSON
    
    def test_refine_prompt_objective_not_provided(self, client):
        """Test refinement with objective field not provided but valid JSON"""
        response = client.post('/api/refine-prompt', json={'other_field': 'value'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'objective' in data['details']
    
    def test_refine_prompt_empty_objective(self, client):
        """Test refinement with empty objective"""
        response = client.post('/api/refine-prompt', json={'objective': '   '})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
    
    def test_refine_prompt_objective_too_long(self, client):
        """Test refinement with objective that's too long"""
        long_objective = 'x' * 5001
        response = client.post('/api/refine-prompt', json={'objective': long_objective})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'too long' in data['message']
    
    def test_refine_prompt_invalid_json(self, client):
        """Test refinement with invalid JSON"""
        response = client.post('/api/refine-prompt', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'INVALID_JSON'
    
    @patch('backend.api.ollama.ollama_service.refine_prompt')
    def test_refine_prompt_connection_error(self, mock_refine, client):
        """Test refinement with Ollama connection error"""
        mock_refine.side_effect = OllamaConnectionError("Failed to connect")
        
        response = client.post('/api/refine-prompt', 
                             json={'objective': 'Test objective'})
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'OLLAMA_CONNECTION_ERROR'
    
    @patch('backend.api.ollama.ollama_service.refine_prompt')
    def test_refine_prompt_timeout_error(self, mock_refine, client):
        """Test refinement with Ollama timeout error"""
        mock_refine.side_effect = OllamaTimeoutError("Request timed out")
        
        response = client.post('/api/refine-prompt', 
                             json={'objective': 'Test objective'})
        
        assert response.status_code == 408
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'OLLAMA_TIMEOUT'


class TestRunTestEndpoint:
    """Test cases for /api/run-test endpoint"""
    
    @patch('backend.api.ollama.ollama_service.test_prompt')
    def test_run_test_success(self, mock_test, client):
        """Test successful prompt testing"""
        mock_test.return_value = {
            'response': 'Hello! How can I help you today?',
            'execution_time': 1.5,
            'model': 'llama2',
            'temperature': 0.7,
            'system_prompt': 'You are a helpful assistant.',
            'user_input': 'Hello'
        }
        
        response = client.post('/api/run-test', json={
            'system_prompt': 'You are a helpful assistant.',
            'user_input': 'Hello'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['response'] == 'Hello! How can I help you today?'
        assert data['execution_time'] == 1.5
        assert data['model'] == 'llama2'
        assert data['temperature'] == 0.7
        assert 'yaml_config' in data
        assert 'prompt_configuration' in data['yaml_config']
        
        mock_test.assert_called_once_with(
            'You are a helpful assistant.',
            'Hello',
            None,
            None
        )
    
    @patch('backend.api.ollama.ollama_service.test_prompt')
    def test_run_test_with_custom_parameters(self, mock_test, client):
        """Test prompt testing with custom model and temperature"""
        mock_test.return_value = {
            'response': 'Test response',
            'execution_time': 2.0,
            'model': 'custom-model',
            'temperature': 0.9,
            'system_prompt': 'Custom prompt',
            'user_input': 'Test input'
        }
        
        response = client.post('/api/run-test', json={
            'system_prompt': 'Custom prompt',
            'user_input': 'Test input',
            'model': 'custom-model',
            'temperature': 0.9
        })
        
        assert response.status_code == 200
        mock_test.assert_called_once_with(
            'Custom prompt',
            'Test input',
            'custom-model',
            0.9
        )
    
    def test_run_test_missing_system_prompt(self, client):
        """Test testing with missing system prompt"""
        response = client.post('/api/run-test', json={
            'user_input': 'Hello'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'system_prompt' in data['details']
    
    def test_run_test_missing_user_input(self, client):
        """Test testing with missing user input"""
        response = client.post('/api/run-test', json={
            'system_prompt': 'You are helpful.'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'user_input' in data['details']
    
    def test_run_test_invalid_temperature(self, client):
        """Test testing with invalid temperature"""
        response = client.post('/api/run-test', json={
            'system_prompt': 'You are helpful.',
            'user_input': 'Hello',
            'temperature': 3.0  # Too high
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'temperature' in data['details']
    
    def test_run_test_system_prompt_too_long(self, client):
        """Test testing with system prompt that's too long"""
        long_prompt = 'x' * 50001
        response = client.post('/api/run-test', json={
            'system_prompt': long_prompt,
            'user_input': 'Hello'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'system_prompt' in data['details']
    
    def test_run_test_user_input_too_long(self, client):
        """Test testing with user input that's too long"""
        long_input = 'x' * 10001
        response = client.post('/api/run-test', json={
            'system_prompt': 'You are helpful.',
            'user_input': long_input
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'user_input' in data['details']
    
    @patch('backend.api.ollama.ollama_service.test_prompt')
    def test_run_test_connection_error(self, mock_test, client):
        """Test testing with Ollama connection error"""
        mock_test.side_effect = OllamaConnectionError("Failed to connect")
        
        response = client.post('/api/run-test', json={
            'system_prompt': 'You are helpful.',
            'user_input': 'Hello'
        })
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'OLLAMA_CONNECTION_ERROR'


class TestModelsEndpoint:
    """Test cases for /api/models endpoint"""
    
    @patch('backend.api.ollama.ollama_service.get_available_models')
    def test_get_models_success(self, mock_get_models, client):
        """Test successful model retrieval"""
        mock_models = [
            {
                'name': 'llama2:latest',
                'size': 3825819519,
                'modified_at': '2023-12-07T09:32:18.757212583Z',
                'digest': 'sha256:1a838c1e519d'
            },
            {
                'name': 'codellama:latest',
                'size': 3825819520,
                'modified_at': '2023-12-08T10:15:22.123456789Z',
                'digest': 'sha256:2b949d2f620e'
            }
        ]
        mock_get_models.return_value = mock_models
        
        response = client.get('/api/models')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
        assert len(data['models']) == 2
        assert data['models'][0]['name'] == 'llama2:latest'
        assert data['models'][1]['name'] == 'codellama:latest'
    
    @patch('backend.api.ollama.ollama_service.get_available_models')
    def test_get_models_empty_list(self, mock_get_models, client):
        """Test model retrieval with empty list"""
        mock_get_models.return_value = []
        
        response = client.get('/api/models')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 0
        assert data['models'] == []
    
    @patch('backend.api.ollama.ollama_service.get_available_models')
    def test_get_models_connection_error(self, mock_get_models, client):
        """Test model retrieval with connection error"""
        mock_get_models.side_effect = OllamaConnectionError("Failed to connect")
        
        response = client.get('/api/models')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] is True
        assert data['code'] == 'OLLAMA_CONNECTION_ERROR'


class TestHealthEndpoint:
    """Test cases for /api/health endpoint"""
    
    @patch('backend.api.ollama.ollama_service.check_connection')
    def test_health_check_success(self, mock_check, client):
        """Test successful health check"""
        mock_check.return_value = {
            'connected': True,
            'endpoint': 'http://localhost:11434',
            'status': 'healthy',
            'message': 'Successfully connected to Ollama'
        }
        
        response = client.get('/api/ollama/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'Successfully connected' in data['message']
        assert data['status']['connected'] is True
    
    @patch('backend.api.ollama.ollama_service.check_connection')
    def test_health_check_failure(self, mock_check, client):
        """Test failed health check"""
        mock_check.return_value = {
            'connected': False,
            'endpoint': 'http://localhost:11434',
            'status': 'error',
            'message': 'Failed to connect to Ollama'
        }
        
        response = client.get('/api/ollama/health')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] is True
        assert 'Failed to connect' in data['message']
        assert data['status']['connected'] is False


class TestOllamaAPIIntegration:
    """Integration tests for complete API workflows"""
    
    @patch('backend.api.ollama.ollama_service.check_connection')
    @patch('backend.api.ollama.ollama_service.refine_prompt')
    @patch('backend.api.ollama.ollama_service.test_prompt')
    def test_complete_workflow(self, mock_test, mock_refine, mock_check, client):
        """Test complete workflow: health check -> refine -> test"""
        # Mock successful responses
        mock_check.return_value = {
            'connected': True,
            'status': 'healthy',
            'message': 'Connected'
        }
        
        mock_refine.return_value = "You are an expert assistant."
        
        mock_test.return_value = {
            'response': 'I can help you with that!',
            'execution_time': 1.2,
            'model': 'llama2',
            'temperature': 0.7,
            'system_prompt': 'You are an expert assistant.',
            'user_input': 'Can you help me?'
        }
        
        # Step 1: Health check
        health_response = client.get('/api/ollama/health')
        assert health_response.status_code == 200
        
        # Step 2: Refine prompt
        refine_response = client.post('/api/refine-prompt', 
                                    json={'objective': 'Help users with questions'})
        assert refine_response.status_code == 200
        refine_data = json.loads(refine_response.data)
        refined_prompt = refine_data['refined_prompt']
        
        # Step 3: Test refined prompt
        test_response = client.post('/api/run-test', json={
            'system_prompt': refined_prompt,
            'user_input': 'Can you help me?'
        })
        assert test_response.status_code == 200
        test_data = json.loads(test_response.data)
        assert 'yaml_config' in test_data
        assert test_data['response'] == 'I can help you with that!'