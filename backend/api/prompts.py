"""
PromptLab Prompt API Endpoints
CRUD operations for prompt management with search functionality
"""

import json
from datetime import datetime, timezone
try:
    import yaml
except ImportError:
    yaml = None
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from backend.database import get_db_session, close_db_session
from backend.models.prompt import Prompt

# Create Blueprint for prompt API endpoints
prompts_bp = Blueprint('prompts', __name__, url_prefix='/api')

def handle_database_error(error):
    """Handle database errors and return appropriate response"""
    if isinstance(error, IntegrityError):
        if 'UNIQUE constraint failed' in str(error):
            return jsonify({
                'error': True,
                'message': 'A prompt with this name already exists',
                'code': 'DUPLICATE_NAME'
            }), 409
        else:
            return jsonify({
                'error': True,
                'message': 'Database constraint violation',
                'code': 'CONSTRAINT_ERROR'
            }), 400
    else:
        return jsonify({
            'error': True,
            'message': 'Database operation failed',
            'code': 'DATABASE_ERROR'
        }), 500

def validate_prompt_data(data, required_fields=None):
    """Validate prompt data and return errors if any"""
    if required_fields is None:
        required_fields = ['name', 'system_prompt']
    
    errors = {}
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f'{field.replace("_", " ").title()} is required'
    
    # Validate specific fields if present
    if 'name' in data and data['name']:
        name = data['name'].strip()
        if len(name) > 255:
            errors['name'] = 'Name cannot exceed 255 characters'
        elif not name:
            errors['name'] = 'Name cannot be empty'
    
    if 'system_prompt' in data and data['system_prompt']:
        system_prompt = data['system_prompt'].strip()
        if len(system_prompt) > 50000:
            errors['system_prompt'] = 'System prompt cannot exceed 50,000 characters'
        elif not system_prompt:
            errors['system_prompt'] = 'System prompt cannot be empty'
    
    if 'model' in data and data['model']:
        model = data['model'].strip()
        if len(model) > 100:
            errors['model'] = 'Model name cannot exceed 100 characters'
        elif not model:
            errors['model'] = 'Model name cannot be empty'
    
    if 'temperature' in data and data['temperature'] is not None:
        try:
            temp = float(data['temperature'])
            if temp < 0.0 or temp > 2.0:
                errors['temperature'] = 'Temperature must be between 0.0 and 2.0'
        except (ValueError, TypeError):
            errors['temperature'] = 'Temperature must be a valid number'
    
    if 'description' in data and data['description']:
        description = data['description'].strip()
        if len(description) > 1000:
            errors['description'] = 'Description cannot exceed 1,000 characters'
    
    return errors

@prompts_bp.route('/prompts', methods=['GET'])
def get_prompts():
    """
    Get all prompts with optional search functionality
    
    Query Parameters:
        search (str): Search term to filter prompts by name and description
    
    Returns:
        JSON response with list of prompts
    """
    session = None
    try:
        session = get_db_session()
        
        # Get search parameter
        search_term = request.args.get('search', '').strip()
        
        # Build query
        query = session.query(Prompt)
        
        # Apply search filter if provided
        if search_term:
            # Case-insensitive search across name and description
            search_filter = f"%{search_term}%"
            query = query.filter(
                (Prompt.name.ilike(search_filter)) |
                (Prompt.description.ilike(search_filter))
            )
        
        # Order by name for consistent results
        prompts = query.order_by(Prompt.name).all()
        
        # Convert to dictionaries
        prompt_list = [prompt.to_dict() for prompt in prompts]
        
        return jsonify({
            'success': True,
            'prompts': prompt_list,
            'count': len(prompt_list)
        })
        
    except SQLAlchemyError as e:
        return handle_database_error(e)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to retrieve prompts',
            'code': 'RETRIEVAL_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

@prompts_bp.route('/prompts', methods=['POST'])
def create_prompt():
    """
    Create a new prompt
    
    Request Body:
        name (str): Unique name for the prompt
        system_prompt (str): The system prompt text
        model (str, optional): AI model name (default: llama2)
        temperature (float, optional): Temperature setting (default: 0.7)
        description (str, optional): Optional description
    
    Returns:
        JSON response with created prompt data
    """
    session = None
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
        validation_errors = validate_prompt_data(data)
        if validation_errors:
            return jsonify({
                'error': True,
                'message': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        session = get_db_session()
        
        # Create new prompt instance
        prompt = Prompt(
            name=data['name'].strip(),
            system_prompt=data['system_prompt'].strip(),
            model=data.get('model', 'llama2').strip(),
            temperature=float(data.get('temperature', 0.7)),
            description=data.get('description', '').strip() or None
        )
        
        # Add to session and commit
        session.add(prompt)
        session.commit()
        
        # Refresh to get generated ID and timestamps
        session.refresh(prompt)
        
        return jsonify({
            'success': True,
            'message': 'Prompt created successfully',
            'prompt': prompt.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'error': True,
            'message': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        return handle_database_error(e)
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({
            'error': True,
            'message': 'Failed to create prompt',
            'code': 'CREATION_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

@prompts_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
def update_prompt(prompt_id):
    """
    Update an existing prompt
    
    Path Parameters:
        prompt_id (int): ID of the prompt to update
    
    Request Body:
        name (str, optional): Updated name for the prompt
        system_prompt (str, optional): Updated system prompt text
        model (str, optional): Updated AI model name
        temperature (float, optional): Updated temperature setting
        description (str, optional): Updated description
    
    Returns:
        JSON response with updated prompt data
    """
    session = None
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
        
        # Validate data (no required fields for updates)
        validation_errors = validate_prompt_data(data, required_fields=[])
        if validation_errors:
            return jsonify({
                'error': True,
                'message': 'Validation failed',
                'code': 'VALIDATION_ERROR',
                'details': validation_errors
            }), 400
        
        session = get_db_session()
        
        # Find existing prompt
        prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return jsonify({
                'error': True,
                'message': 'Prompt not found',
                'code': 'NOT_FOUND'
            }), 404
        
        # Update fields
        prompt.update_from_dict(data)
        
        # Commit changes
        session.commit()
        
        # Refresh to get updated timestamps
        session.refresh(prompt)
        
        return jsonify({
            'success': True,
            'message': 'Prompt updated successfully',
            'prompt': prompt.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            'error': True,
            'message': str(e),
            'code': 'VALIDATION_ERROR'
        }), 400
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        return handle_database_error(e)
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({
            'error': True,
            'message': 'Failed to update prompt',
            'code': 'UPDATE_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

@prompts_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
def delete_prompt(prompt_id):
    """
    Delete a prompt
    
    Path Parameters:
        prompt_id (int): ID of the prompt to delete
    
    Returns:
        JSON response confirming deletion
    """
    session = None
    try:
        session = get_db_session()
        
        # Find existing prompt
        prompt = session.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            return jsonify({
                'error': True,
                'message': 'Prompt not found',
                'code': 'NOT_FOUND'
            }), 404
        
        # Store prompt data for response
        prompt_data = prompt.to_dict()
        
        # Delete prompt
        session.delete(prompt)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Prompt deleted successfully',
            'deleted_prompt': prompt_data
        })
        
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        return handle_database_error(e)
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({
            'error': True,
            'message': 'Failed to delete prompt',
            'code': 'DELETION_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

@prompts_bp.route('/export-library', methods=['POST'])
def export_library():
    """
    Export all prompts to JSON/YAML format with metadata
    
    Request Body:
        format (str, optional): Export format - 'json' or 'yaml' (default: 'json')
    
    Returns:
        JSON response with exported library data
    """
    session = None
    try:
        # Get request data - handle empty request body
        try:
            data = request.get_json() or {}
        except Exception:
            data = {}
        export_format = data.get('format', 'json').lower()
        
        # Validate format
        if export_format not in ['json', 'yaml']:
            return jsonify({
                'error': True,
                'message': 'Invalid export format. Must be "json" or "yaml"',
                'code': 'INVALID_FORMAT'
            }), 400
        
        session = get_db_session()
        
        # Get all prompts
        prompts = session.query(Prompt).order_by(Prompt.name).all()
        
        # Create export data structure
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_prompts': len(prompts),
                'format_version': '1.0',
                'exported_by': 'PromptLab'
            },
            'prompts': [prompt.to_dict() for prompt in prompts]
        }
        
        # Convert to requested format
        if export_format == 'yaml':
            if yaml is None:
                return jsonify({
                    'error': True,
                    'message': 'YAML support not available',
                    'code': 'YAML_NOT_AVAILABLE'
                }), 500
            try:
                formatted_data = yaml.dump(export_data, default_flow_style=False, sort_keys=False)
                content_type = 'application/x-yaml'
            except Exception as e:
                return jsonify({
                    'error': True,
                    'message': f'Failed to convert data to YAML format: {str(e)}',
                    'code': 'YAML_CONVERSION_ERROR'
                }), 500
        else:
            try:
                formatted_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                content_type = 'application/json'
            except Exception as e:
                return jsonify({
                    'error': True,
                    'message': f'Failed to convert data to JSON format: {str(e)}',
                    'code': 'JSON_CONVERSION_ERROR'
                }), 500
        
        return jsonify({
            'success': True,
            'message': f'Library exported successfully in {export_format.upper()} format',
            'export_data': formatted_data,
            'metadata': export_data['metadata'],
            'content_type': content_type
        })
        
    except SQLAlchemyError as e:
        return handle_database_error(e)
    except Exception as e:
        return jsonify({
            'error': True,
            'message': 'Failed to export library',
            'code': 'EXPORT_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

@prompts_bp.route('/import-library', methods=['POST'])
def import_library():
    """
    Import prompts from JSON/YAML format with conflict detection and resolution
    
    Request Body:
        import_data (str): The exported library data (JSON or YAML string)
        conflict_resolution (str, optional): How to handle conflicts - 'skip', 'overwrite', or 'rename' (default: 'skip')
        format (str, optional): Data format - 'json' or 'yaml' (auto-detected if not provided)
    
    Returns:
        JSON response with import results and conflict information
    """
    session = None
    try:
        # Get request data
        data = request.get_json(force=True)
        if not data:
            return jsonify({
                'error': True,
                'message': 'Request body must contain JSON data',
                'code': 'INVALID_JSON'
            }), 400
        
        import_data_str = data.get('import_data')
        if not import_data_str:
            return jsonify({
                'error': True,
                'message': 'import_data field is required',
                'code': 'MISSING_IMPORT_DATA'
            }), 400
        
        conflict_resolution = data.get('conflict_resolution', 'skip').lower()
        data_format = data.get('format', '').lower()
        
        # Validate conflict resolution strategy
        if conflict_resolution not in ['skip', 'overwrite', 'rename']:
            return jsonify({
                'error': True,
                'message': 'Invalid conflict_resolution. Must be "skip", "overwrite", or "rename"',
                'code': 'INVALID_CONFLICT_RESOLUTION'
            }), 400
        
        # Parse import data
        try:
            # Auto-detect format if not provided
            if not data_format:
                import_data_str_stripped = import_data_str.strip()
                if import_data_str_stripped.startswith('{') or import_data_str_stripped.startswith('['):
                    data_format = 'json'
                else:
                    data_format = 'yaml'
            
            if data_format == 'yaml':
                if yaml is None:
                    return jsonify({
                        'error': True,
                        'message': 'YAML support not available',
                        'code': 'YAML_NOT_AVAILABLE'
                    }), 500
                import_data = yaml.safe_load(import_data_str)
            else:
                import_data = json.loads(import_data_str)
                
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            return jsonify({
                'error': True,
                'message': f'Failed to parse {data_format.upper()} data: {str(e)}',
                'code': 'PARSE_ERROR'
            }), 400
        except Exception as e:
            return jsonify({
                'error': True,
                'message': f'Failed to parse {data_format.upper()} data: {str(e)}',
                'code': 'PARSE_ERROR'
            }), 400
        
        # Validate import data structure
        if not isinstance(import_data, dict):
            return jsonify({
                'error': True,
                'message': 'Import data must be a JSON object',
                'code': 'INVALID_STRUCTURE'
            }), 400
        
        if 'prompts' not in import_data:
            return jsonify({
                'error': True,
                'message': 'Import data must contain a "prompts" field',
                'code': 'MISSING_PROMPTS_FIELD'
            }), 400
        
        if not isinstance(import_data['prompts'], list):
            return jsonify({
                'error': True,
                'message': 'Prompts field must be an array',
                'code': 'INVALID_PROMPTS_STRUCTURE'
            }), 400
        
        session = get_db_session()
        
        # Get existing prompt names for conflict detection
        existing_prompts = {prompt.name.lower(): prompt for prompt in session.query(Prompt).all()}
        
        # Process import results
        results = {
            'imported': [],
            'skipped': [],
            'overwritten': [],
            'renamed': [],
            'errors': []
        }
        
        for prompt_data in import_data['prompts']:
            try:
                # Validate prompt data structure
                validation_errors = validate_imported_prompt_data(prompt_data)
                if validation_errors:
                    results['errors'].append({
                        'name': prompt_data.get('name', 'Unknown'),
                        'errors': validation_errors
                    })
                    continue
                
                original_name = prompt_data['name']
                name_lower = original_name.lower()
                
                # Check for conflicts
                if name_lower in existing_prompts:
                    if conflict_resolution == 'skip':
                        results['skipped'].append({
                            'name': original_name,
                            'reason': 'Name already exists'
                        })
                        continue
                    elif conflict_resolution == 'overwrite':
                        # Update existing prompt
                        existing_prompt = existing_prompts[name_lower]
                        existing_prompt.update_from_dict({
                            'description': prompt_data.get('description'),
                            'system_prompt': prompt_data['system_prompt'],
                            'model': prompt_data.get('model', 'llama2'),
                            'temperature': prompt_data.get('temperature', 0.7)
                        })
                        results['overwritten'].append({
                            'name': original_name,
                            'id': existing_prompt.id
                        })
                        continue
                    elif conflict_resolution == 'rename':
                        # Generate unique name
                        new_name = generate_unique_name(original_name, existing_prompts)
                        prompt_data['name'] = new_name
                        results['renamed'].append({
                            'original_name': original_name,
                            'new_name': new_name
                        })
                
                # Create new prompt
                prompt = Prompt(
                    name=prompt_data['name'],
                    system_prompt=prompt_data['system_prompt'],
                    model=prompt_data.get('model', 'llama2'),
                    temperature=prompt_data.get('temperature', 0.7),
                    description=prompt_data.get('description')
                )
                
                session.add(prompt)
                session.flush()  # Get ID without committing
                
                # Add to existing prompts for future conflict detection
                existing_prompts[prompt.name.lower()] = prompt
                
                results['imported'].append({
                    'name': prompt.name,
                    'id': prompt.id
                })
                
            except Exception as e:
                results['errors'].append({
                    'name': prompt_data.get('name', 'Unknown'),
                    'errors': [str(e)]
                })
        
        # Commit all changes
        session.commit()
        
        # Prepare response
        total_processed = len(results['imported']) + len(results['skipped']) + len(results['overwritten']) + len(results['renamed']) + len(results['errors'])
        
        return jsonify({
            'success': True,
            'message': f'Import completed. Processed {total_processed} prompts.',
            'results': results,
            'summary': {
                'total_processed': total_processed,
                'imported': len(results['imported']),
                'skipped': len(results['skipped']),
                'overwritten': len(results['overwritten']),
                'renamed': len(results['renamed']),
                'errors': len(results['errors'])
            }
        })
        
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        return handle_database_error(e)
    except Exception as e:
        if session:
            session.rollback()
        return jsonify({
            'error': True,
            'message': 'Failed to import library',
            'code': 'IMPORT_ERROR'
        }), 500
    finally:
        if session:
            close_db_session(session)

def validate_imported_prompt_data(prompt_data):
    """
    Validate imported prompt data structure and content
    
    Args:
        prompt_data (dict): Prompt data from import
    
    Returns:
        list: List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    required_fields = ['name', 'system_prompt']
    for field in required_fields:
        if field not in prompt_data or not prompt_data[field]:
            errors.append(f'{field.replace("_", " ").title()} is required')
    
    # Validate field types and constraints
    if 'name' in prompt_data:
        name = prompt_data['name']
        if not isinstance(name, str):
            errors.append('Name must be a string')
        elif len(name.strip()) > 255:
            errors.append('Name cannot exceed 255 characters')
        elif not name.strip():
            errors.append('Name cannot be empty')
    
    if 'system_prompt' in prompt_data:
        system_prompt = prompt_data['system_prompt']
        if not isinstance(system_prompt, str):
            errors.append('System prompt must be a string')
        elif len(system_prompt.strip()) > 50000:
            errors.append('System prompt cannot exceed 50,000 characters')
        elif not system_prompt.strip():
            errors.append('System prompt cannot be empty')
    
    if 'model' in prompt_data and prompt_data['model'] is not None:
        model = prompt_data['model']
        if not isinstance(model, str):
            errors.append('Model must be a string')
        elif len(model.strip()) > 100:
            errors.append('Model name cannot exceed 100 characters')
        elif not model.strip():
            errors.append('Model name cannot be empty')
    
    if 'temperature' in prompt_data and prompt_data['temperature'] is not None:
        temperature = prompt_data['temperature']
        try:
            temp = float(temperature)
            if temp < 0.0 or temp > 2.0:
                errors.append('Temperature must be between 0.0 and 2.0')
        except (ValueError, TypeError):
            errors.append('Temperature must be a valid number')
    
    if 'description' in prompt_data and prompt_data['description'] is not None:
        description = prompt_data['description']
        if not isinstance(description, str):
            errors.append('Description must be a string')
        elif len(description.strip()) > 1000:
            errors.append('Description cannot exceed 1,000 characters')
    
    return errors

def generate_unique_name(original_name, existing_prompts):
    """
    Generate a unique name by appending a number suffix
    
    Args:
        original_name (str): The original prompt name
        existing_prompts (dict): Dictionary of existing prompt names (lowercase keys)
    
    Returns:
        str: A unique name
    """
    base_name = original_name
    counter = 1
    
    while True:
        candidate_name = f"{base_name} ({counter})"
        if candidate_name.lower() not in existing_prompts:
            return candidate_name
        counter += 1