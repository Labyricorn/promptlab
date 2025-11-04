"""
Integration tests for Ollama service
Tests Ollama communication, prompt refinement, and testing workflows
"""

import pytest
import requests
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from backend.services.ollama_service import OllamaService, OllamaConnectionError, OllamaTimeoutError


class TestOllamaService:
    """Test cases for OllamaService"""
    
    @pytest.fixture
    def ollama_service(self):
        """Create OllamaService instance for testing"""
        return OllamaService(endpoint="http://localhost:11434", timeout=10, max_retries=2)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response object"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = Mock()
        return mock_resp
    
    def test_init_with_defaults(self):
        """Test OllamaService initialization with default values"""
        service = OllamaService()
        assert service.endpoint == "http://localhost:11434"  # From config
        assert service.timeout == 30
        assert service.max_retries == 3
        assert service.session is not None
    
    def test_init_with_custom_values(self):
        """Test OllamaService initialization with custom values"""
        service = OllamaService(
            endpoint="http://custom:8080",
            timeout=60,
            max_retries=5
        )
        assert service.endpoint == "http://custom:8080"
        assert service.timeout == 60
        assert service.max_retries == 5
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_make_request_success(self, mock_request, ollama_service, mock_response):
        """Test successful HTTP request"""
        mock_request.return_value = mock_response
        
        response = ollama_service._make_request('GET', 'api/tags')
        
        assert response == mock_response
        mock_request.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_make_request_timeout_retry(self, mock_request, ollama_service):
        """Test request timeout with retry logic"""
        mock_request.side_effect = requests.exceptions.Timeout("Timeout")
        
        with pytest.raises(OllamaTimeoutError) as exc_info:
            ollama_service._make_request('GET', 'api/tags')
        
        assert "Request timed out" in str(exc_info.value)
        assert mock_request.call_count == ollama_service.max_retries
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_make_request_connection_error_retry(self, mock_request, ollama_service):
        """Test connection error with retry logic"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_service._make_request('GET', 'api/tags')
        
        assert "Failed to connect to Ollama" in str(exc_info.value)
        assert mock_request.call_count == ollama_service.max_retries
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_make_request_server_error_retry(self, mock_request, ollama_service):
        """Test server error (5xx) with retry logic"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_request.return_value = mock_response
        
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_service._make_request('GET', 'api/tags')
        
        assert "Ollama server error: 500" in str(exc_info.value)
        assert mock_request.call_count == ollama_service.max_retries
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_make_request_client_error_no_retry(self, mock_request, ollama_service):
        """Test client error (4xx) without retry"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_request.return_value = mock_response
        
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_service._make_request('GET', 'api/tags')
        
        assert "Ollama API error: 404" in str(exc_info.value)
        assert mock_request.call_count == 1  # No retry for client errors
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_check_connection_success(self, mock_request, ollama_service, mock_response):
        """Test successful connection check"""
        mock_request.return_value = mock_response
        
        result = ollama_service.check_connection()
        
        assert result['connected'] is True
        assert result['status'] == 'healthy'
        assert 'Successfully connected' in result['message']
        assert result['endpoint'] == ollama_service.endpoint
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_check_connection_failure(self, mock_request, ollama_service):
        """Test failed connection check"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = ollama_service.check_connection()
        
        assert result['connected'] is False
        assert result['status'] == 'error'
        assert 'Failed to connect to Ollama' in result['message']
        assert result['endpoint'] == ollama_service.endpoint
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_get_available_models_success(self, mock_request, ollama_service, mock_response):
        """Test successful model retrieval"""
        mock_models_data = {
            'models': [
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
        }
        mock_response.json.return_value = mock_models_data
        mock_request.return_value = mock_response
        
        models = ollama_service.get_available_models()
        
        assert len(models) == 2
        assert models[0]['name'] == 'llama2:latest'
        assert models[0]['size'] == 3825819519
        assert models[1]['name'] == 'codellama:latest'
        assert models[1]['size'] == 3825819520
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_get_available_models_empty_response(self, mock_request, ollama_service, mock_response):
        """Test model retrieval with empty response"""
        mock_response.json.return_value = {'models': []}
        mock_request.return_value = mock_response
        
        models = ollama_service.get_available_models()
        
        assert models == []
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_get_available_models_connection_error(self, mock_request, ollama_service):
        """Test model retrieval with connection error"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(OllamaConnectionError):
            ollama_service.get_available_models()
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_health_check_success(self, mock_request, ollama_service, mock_response):
        """Test successful health check"""
        mock_request.return_value = mock_response
        
        result = ollama_service.health_check()
        
        assert result is True
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_health_check_failure(self, mock_request, ollama_service):
        """Test failed health check"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = ollama_service.health_check()
        
        assert result is False
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_refine_prompt_success(self, mock_request, ollama_service, mock_response):
        """Test successful prompt refinement"""
        mock_generate_response = {
            'response': 'You are an expert code reviewer. Your task is to analyze code submissions and provide constructive feedback focusing on best practices, potential bugs, and improvements.'
        }
        mock_response.json.return_value = mock_generate_response
        mock_request.return_value = mock_response
        
        objective = "Help users review their code"
        refined_prompt = ollama_service.refine_prompt(objective)
        
        assert refined_prompt == mock_generate_response['response']
        
        # Verify the request was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'POST'  # method
        assert 'api/generate' in call_args[0][1]  # URL
        
        # Check request payload
        request_data = call_args[1]['json']
        assert 'model' in request_data
        assert 'prompt' in request_data
        assert objective in request_data['prompt']
        assert request_data['stream'] is False
        assert request_data['options']['temperature'] == 0.3
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_refine_prompt_empty_response(self, mock_request, ollama_service, mock_response):
        """Test prompt refinement with empty response"""
        mock_response.json.return_value = {'response': ''}
        mock_request.return_value = mock_response
        
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_service.refine_prompt("Test objective")
        
        assert "empty response" in str(exc_info.value)
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_refine_prompt_with_custom_model(self, mock_request, ollama_service, mock_response):
        """Test prompt refinement with custom model"""
        mock_response.json.return_value = {'response': 'Refined prompt text'}
        mock_request.return_value = mock_response
        
        ollama_service.refine_prompt("Test objective", "custom-model")
        
        # Verify custom model was used
        call_args = mock_request.call_args
        request_data = call_args[1]['json']
        assert request_data['model'] == 'custom-model'
    
    @patch('backend.services.ollama_service.requests.Session.request')
    @patch('time.time')
    def test_test_prompt_success(self, mock_time, mock_request, ollama_service, mock_response):
        """Test successful prompt testing"""
        # Mock time for execution time calculation
        mock_time.side_effect = [1000.0, 1002.5]  # 2.5 seconds execution time
        
        mock_generate_response = {
            'response': 'This is a test response from the AI model.'
        }
        mock_response.json.return_value = mock_generate_response
        mock_request.return_value = mock_response
        
        system_prompt = "You are a helpful assistant."
        user_input = "Hello, how are you?"
        
        result = ollama_service.test_prompt(system_prompt, user_input)
        
        assert result['response'] == mock_generate_response['response']
        assert result['execution_time'] == 2.5
        assert result['system_prompt'] == system_prompt
        assert result['user_input'] == user_input
        assert 'model' in result
        assert 'temperature' in result
        
        # Verify the request was made correctly
        call_args = mock_request.call_args
        request_data = call_args[1]['json']
        assert system_prompt in request_data['prompt']
        assert user_input in request_data['prompt']
        assert request_data['stream'] is False
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_test_prompt_empty_response(self, mock_request, ollama_service, mock_response):
        """Test prompt testing with empty response"""
        mock_response.json.return_value = {'response': ''}
        mock_request.return_value = mock_response
        
        with pytest.raises(OllamaConnectionError) as exc_info:
            ollama_service.test_prompt("System prompt", "User input")
        
        assert "empty response" in str(exc_info.value)
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_test_prompt_with_custom_parameters(self, mock_request, ollama_service, mock_response):
        """Test prompt testing with custom model and temperature"""
        mock_response.json.return_value = {'response': 'Test response'}
        mock_request.return_value = mock_response
        
        ollama_service.test_prompt(
            "System prompt", 
            "User input", 
            model="custom-model", 
            temperature=0.9
        )
        
        # Verify custom parameters were used
        call_args = mock_request.call_args
        request_data = call_args[1]['json']
        assert request_data['model'] == 'custom-model'
        assert request_data['options']['temperature'] == 0.9
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_refine_prompt_connection_error(self, mock_request, ollama_service):
        """Test prompt refinement with connection error"""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(OllamaConnectionError):
            ollama_service.refine_prompt("Test objective")
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_test_prompt_timeout_error(self, mock_request, ollama_service):
        """Test prompt testing with timeout error"""
        mock_request.side_effect = requests.exceptions.Timeout("Timeout")
        
        with pytest.raises(OllamaTimeoutError):
            ollama_service.test_prompt("System prompt", "User input")


class TestOllamaServiceIntegration:
    """Integration tests that test the complete workflow"""
    
    @pytest.fixture
    def ollama_service(self):
        """Create OllamaService instance for integration testing"""
        return OllamaService(endpoint="http://localhost:11434", timeout=5, max_retries=1)
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_complete_refinement_workflow(self, mock_request, ollama_service):
        """Test complete prompt refinement workflow"""
        # Mock successful responses for the workflow
        mock_responses = [
            # First call: check connection (health check)
            Mock(status_code=200, json=lambda: {'models': []}),
            # Second call: refine prompt
            Mock(status_code=200, json=lambda: {
                'response': 'You are an expert assistant specialized in helping users with their questions.'
            })
        ]
        
        mock_request.side_effect = mock_responses
        for mock_resp in mock_responses:
            mock_resp.raise_for_status = Mock()
        
        # Test the workflow
        health = ollama_service.health_check()
        assert health is True
        
        refined = ollama_service.refine_prompt("Help users with questions")
        assert "expert assistant" in refined
        assert len(refined) > 20  # Should be a substantial prompt
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_complete_testing_workflow(self, mock_request, ollama_service):
        """Test complete prompt testing workflow"""
        # Mock successful responses
        mock_responses = [
            # Health check
            Mock(status_code=200, json=lambda: {'models': []}),
            # Test prompt
            Mock(status_code=200, json=lambda: {
                'response': 'Hello! I am doing well, thank you for asking. How can I help you today?'
            })
        ]
        
        mock_request.side_effect = mock_responses
        for mock_resp in mock_responses:
            mock_resp.raise_for_status = Mock()
        
        # Test the workflow
        health = ollama_service.health_check()
        assert health is True
        
        with patch('time.time', side_effect=[1000.0, 1001.5]):
            result = ollama_service.test_prompt(
                "You are a helpful assistant.",
                "Hello, how are you?"
            )
        
        assert "Hello!" in result['response']
        assert result['execution_time'] == 1.5
        assert result['system_prompt'] == "You are a helpful assistant."
        assert result['user_input'] == "Hello, how are you?"
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_error_recovery_workflow(self, mock_request, ollama_service):
        """Test error handling and recovery in workflows"""
        # First attempt fails
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        # First call should fail
        health1 = ollama_service.health_check()
        assert health1 is False
        
        # Second attempt succeeds
        mock_success_response = Mock(status_code=200, json=lambda: {'models': []})
        mock_success_response.raise_for_status = Mock()
        mock_request.side_effect = None
        mock_request.return_value = mock_success_response
        
        health2 = ollama_service.health_check()
        assert health2 is True


class TestOllamaServiceCaching:
    """Test caching functionality in OllamaService"""
    
    @pytest.fixture
    def service(self):
        """Create OllamaService instance for testing"""
        return OllamaService(endpoint="http://test:11434", cache_duration=60)
    
    def test_cache_initialization(self, service):
        """Test that cache is properly initialized"""
        assert service._models_cache is None
        assert service._models_cache_time is None
        assert not service._is_cache_valid()
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_get_models_with_caching(self, mock_request, service):
        """Test model retrieval with caching"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama2', 'size': 1000000, 'modified_at': '2023-01-01', 'digest': 'abc123'}
            ]
        }
        mock_request.return_value = mock_response
        
        # First call should make HTTP request
        models1 = service.get_available_models()
        assert len(models1) == 1
        assert models1[0]['name'] == 'llama2'
        assert models1[0]['size_mb'] == 1.0
        assert mock_request.call_count == 1
        
        # Second call should use cache
        models2 = service.get_available_models()
        assert models2 == models1
        assert mock_request.call_count == 1  # No additional HTTP request
        
        # Cache should be valid
        assert service._is_cache_valid()
        cache_info = service.get_cache_info()
        assert cache_info['cached'] is True
        assert cache_info['cache_valid'] is True
        assert cache_info['models_count'] == 1
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_get_models_bypass_cache(self, mock_request, service):
        """Test model retrieval bypassing cache"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama2', 'size': 1000000, 'modified_at': '2023-01-01', 'digest': 'abc123'}
            ]
        }
        mock_request.return_value = mock_response
        
        # First call with cache
        models1 = service.get_available_models(use_cache=True)
        assert mock_request.call_count == 1
        
        # Second call bypassing cache
        models2 = service.get_available_models(use_cache=False)
        assert mock_request.call_count == 2  # Additional HTTP request made
        assert models2 == models1
    
    @patch('backend.services.ollama_service.requests.Session.request')
    def test_refresh_models_cache(self, mock_request, service):
        """Test force refresh of models cache"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [
                {'name': 'codellama', 'size': 2000000, 'modified_at': '2023-01-02', 'digest': 'def456'}
            ]
        }
        mock_request.return_value = mock_response
        
        # Populate cache first
        service.get_available_models()
        assert mock_request.call_count == 1
        
        # Refresh cache
        models = service.refresh_models_cache()
        assert len(models) == 1
        assert models[0]['name'] == 'codellama'
        assert mock_request.call_count == 2  # Additional request made
    
    def test_clear_models_cache(self, service):
        """Test clearing models cache"""
        # Simulate cached data
        service._models_cache = [{'name': 'test'}]
        service._models_cache_time = datetime.now()
        
        assert service._is_cache_valid()
        
        # Clear cache
        service.clear_models_cache()
        
        assert service._models_cache is None
        assert service._models_cache_time is None
        assert not service._is_cache_valid()
    
    def test_cache_expiry(self, service):
        """Test cache expiry functionality"""
        from datetime import timedelta
        
        # Set cache with expired time
        service._models_cache = [{'name': 'test'}]
        service._models_cache_time = datetime.now() - timedelta(seconds=service.cache_duration + 1)
        
        assert not service._is_cache_valid()
        
        cache_info = service.get_cache_info()
        assert cache_info['cached'] is True
        assert cache_info['cache_valid'] is False
        assert cache_info['cache_age_seconds'] > service.cache_duration
    
    def test_get_cache_info_empty(self, service):
        """Test cache info when cache is empty"""
        cache_info = service.get_cache_info()
        
        assert cache_info['cached'] is False
        assert cache_info['cache_time'] is None
        assert cache_info['cache_age_seconds'] is None
        assert cache_info['cache_valid'] is False
        assert cache_info['models_count'] == 0
    
    def test_get_cache_info_populated(self, service):
        """Test cache info when cache is populated"""
        # Simulate cached data
        service._models_cache = [{'name': 'test1'}, {'name': 'test2'}]
        service._models_cache_time = datetime.now()
        
        cache_info = service.get_cache_info()
        
        assert cache_info['cached'] is True
        assert cache_info['cache_time'] is not None
        assert cache_info['cache_age_seconds'] >= 0
        assert cache_info['cache_valid'] is True
        assert cache_info['models_count'] == 2
        assert cache_info['cache_duration_seconds'] == service.cache_duration