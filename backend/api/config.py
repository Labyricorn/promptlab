"""
PromptLab Configuration API Endpoints
Configuration management and system settings
"""

from flask import Blueprint, request, jsonify
from backend.config import config, AppConfig
from backend.services.ollama_service import OllamaService
import os
import json
from pathlib import Path

# Create Blueprint for configuration API endpoints
config_bp = Blueprint('config', __name__, url_prefix='/api')

def validate_config_update(data):
    """Validate configuration update data"""
    errors = {}
    
    # Create a temporary config to validate
    try:
        temp_config = AppConfig.from_dict(data)
        validation_errors = temp_config.validate()
        if validation_errors:
            errors.update(validation_errors)
    except Exception as e:
        errors['general'] = f"Invalid configuration data: {str(e)}"
    
    return errors

@config_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get current application configuration
    
    Returns:
        JSON response with current configuration settings
    """
    try:
        # Get current configuration
        config_data = config.to_dict()
        
        # Test Ollama connection status
        ollama_service = OllamaService()
        connection_status = ollama_service.check_connection()
        
        return jsonify({
            'success': True,
            'config': config_data,
            'ollama_status': {
                'connected': connection_status,
                'endpoint': config.ollama_endpoint
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve configuration',
            'code': 'CONFIG_RETRIEVAL_ERROR'
        }), 500

@config_bp.route('/config', methods=['PUT'])
def update_config():
    """
    Update application configuration
    
    Request Body:
        ollama_endpoint (str, optional): Ollama API endpoint URL
        default_model (str, optional): Default AI model name
        default_temperature (float, optional): Default temperature setting
        database_path (str, optional): Database file path
        flask_host (str, optional): Flask server host
        flask_port (int, optional): Flask server port
        flask_debug (bool, optional): Flask debug mode
    
    Returns:
        JSON response with updated configuration
    """
    try:
        # Get JSON data with error handling
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({
                'error': True,
                'message': 'Request body must contain valid JSON data',
                'code': 'INVALID_JSON'
            }), 400
            
        if not data:
            return jsonify({
                'error': True,
                'message': 'Request body must contain JSON data',
                'code': 'INVALID_JSON'
            }), 400
        
        # Validate configuration data
        validation_errors = validate_config_update(data)
        if validation_errors:
            return jsonify({
                'error': True,
                'message': 'Configuration validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        # Update global configuration
        global config
        current_config_dict = config.to_dict()
        current_config_dict.update(data)
        config = AppConfig.from_dict(current_config_dict)
        
        # Test new Ollama connection if endpoint was updated
        connection_status = False
        if 'ollama_endpoint' in data:
            ollama_service = OllamaService()
            connection_status = ollama_service.check_connection()
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully',
            'config': config.to_dict(),
            'ollama_status': {
                'connected': connection_status,
                'endpoint': config.ollama_endpoint
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to update configuration',
            'code': 'CONFIG_UPDATE_ERROR'
        }), 500

@config_bp.route('/config/test-connection', methods=['POST'])
def test_ollama_connection():
    """
    Test connection to Ollama endpoint
    
    Request Body:
        endpoint (str, optional): Ollama endpoint to test (defaults to current config)
    
    Returns:
        JSON response with connection test results
    """
    try:
        # Get JSON data
        data = request.get_json() or {}
        
        # Use provided endpoint or current config
        endpoint = data.get('endpoint', config.ollama_endpoint)
        
        # Validate endpoint format
        if not endpoint or not isinstance(endpoint, str):
            return jsonify({
                'error': True,
                'message': 'Endpoint must be a valid URL string',
                'code': 'INVALID_ENDPOINT'
            }), 400
        
        if not endpoint.startswith(('http://', 'https://')):
            return jsonify({
                'error': True,
                'message': 'Endpoint must start with http:// or https://',
                'code': 'INVALID_ENDPOINT'
            }), 400
        
        # Test connection
        ollama_service = OllamaService(endpoint=endpoint)
        connection_status = ollama_service.check_connection()
        
        response_data = {
            'success': True,
            'connected': connection_status,
            'endpoint': endpoint
        }
        
        # If connected, try to get models
        if connection_status:
            try:
                models = ollama_service.get_available_models()
                response_data['models_available'] = len(models)
                response_data['models'] = models[:5]  # First 5 models for preview
            except Exception:
                response_data['models_available'] = 0
                response_data['models'] = []
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Connection test failed',
            'code': 'CONNECTION_TEST_ERROR',
            'details': str(e)
        }), 500

@config_bp.route('/config/save', methods=['POST'])
def save_config_to_file():
    """
    Save current configuration to file
    
    Request Body:
        path (str, optional): File path to save configuration (defaults to config.json)
        format (str, optional): File format - 'json' or 'yaml' (defaults to 'json')
    
    Returns:
        JSON response confirming configuration save
    """
    try:
        # Get JSON data
        data = request.get_json() or {}
        
        # Get file path and format
        config_path = data.get('path', 'config.json')
        file_format = data.get('format', 'json').lower()
        
        if file_format not in ['json', 'yaml']:
            return jsonify({
                'error': True,
                'message': 'Format must be either "json" or "yaml"',
                'code': 'INVALID_FORMAT'
            }), 400
        
        # Prepare configuration data
        config_data = config.to_dict()
        
        # Create directory if it doesn't exist
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration file
        with open(config_file, 'w', encoding='utf-8') as f:
            if file_format == 'yaml':
                import yaml
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully',
            'path': str(config_file.absolute()),
            'format': file_format
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to save configuration',
            'code': 'CONFIG_SAVE_ERROR',
            'details': str(e)
        }), 500

@config_bp.route('/config/load', methods=['POST'])
def load_config_from_file():
    """
    Load configuration from file
    
    Request Body:
        path (str): File path to load configuration from
    
    Returns:
        JSON response with loaded configuration
    """
    try:
        # Get JSON data
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({
                'error': True,
                'message': 'Request body must contain valid JSON data',
                'code': 'INVALID_JSON'
            }), 400
        
        if not data or 'path' not in data:
            return jsonify({
                'error': True,
                'message': 'File path is required',
                'code': 'MISSING_PATH'
            }), 400
        
        config_path = data['path']
        
        # Load configuration from file
        try:
            new_config = AppConfig.from_file(config_path)
        except FileNotFoundError:
            return jsonify({
                'error': True,
                'message': f'Configuration file not found: {config_path}',
                'code': 'FILE_NOT_FOUND'
            }), 404
        except ValueError as e:
            return jsonify({
                'error': True,
                'message': str(e),
                'code': 'INVALID_CONFIG_FILE'
            }), 400
        
        # Validate loaded configuration
        validation_errors = new_config.validate()
        if validation_errors:
            return jsonify({
                'error': True,
                'message': 'Loaded configuration is invalid',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        # Update global configuration
        global config
        config = new_config
        
        # Test Ollama connection with new config
        ollama_service = OllamaService()
        connection_status = ollama_service.check_connection()
        
        return jsonify({
            'success': True,
            'message': 'Configuration loaded successfully',
            'config': config.to_dict(),
            'ollama_status': {
                'connected': connection_status,
                'endpoint': config.ollama_endpoint
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to load configuration',
            'code': 'CONFIG_LOAD_ERROR',
            'details': str(e)
        }), 500

@config_bp.route('/config/models', methods=['GET'])
def get_models_with_config():
    """
    Get available models integrated with configuration system
    
    Query Parameters:
        refresh (bool): Force refresh of model cache (default: false)
        include_default (bool): Include default model information (default: true)
    
    Returns:
        JSON response with models and configuration context
    """
    try:
        # Get query parameters
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        include_default = request.args.get('include_default', 'true').lower() == 'true'
        
        # Get models from Ollama service
        ollama_service = OllamaService()
        
        if force_refresh:
            models = ollama_service.refresh_models_cache()
        else:
            models = ollama_service.get_available_models()
        
        response_data = {
            'success': True,
            'message': 'Models retrieved successfully',
            'models': models,
            'count': len(models),
            'cache_info': ollama_service.get_cache_info()
        }
        
        # Include default model information if requested
        if include_default:
            default_model = config.default_model
            default_model_available = any(model['name'] == default_model for model in models)
            
            response_data['default_model'] = {
                'name': default_model,
                'available': default_model_available,
                'temperature': config.default_temperature
            }
            
            # If default model is not available, suggest alternatives
            if not default_model_available and models:
                response_data['suggested_models'] = models[:3]  # First 3 available models
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve models with configuration',
            'code': 'MODELS_CONFIG_ERROR',
            'details': str(e)
        }), 500