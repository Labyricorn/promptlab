"""
PromptLab Configuration Management
"""

import os
import json
import yaml
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class AppConfig:
    """Application configuration with default values"""
    ollama_endpoint: str = "http://localhost:11434"
    default_model: str = "llama2"
    default_temperature: float = 0.7
    database_path: str = "promptlab.db"
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    flask_debug: bool = True
    
    def validate(self) -> Dict[str, str]:
        """Validate configuration values and return errors if any"""
        errors = {}
        
        # Validate ollama_endpoint
        if not self.ollama_endpoint or not isinstance(self.ollama_endpoint, str):
            errors['ollama_endpoint'] = 'Ollama endpoint must be a valid URL string'
        elif not self.ollama_endpoint.startswith(('http://', 'https://')):
            errors['ollama_endpoint'] = 'Ollama endpoint must start with http:// or https://'
        
        # Validate default_model
        if not self.default_model or not isinstance(self.default_model, str):
            errors['default_model'] = 'Default model must be a non-empty string'
        elif len(self.default_model.strip()) == 0:
            errors['default_model'] = 'Default model cannot be empty'
        
        # Validate default_temperature
        if not isinstance(self.default_temperature, (int, float)):
            errors['default_temperature'] = 'Default temperature must be a number'
        elif not (0.0 <= self.default_temperature <= 2.0):
            errors['default_temperature'] = 'Default temperature must be between 0.0 and 2.0'
        
        # Validate database_path
        if not self.database_path or not isinstance(self.database_path, str):
            errors['database_path'] = 'Database path must be a non-empty string'
        
        # Validate flask_host
        if not self.flask_host or not isinstance(self.flask_host, str):
            errors['flask_host'] = 'Flask host must be a non-empty string'
        
        # Validate flask_port
        if not isinstance(self.flask_port, int):
            errors['flask_port'] = 'Flask port must be an integer'
        elif not (1 <= self.flask_port <= 65535):
            errors['flask_port'] = 'Flask port must be between 1 and 65535'
        
        # Validate flask_debug
        if not isinstance(self.flask_debug, bool):
            errors['flask_debug'] = 'Flask debug must be a boolean value'
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary with type conversion"""
        config_data = {}
        
        # Handle each field with proper type conversion
        if 'ollama_endpoint' in data:
            config_data['ollama_endpoint'] = str(data['ollama_endpoint'])
        
        if 'default_model' in data:
            config_data['default_model'] = str(data['default_model'])
        
        if 'default_temperature' in data:
            try:
                config_data['default_temperature'] = float(data['default_temperature'])
            except (ValueError, TypeError):
                config_data['default_temperature'] = cls.default_temperature
        
        if 'database_path' in data:
            config_data['database_path'] = str(data['database_path'])
        
        if 'flask_host' in data:
            config_data['flask_host'] = str(data['flask_host'])
        
        if 'flask_port' in data:
            try:
                config_data['flask_port'] = int(data['flask_port'])
            except (ValueError, TypeError):
                config_data['flask_port'] = cls.flask_port
        
        if 'flask_debug' in data:
            if isinstance(data['flask_debug'], bool):
                config_data['flask_debug'] = data['flask_debug']
            elif isinstance(data['flask_debug'], str):
                config_data['flask_debug'] = data['flask_debug'].lower() in ('true', '1', 'yes', 'on')
            else:
                config_data['flask_debug'] = cls.flask_debug
        
        return cls(**config_data)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AppConfig':
        """Load configuration from JSON or YAML file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_file.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {config_file.suffix}")
            
            if not isinstance(data, dict):
                raise ValueError("Configuration file must contain a JSON object or YAML mapping")
            
            return cls.from_dict(data)
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid configuration file format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration file: {e}")
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables"""
        return cls(
            ollama_endpoint=os.getenv('OLLAMA_ENDPOINT', cls.ollama_endpoint),
            default_model=os.getenv('DEFAULT_MODEL', cls.default_model),
            default_temperature=float(os.getenv('DEFAULT_TEMPERATURE', str(cls.default_temperature))),
            database_path=os.getenv('DATABASE_PATH', cls.database_path),
            flask_host=os.getenv('FLASK_HOST', cls.flask_host),
            flask_port=int(os.getenv('FLASK_PORT', str(cls.flask_port))),
            flask_debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        )
    
    @classmethod
    def load_config(cls, config_path: Optional[str] = None) -> 'AppConfig':
        """Load configuration with fallback priority: file -> env -> defaults"""
        if config_path and os.path.exists(config_path):
            try:
                return cls.from_file(config_path)
            except Exception:
                # Fall back to environment variables if file loading fails
                pass
        
        return cls.from_env()

# Global configuration instance
config = AppConfig.load_config(os.getenv('CONFIG_FILE'))