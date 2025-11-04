"""
Unit tests for PromptLab data models
Tests for Prompt model validation, serialization, and database operations
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from backend.models.prompt import Prompt

class TestPromptModel:
    """Test cases for the Prompt model"""
    
    def test_prompt_creation_with_valid_data(self, db_session, sample_prompt_data):
        """Test creating a prompt with valid data"""
        prompt = Prompt(**sample_prompt_data)
        db_session.add(prompt)
        db_session.commit()
        
        assert prompt.id is not None
        assert prompt.name == sample_prompt_data['name']
        assert prompt.description == sample_prompt_data['description']
        assert prompt.system_prompt == sample_prompt_data['system_prompt']
        assert prompt.model == sample_prompt_data['model']
        assert prompt.temperature == sample_prompt_data['temperature']
        assert isinstance(prompt.created_at, datetime)
        assert isinstance(prompt.updated_at, datetime)
    
    def test_prompt_creation_with_minimal_data(self, db_session):
        """Test creating a prompt with only required fields"""
        prompt = Prompt(
            name='Minimal Prompt',
            system_prompt='You are a helpful assistant.'
        )
        db_session.add(prompt)
        db_session.commit()
        
        assert prompt.id is not None
        assert prompt.name == 'Minimal Prompt'
        assert prompt.description is None
        assert prompt.model == 'llama2'  # Default value
        assert prompt.temperature == 0.7  # Default value
    
    def test_prompt_name_validation(self, db_session):
        """Test prompt name validation rules"""
        # Test empty name
        with pytest.raises(ValueError, match="Prompt name cannot be empty"):
            Prompt(name='', system_prompt='Test')
        
        # Test whitespace-only name
        with pytest.raises(ValueError, match="Prompt name cannot be empty"):
            Prompt(name='   ', system_prompt='Test')
        
        # Test name too long
        long_name = 'x' * 256
        with pytest.raises(ValueError, match="Prompt name cannot exceed 255 characters"):
            Prompt(name=long_name, system_prompt='Test')
        
        # Test invalid characters
        invalid_names = ['test/name', 'test\\name', 'test:name', 'test*name', 'test?name']
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Prompt name cannot contain these characters"):
                Prompt(name=invalid_name, system_prompt='Test')
    
    def test_system_prompt_validation(self, db_session):
        """Test system prompt validation rules"""
        # Test empty system prompt
        with pytest.raises(ValueError, match="System prompt cannot be empty"):
            Prompt(name='Test', system_prompt='')
        
        # Test whitespace-only system prompt
        with pytest.raises(ValueError, match="System prompt cannot be empty"):
            Prompt(name='Test', system_prompt='   ')
        
        # Test system prompt too long
        long_prompt = 'x' * 50001
        with pytest.raises(ValueError, match="System prompt cannot exceed 50,000 characters"):
            Prompt(name='Test', system_prompt=long_prompt)
    
    def test_model_validation(self, db_session):
        """Test model name validation rules"""
        # Test empty model
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            Prompt(name='Test', system_prompt='Test', model='')
        
        # Test model name too long
        long_model = 'x' * 101
        with pytest.raises(ValueError, match="Model name cannot exceed 100 characters"):
            Prompt(name='Test', system_prompt='Test', model=long_model)
    
    def test_temperature_validation(self, db_session):
        """Test temperature parameter validation rules"""
        # Test None temperature
        with pytest.raises(ValueError, match="Temperature cannot be None"):
            Prompt(name='Test', system_prompt='Test', temperature=None)
        
        # Test invalid temperature type
        with pytest.raises(ValueError, match="Temperature must be a valid number"):
            Prompt(name='Test', system_prompt='Test', temperature='invalid')
        
        # Test temperature out of range
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            Prompt(name='Test', system_prompt='Test', temperature=-0.1)
        
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 2.0"):
            Prompt(name='Test', system_prompt='Test', temperature=2.1)
        
        # Test valid temperature values
        valid_temps = [0.0, 0.5, 1.0, 1.5, 2.0]
        for temp in valid_temps:
            prompt = Prompt(name=f'Test{temp}', system_prompt='Test', temperature=temp)
            assert prompt.temperature == temp
    
    def test_description_validation(self, db_session):
        """Test description field validation"""
        # Test description too long
        long_description = 'x' * 1001
        with pytest.raises(ValueError, match="Description cannot exceed 1,000 characters"):
            Prompt(name='Test', system_prompt='Test', description=long_description)
        
        # Test empty description becomes None
        prompt = Prompt(name='Test', system_prompt='Test', description='')
        assert prompt.description is None
        
        # Test whitespace-only description becomes None
        prompt = Prompt(name='Test', system_prompt='Test', description='   ')
        assert prompt.description is None
    
    def test_unique_name_constraint(self, db_session, sample_prompt):
        """Test that prompt names must be unique"""
        # Try to create another prompt with the same name
        duplicate_prompt = Prompt(
            name=sample_prompt.name,
            system_prompt='Different prompt content'
        )
        db_session.add(duplicate_prompt)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_to_dict_serialization(self, sample_prompt):
        """Test prompt serialization to dictionary"""
        prompt_dict = sample_prompt.to_dict()
        
        assert isinstance(prompt_dict, dict)
        assert prompt_dict['id'] == sample_prompt.id
        assert prompt_dict['name'] == sample_prompt.name
        assert prompt_dict['description'] == sample_prompt.description
        assert prompt_dict['system_prompt'] == sample_prompt.system_prompt
        assert prompt_dict['model'] == sample_prompt.model
        assert prompt_dict['temperature'] == sample_prompt.temperature
        assert 'created_at' in prompt_dict
        assert 'updated_at' in prompt_dict
        
        # Test datetime serialization
        assert isinstance(prompt_dict['created_at'], str)
        assert isinstance(prompt_dict['updated_at'], str)
    
    def test_update_from_dict(self, db_session, sample_prompt):
        """Test updating prompt from dictionary data"""
        original_created_at = sample_prompt.created_at
        original_updated_at = sample_prompt.updated_at
        
        update_data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'system_prompt': 'Updated system prompt',
            'model': 'updated-model',
            'temperature': 1.2
        }
        
        sample_prompt.update_from_dict(update_data)
        db_session.commit()
        
        assert sample_prompt.name == update_data['name']
        assert sample_prompt.description == update_data['description']
        assert sample_prompt.system_prompt == update_data['system_prompt']
        assert sample_prompt.model == update_data['model']
        assert sample_prompt.temperature == update_data['temperature']
        assert sample_prompt.created_at == original_created_at  # Should not change
        assert sample_prompt.updated_at > original_updated_at  # Should be updated
    
    def test_update_from_dict_partial(self, db_session, sample_prompt):
        """Test partial update from dictionary data"""
        original_name = sample_prompt.name
        original_model = sample_prompt.model
        
        update_data = {
            'description': 'Only updating description',
            'temperature': 1.5
        }
        
        sample_prompt.update_from_dict(update_data)
        db_session.commit()
        
        # Updated fields
        assert sample_prompt.description == update_data['description']
        assert sample_prompt.temperature == update_data['temperature']
        
        # Unchanged fields
        assert sample_prompt.name == original_name
        assert sample_prompt.model == original_model
    
    def test_string_representations(self, sample_prompt):
        """Test __repr__ and __str__ methods"""
        repr_str = repr(sample_prompt)
        str_str = str(sample_prompt)
        
        assert f"Prompt(id={sample_prompt.id}" in repr_str
        assert sample_prompt.name in repr_str
        assert sample_prompt.model in repr_str
        
        assert sample_prompt.name in str_str
        assert sample_prompt.model in str_str
        assert str(sample_prompt.temperature) in str_str