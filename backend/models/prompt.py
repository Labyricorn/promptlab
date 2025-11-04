"""
PromptLab Prompt Data Model
SQLAlchemy model for storing and managing prompts
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import validates
from backend.database import Base

class Prompt(Base):
    """
    Prompt model for storing system prompts with metadata
    
    Represents a saved prompt with all necessary configuration
    for AI model interaction including system prompt text,
    model selection, and temperature settings.
    """
    __tablename__ = 'prompts'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Required fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    system_prompt = Column(Text, nullable=False)
    model = Column(String(100), nullable=False, default='llama2')
    temperature = Column(Float, nullable=False, default=0.7)
    
    # Optional fields
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __init__(self, name, system_prompt, model='llama2', temperature=0.7, description=None):
        """Initialize a new Prompt instance with validation"""
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.description = description
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate prompt name"""
        if not name or not name.strip():
            raise ValueError("Prompt name cannot be empty")
        
        name = name.strip()
        if len(name) > 255:
            raise ValueError("Prompt name cannot exceed 255 characters")
        
        # Check for invalid characters that might cause issues
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in name for char in invalid_chars):
            raise ValueError(f"Prompt name cannot contain these characters: {', '.join(invalid_chars)}")
        
        return name
    
    @validates('system_prompt')
    def validate_system_prompt(self, key, system_prompt):
        """Validate system prompt content"""
        if not system_prompt or not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        
        system_prompt = system_prompt.strip()
        if len(system_prompt) > 50000:  # Reasonable limit for prompt length
            raise ValueError("System prompt cannot exceed 50,000 characters")
        
        return system_prompt
    
    @validates('model')
    def validate_model(self, key, model):
        """Validate model name"""
        if not model or not model.strip():
            raise ValueError("Model name cannot be empty")
        
        model = model.strip()
        if len(model) > 100:
            raise ValueError("Model name cannot exceed 100 characters")
        
        return model
    
    @validates('temperature')
    def validate_temperature(self, key, temperature):
        """Validate temperature parameter"""
        if temperature is None:
            raise ValueError("Temperature cannot be None")
        
        try:
            temperature = float(temperature)
        except (ValueError, TypeError):
            raise ValueError("Temperature must be a valid number")
        
        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        return temperature
    
    @validates('description')
    def validate_description(self, key, description):
        """Validate optional description field"""
        if description is not None:
            description = description.strip()
            if len(description) > 1000:
                raise ValueError("Description cannot exceed 1,000 characters")
            # Return None for empty descriptions
            return description if description else None
        return description
    
    def to_dict(self):
        """
        Convert Prompt instance to dictionary for API responses
        
        Returns:
            dict: Dictionary representation of the prompt
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'model': self.model,
            'temperature': self.temperature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_from_dict(self, data):
        """
        Update prompt fields from dictionary data
        
        Args:
            data (dict): Dictionary containing fields to update
        """
        updatable_fields = ['name', 'description', 'system_prompt', 'model', 'temperature']
        
        for field in updatable_fields:
            if field in data:
                setattr(self, field, data[field])
        
        # Update timestamp
        self.updated_at = datetime.now(timezone.utc)
    
    def __repr__(self):
        """String representation of Prompt instance"""
        return f"<Prompt(id={self.id}, name='{self.name}', model='{self.model}')>"
    
    def __str__(self):
        """Human-readable string representation"""
        return f"Prompt '{self.name}' using {self.model} (temp: {self.temperature})"