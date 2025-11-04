"""
Integration tests for PromptLab Prompt API endpoints
Tests for CRUD operations, search functionality, and error handling
"""

import pytest
import json
from flask import Flask
from backend.app import create_app
from backend.database import Base, get_db_session, close_db_session
from backend.models.prompt import Prompt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

@pytest.fixture(scope="function")
def test_app():
    """Create a test Flask application with temporary database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Override database path for testing
    import backend.config
    original_db_path = backend.config.config.database_path
    backend.config.config.database_path = db_path
    
    # Create test app
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Cleanup
    backend.config.config.database_path = original_db_path
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        pass

@pytest.fixture
def client(test_app):
    """Create a test client"""
    return test_app.test_client()

@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing"""
    return {
        'name': 'Test Prompt',
        'description': 'A test prompt for API testing',
        'system_prompt': 'You are a helpful assistant for testing purposes.',
        'model': 'llama2',
        'temperature': 0.7
    }

@pytest.fixture
def create_test_prompt(client, sample_prompt_data):
    """Create a test prompt via API and return its data"""
    response = client.post('/api/prompts', 
                          data=json.dumps(sample_prompt_data),
                          content_type='application/json')
    assert response.status_code == 201
    return response.get_json()['prompt']

class TestPromptsAPI:
    """Test cases for the Prompts API endpoints"""
    
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'PromptLab Backend'
    
    def test_get_prompts_empty(self, client):
        """Test getting prompts when database is empty"""
        response = client.get('/api/prompts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['prompts'] == []
        assert data['count'] == 0
    
    def test_create_prompt_success(self, client, sample_prompt_data):
        """Test creating a prompt with valid data"""
        response = client.post('/api/prompts', 
                              data=json.dumps(sample_prompt_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Prompt created successfully'
        
        prompt = data['prompt']
        assert prompt['name'] == sample_prompt_data['name']
        assert prompt['description'] == sample_prompt_data['description']
        assert prompt['system_prompt'] == sample_prompt_data['system_prompt']
        assert prompt['model'] == sample_prompt_data['model']
        assert prompt['temperature'] == sample_prompt_data['temperature']
        assert 'id' in prompt
        assert 'created_at' in prompt
        assert 'updated_at' in prompt
    
    def test_create_prompt_minimal_data(self, client):
        """Test creating a prompt with only required fields"""
        minimal_data = {
            'name': 'Minimal Prompt',
            'system_prompt': 'You are a helpful assistant.'
        }
        
        response = client.post('/api/prompts', 
                              data=json.dumps(minimal_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        prompt = data['prompt']
        
        assert prompt['name'] == minimal_data['name']
        assert prompt['system_prompt'] == minimal_data['system_prompt']
        assert prompt['model'] == 'llama2'  # Default value
        assert prompt['temperature'] == 0.7  # Default value
        assert prompt['description'] is None
    
    def test_create_prompt_missing_required_fields(self, client):
        """Test creating a prompt with missing required fields"""
        # Missing name
        invalid_data = {
            'system_prompt': 'You are a helpful assistant.'
        }
        
        response = client.post('/api/prompts', 
                              data=json.dumps(invalid_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'name' in data['details']
        
        # Missing system_prompt
        invalid_data = {
            'name': 'Test Prompt'
        }
        
        response = client.post('/api/prompts', 
                              data=json.dumps(invalid_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] is True
        assert 'system_prompt' in data['details']
    
    def test_create_prompt_invalid_data(self, client):
        """Test creating a prompt with invalid field values"""
        # Invalid temperature
        invalid_data = {
            'name': 'Test Prompt',
            'system_prompt': 'You are a helpful assistant.',
            'temperature': 3.0  # Out of range
        }
        
        response = client.post('/api/prompts', 
                              data=json.dumps(invalid_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] is True
        assert 'temperature' in data['details']
    
    def test_create_prompt_duplicate_name(self, client, create_test_prompt):
        """Test creating a prompt with duplicate name"""
        duplicate_data = {
            'name': create_test_prompt['name'],  # Same name as existing prompt
            'system_prompt': 'Different system prompt'
        }
        
        response = client.post('/api/prompts', 
                              data=json.dumps(duplicate_data),
                              content_type='application/json')
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'DUPLICATE_NAME'
    
    def test_create_prompt_invalid_json(self, client):
        """Test creating a prompt with invalid JSON"""
        response = client.post('/api/prompts', 
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'INVALID_JSON'
    
    def test_get_prompts_with_data(self, client, create_test_prompt):
        """Test getting prompts when database has data"""
        response = client.get('/api/prompts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert len(data['prompts']) == 1
        assert data['count'] == 1
        
        prompt = data['prompts'][0]
        assert prompt['id'] == create_test_prompt['id']
        assert prompt['name'] == create_test_prompt['name']
    
    def test_search_prompts_by_name(self, client, create_test_prompt):
        """Test searching prompts by name"""
        # Create additional prompt
        additional_data = {
            'name': 'Another Prompt',
            'system_prompt': 'Another system prompt'
        }
        client.post('/api/prompts', 
                   data=json.dumps(additional_data),
                   content_type='application/json')
        
        # Search for specific prompt
        response = client.get('/api/prompts?search=Test')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 1
        assert data['prompts'][0]['name'] == create_test_prompt['name']
    
    def test_search_prompts_by_description(self, client, create_test_prompt):
        """Test searching prompts by description"""
        # Create prompt with specific description
        specific_data = {
            'name': 'Specific Prompt',
            'description': 'This is a unique description for searching',
            'system_prompt': 'System prompt'
        }
        client.post('/api/prompts', 
                   data=json.dumps(specific_data),
                   content_type='application/json')
        
        # Search by description
        response = client.get('/api/prompts?search=unique')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 1
        assert data['prompts'][0]['name'] == 'Specific Prompt'
    
    def test_search_prompts_case_insensitive(self, client, create_test_prompt):
        """Test that search is case-insensitive"""
        # Search with different cases
        test_cases = ['test', 'TEST', 'Test', 'tEsT']
        
        for search_term in test_cases:
            response = client.get(f'/api/prompts?search={search_term}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert data['count'] == 1
            assert data['prompts'][0]['name'] == create_test_prompt['name']
    
    def test_search_prompts_no_results(self, client, create_test_prompt):
        """Test searching with no matching results"""
        response = client.get('/api/prompts?search=nonexistent')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['prompts'] == []
    
    def test_update_prompt_success(self, client, create_test_prompt):
        """Test updating a prompt with valid data"""
        update_data = {
            'name': 'Updated Prompt Name',
            'description': 'Updated description',
            'temperature': 1.2
        }
        
        prompt_id = create_test_prompt['id']
        response = client.put(f'/api/prompts/{prompt_id}', 
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Prompt updated successfully'
        
        prompt = data['prompt']
        assert prompt['name'] == update_data['name']
        assert prompt['description'] == update_data['description']
        assert prompt['temperature'] == update_data['temperature']
        # Unchanged fields
        assert prompt['system_prompt'] == create_test_prompt['system_prompt']
        assert prompt['model'] == create_test_prompt['model']
    
    def test_update_prompt_not_found(self, client):
        """Test updating a non-existent prompt"""
        update_data = {
            'name': 'Updated Name'
        }
        
        response = client.put('/api/prompts/999', 
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'NOT_FOUND'
    
    def test_update_prompt_invalid_data(self, client, create_test_prompt):
        """Test updating a prompt with invalid data"""
        update_data = {
            'temperature': 5.0  # Out of range
        }
        
        prompt_id = create_test_prompt['id']
        response = client.put(f'/api/prompts/{prompt_id}', 
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'VALIDATION_ERROR'
        assert 'temperature' in data['details']
    
    def test_delete_prompt_success(self, client, create_test_prompt):
        """Test deleting a prompt successfully"""
        prompt_id = create_test_prompt['id']
        response = client.delete(f'/api/prompts/{prompt_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Prompt deleted successfully'
        assert data['deleted_prompt']['id'] == prompt_id
        
        # Verify prompt is actually deleted
        response = client.get('/api/prompts')
        data = response.get_json()
        assert data['count'] == 0
    
    def test_delete_prompt_not_found(self, client):
        """Test deleting a non-existent prompt"""
        response = client.delete('/api/prompts/999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'NOT_FOUND'
    
    def test_api_error_handling_invalid_methods(self, client):
        """Test API error handling for invalid HTTP methods"""
        # Test invalid method on prompts collection
        response = client.patch('/api/prompts')
        assert response.status_code == 405
        
        # Test invalid method on specific prompt
        response = client.patch('/api/prompts/1')
        assert response.status_code == 405
    
    def test_multiple_prompts_ordering(self, client):
        """Test that multiple prompts are returned in consistent order"""
        # Create multiple prompts
        prompts_data = [
            {'name': 'Zebra Prompt', 'system_prompt': 'System prompt Z'},
            {'name': 'Alpha Prompt', 'system_prompt': 'System prompt A'},
            {'name': 'Beta Prompt', 'system_prompt': 'System prompt B'}
        ]
        
        for prompt_data in prompts_data:
            client.post('/api/prompts', 
                       data=json.dumps(prompt_data),
                       content_type='application/json')
        
        # Get all prompts
        response = client.get('/api/prompts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['count'] == 3
        
        # Verify alphabetical ordering by name
        names = [prompt['name'] for prompt in data['prompts']]
        assert names == ['Alpha Prompt', 'Beta Prompt', 'Zebra Prompt']

class TestImportExportAPI:
    """Test cases for the Import/Export API endpoints"""
    
    def test_export_library_empty(self, client):
        """Test exporting an empty library"""
        response = client.post('/api/export-library')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'export_data' in data
        assert 'metadata' in data
        assert data['metadata']['total_prompts'] == 0
        
        # Verify export data structure
        import json
        export_data = json.loads(data['export_data'])
        assert 'metadata' in export_data
        assert 'prompts' in export_data
        assert export_data['prompts'] == []
    
    def test_export_library_json_format(self, client, create_test_prompt):
        """Test exporting library in JSON format"""
        response = client.post('/api/export-library', 
                              data=json.dumps({'format': 'json'}),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['content_type'] == 'application/json'
        assert data['metadata']['total_prompts'] == 1
        
        # Verify export data can be parsed as JSON
        export_data = json.loads(data['export_data'])
        assert len(export_data['prompts']) == 1
        assert export_data['prompts'][0]['name'] == create_test_prompt['name']
    
    def test_export_library_yaml_format(self, client, create_test_prompt):
        """Test exporting library in YAML format"""
        response = client.post('/api/export-library', 
                              data=json.dumps({'format': 'yaml'}),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['content_type'] == 'application/x-yaml'
        assert data['metadata']['total_prompts'] == 1
        
        # Verify export data can be parsed as YAML
        import yaml
        export_data = yaml.safe_load(data['export_data'])
        assert len(export_data['prompts']) == 1
        assert export_data['prompts'][0]['name'] == create_test_prompt['name']
    
    def test_export_library_invalid_format(self, client):
        """Test exporting library with invalid format"""
        response = client.post('/api/export-library', 
                              data=json.dumps({'format': 'xml'}),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'INVALID_FORMAT'
    
    def test_import_library_json_success(self, client):
        """Test importing library from JSON format"""
        import_data = {
            'metadata': {
                'export_timestamp': '2023-01-01T00:00:00Z',
                'total_prompts': 2,
                'format_version': '1.0'
            },
            'prompts': [
                {
                    'name': 'Imported Prompt 1',
                    'description': 'First imported prompt',
                    'system_prompt': 'You are a helpful assistant.',
                    'model': 'llama2',
                    'temperature': 0.7
                },
                {
                    'name': 'Imported Prompt 2',
                    'system_prompt': 'You are a creative assistant.',
                    'model': 'gpt-3.5',
                    'temperature': 1.0
                }
            ]
        }
        
        request_data = {
            'import_data': json.dumps(import_data),
            'format': 'json'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['imported'] == 2
        assert data['summary']['errors'] == 0
        
        # Verify prompts were actually imported
        response = client.get('/api/prompts')
        prompts_data = response.get_json()
        assert prompts_data['count'] == 2
    
    def test_import_library_yaml_success(self, client):
        """Test importing library from YAML format"""
        import yaml
        import_data = {
            'metadata': {
                'export_timestamp': '2023-01-01T00:00:00Z',
                'total_prompts': 1
            },
            'prompts': [
                {
                    'name': 'YAML Imported Prompt',
                    'system_prompt': 'You are a YAML assistant.',
                    'model': 'llama2',
                    'temperature': 0.5
                }
            ]
        }
        
        request_data = {
            'import_data': yaml.dump(import_data),
            'format': 'yaml'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['imported'] == 1
    
    def test_import_library_conflict_skip(self, client, create_test_prompt):
        """Test importing library with conflict resolution set to skip"""
        import_data = {
            'prompts': [
                {
                    'name': create_test_prompt['name'],  # Conflicting name
                    'system_prompt': 'Different system prompt',
                    'model': 'different-model',
                    'temperature': 1.5
                }
            ]
        }
        
        request_data = {
            'import_data': json.dumps(import_data),
            'conflict_resolution': 'skip'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['skipped'] == 1
        assert data['summary']['imported'] == 0
        
        # Verify original prompt unchanged
        response = client.get('/api/prompts')
        prompts_data = response.get_json()
        assert prompts_data['count'] == 1
        original_prompt = prompts_data['prompts'][0]
        assert original_prompt['system_prompt'] == create_test_prompt['system_prompt']
    
    def test_import_library_conflict_overwrite(self, client, create_test_prompt):
        """Test importing library with conflict resolution set to overwrite"""
        new_system_prompt = 'Overwritten system prompt'
        import_data = {
            'prompts': [
                {
                    'name': create_test_prompt['name'],  # Conflicting name
                    'system_prompt': new_system_prompt,
                    'model': 'new-model',
                    'temperature': 1.5
                }
            ]
        }
        
        request_data = {
            'import_data': json.dumps(import_data),
            'conflict_resolution': 'overwrite'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['overwritten'] == 1
        assert data['summary']['imported'] == 0
        
        # Verify prompt was overwritten
        response = client.get('/api/prompts')
        prompts_data = response.get_json()
        assert prompts_data['count'] == 1
        updated_prompt = prompts_data['prompts'][0]
        assert updated_prompt['system_prompt'] == new_system_prompt
        assert updated_prompt['model'] == 'new-model'
    
    def test_import_library_conflict_rename(self, client, create_test_prompt):
        """Test importing library with conflict resolution set to rename"""
        import_data = {
            'prompts': [
                {
                    'name': create_test_prompt['name'],  # Conflicting name
                    'system_prompt': 'Renamed system prompt',
                    'model': 'renamed-model',
                    'temperature': 1.2
                }
            ]
        }
        
        request_data = {
            'import_data': json.dumps(import_data),
            'conflict_resolution': 'rename'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['renamed'] == 1
        assert data['summary']['imported'] == 1
        
        # Verify both prompts exist
        response = client.get('/api/prompts')
        prompts_data = response.get_json()
        assert prompts_data['count'] == 2
        
        # Check that renamed prompt has suffix
        prompt_names = [p['name'] for p in prompts_data['prompts']]
        assert create_test_prompt['name'] in prompt_names
        assert f"{create_test_prompt['name']} (1)" in prompt_names
    
    def test_import_library_invalid_data_structure(self, client):
        """Test importing library with invalid data structure"""
        # Missing prompts field
        invalid_data = {
            'metadata': {'total_prompts': 1}
        }
        
        request_data = {
            'import_data': json.dumps(invalid_data)
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'MISSING_PROMPTS_FIELD'
    
    def test_import_library_invalid_prompt_data(self, client):
        """Test importing library with invalid prompt data"""
        import_data = {
            'prompts': [
                {
                    'name': 'Valid Prompt',
                    'system_prompt': 'Valid system prompt'
                },
                {
                    'name': '',  # Invalid: empty name
                    'system_prompt': 'System prompt'
                },
                {
                    'name': 'Missing System Prompt'
                    # Missing system_prompt
                }
            ]
        }
        
        request_data = {
            'import_data': json.dumps(import_data)
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['summary']['imported'] == 1  # Only valid prompt imported
        assert data['summary']['errors'] == 2   # Two invalid prompts
    
    def test_import_library_invalid_json(self, client):
        """Test importing library with invalid JSON"""
        request_data = {
            'import_data': '{"invalid": json, "missing": quotes}',  # Invalid JSON syntax
            'format': 'json'  # Force JSON parsing
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'PARSE_ERROR'
    
    def test_import_library_missing_import_data(self, client):
        """Test importing library without import_data field"""
        request_data = {
            'conflict_resolution': 'skip'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'MISSING_IMPORT_DATA'
    
    def test_import_library_invalid_conflict_resolution(self, client):
        """Test importing library with invalid conflict resolution"""
        import_data = {
            'prompts': []
        }
        
        request_data = {
            'import_data': json.dumps(import_data),
            'conflict_resolution': 'invalid_option'
        }
        
        response = client.post('/api/import-library', 
                              data=json.dumps(request_data),
                              content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['error'] is True
        assert data['code'] == 'INVALID_CONFLICT_RESOLUTION'
    
    def test_export_import_roundtrip(self, client, create_test_prompt):
        """Test complete export-import roundtrip"""
        # Export the library
        export_response = client.post('/api/export-library')
        assert export_response.status_code == 200
        export_data = export_response.get_json()
        
        # Delete the original prompt
        client.delete(f'/api/prompts/{create_test_prompt["id"]}')
        
        # Verify library is empty
        response = client.get('/api/prompts')
        assert response.get_json()['count'] == 0
        
        # Import the exported data
        request_data = {
            'import_data': export_data['export_data']
        }
        
        import_response = client.post('/api/import-library', 
                                     data=json.dumps(request_data),
                                     content_type='application/json')
        assert import_response.status_code == 200
        
        import_result = import_response.get_json()
        assert import_result['success'] is True
        assert import_result['summary']['imported'] == 1
        
        # Verify prompt was restored
        response = client.get('/api/prompts')
        prompts_data = response.get_json()
        assert prompts_data['count'] == 1
        restored_prompt = prompts_data['prompts'][0]
        assert restored_prompt['name'] == create_test_prompt['name']
        assert restored_prompt['system_prompt'] == create_test_prompt['system_prompt']