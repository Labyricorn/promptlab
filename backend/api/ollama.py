"""
PromptLab Ollama API Endpoints
Endpoints for AI model interaction, prompt refinement, and testing
"""

from flask import Blueprint, request, jsonify
import yaml
from backend.services.ollama_service import ollama_service, OllamaConnectionError, OllamaTimeoutError

# Create Blueprint for Ollama API endpoints
ollama_bp = Blueprint('ollama', __name__, url_prefix='/api')

def handle_ollama_error(error):
    """Handle Ollama service errors and return appropriate response"""
    if isinstance(error, OllamaTimeoutError):
        return jsonify({
            'error': True,
            'message': 'Request to Ollama timed out. Please check your connection and try again.',
            'code': 'OLLAMA_TIMEOUT'
        }), 408
    elif isinstance(error, OllamaConnectionError):
        return jsonify({
            'error': True,
            'message': str(error),
            'code': 'OLLAMA_CONNECTION_ERROR'
        }), 503
    else:
        return jsonify({
            'error': True,
            'message': 'Unexpected error communicating with Ollama',
            'code': 'OLLAMA_ERROR'
        }), 500

@ollama_bp.route('/refine-prompt', methods=['POST'])
def refine_prompt():
    """
    Refine a simple objective into a detailed system prompt using AI
    
    Request Body:
        objective (str): Simple objective or goal for the prompt
        target_model (str, optional): Model to use for refinement
    
    Returns:
        JSON response with refined system prompt
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
        
        # Validate required fields
        objective = data.get('objective', '').strip()
        if not objective:
            return jsonify({
                'error': True,
                'message': 'Objective is required',
                'code': 'VALIDATION_ERROR',
                'details': {'objective': 'Objective cannot be empty'}
            }), 400
        
        if len(objective) > 5000:
            return jsonify({
                'error': True,
                'message': 'Objective is too long',
                'code': 'VALIDATION_ERROR',
                'details': {'objective': 'Objective cannot exceed 5,000 characters'}
            }), 400
        
        target_model = data.get('target_model', '').strip() or None
        
        # Call Ollama service to refine the prompt
        refined_prompt = ollama_service.refine_prompt(objective, target_model)
        
        return jsonify({
            'success': True,
            'message': 'Prompt refined successfully',
            'objective': objective,
            'refined_prompt': refined_prompt,
            'model_used': target_model or ollama_service.endpoint
        })
        
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        return handle_ollama_error(e)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to refine prompt',
            'code': 'REFINEMENT_ERROR'
        }), 500

@ollama_bp.route('/run-test', methods=['POST'])
def run_test():
    """
    Test a system prompt with user input using specified model and parameters
    
    Request Body:
        system_prompt (str): The system prompt to test
        user_input (str): User message to send with the system prompt
        model (str, optional): Model to use for testing
        temperature (float, optional): Temperature setting (0.0-2.0)
    
    Returns:
        JSON response with AI response and YAML configuration
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
        
        # Validate required fields
        errors = {}
        
        system_prompt = data.get('system_prompt', '').strip()
        if not system_prompt:
            errors['system_prompt'] = 'System prompt is required'
        elif len(system_prompt) > 50000:
            errors['system_prompt'] = 'System prompt cannot exceed 50,000 characters'
        
        user_input = data.get('user_input', '').strip()
        if not user_input:
            errors['user_input'] = 'User input is required'
        elif len(user_input) > 10000:
            errors['user_input'] = 'User input cannot exceed 10,000 characters'
        
        # Validate optional fields
        model = data.get('model', '').strip() or None
        if model and len(model) > 100:
            errors['model'] = 'Model name cannot exceed 100 characters'
        
        temperature = data.get('temperature')
        if temperature is not None:
            try:
                temperature = float(temperature)
                if temperature < 0.0 or temperature > 2.0:
                    errors['temperature'] = 'Temperature must be between 0.0 and 2.0'
            except (ValueError, TypeError):
                errors['temperature'] = 'Temperature must be a valid number'
        
        if errors:
            return jsonify({
                'error': True,
                'message': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': errors
            }), 400
        
        # Call Ollama service to test the prompt
        test_result = ollama_service.test_prompt(system_prompt, user_input, model, temperature)
        
        # Generate YAML configuration
        yaml_config = {
            'prompt_configuration': {
                'system_prompt': system_prompt,
                'model': test_result['model'],
                'temperature': test_result['temperature'],
                'test_input': user_input,
                'test_output': test_result['response'],
                'execution_time_seconds': test_result['execution_time']
            }
        }
        
        yaml_string = yaml.dump(yaml_config, default_flow_style=False, sort_keys=False)
        
        return jsonify({
            'success': True,
            'message': 'Prompt test completed successfully',
            'response': test_result['response'],
            'execution_time': test_result['execution_time'],
            'model': test_result['model'],
            'temperature': test_result['temperature'],
            'yaml_config': yaml_string
        })
        
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        return handle_ollama_error(e)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to run prompt test',
            'code': 'TEST_ERROR'
        }), 500

@ollama_bp.route('/models', methods=['GET'])
def get_models():
    """
    Get list of available models from Ollama with caching support
    
    Query Parameters:
        refresh (bool): Force refresh of model cache (default: false)
        cache_info (bool): Include cache information in response (default: false)
    
    Returns:
        JSON response with list of available models
    """
    try:
        # Get query parameters
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        include_cache_info = request.args.get('cache_info', 'false').lower() == 'true'
        
        # Get models (with or without cache)
        if force_refresh:
            models = ollama_service.refresh_models_cache()
        else:
            models = ollama_service.get_available_models()
        
        response_data = {
            'success': True,
            'message': 'Models retrieved successfully',
            'models': models,
            'count': len(models)
        }
        
        # Include cache information if requested
        if include_cache_info:
            response_data['cache_info'] = ollama_service.get_cache_info()
        
        return jsonify(response_data)
        
    except (OllamaConnectionError, OllamaTimeoutError) as e:
        return handle_ollama_error(e)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve models',
            'code': 'MODEL_RETRIEVAL_ERROR'
        }), 500

@ollama_bp.route('/models/cache', methods=['DELETE'])
def clear_models_cache():
    """
    Clear the models cache
    
    Returns:
        JSON response confirming cache clearance
    """
    try:
        ollama_service.clear_models_cache()
        
        return jsonify({
            'success': True,
            'message': 'Models cache cleared successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to clear models cache',
            'code': 'CACHE_CLEAR_ERROR'
        }), 500

@ollama_bp.route('/models/cache', methods=['GET'])
def get_cache_info():
    """
    Get information about the models cache
    
    Returns:
        JSON response with cache information
    """
    try:
        cache_info = ollama_service.get_cache_info()
        
        return jsonify({
            'success': True,
            'message': 'Cache information retrieved successfully',
            'cache_info': cache_info
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve cache information',
            'code': 'CACHE_INFO_ERROR'
        }), 500

@ollama_bp.route('/ollama/health', methods=['GET'])
def ollama_health():
    """
    Check Ollama connection health
    
    Returns:
        JSON response with connection status
    """
    try:
        connection_status = ollama_service.check_connection()
        
        if connection_status['connected']:
            return jsonify({
                'success': True,
                'message': connection_status['message'],
                'status': connection_status
            })
        else:
            return jsonify({
                'error': True,
                'message': connection_status['message'],
                'status': connection_status
            }), 503
            
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to check Ollama health',
            'code': 'HEALTH_CHECK_ERROR'
        }), 500