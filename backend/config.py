"""
PromptLab Configuration Management
"""

import os
from dataclasses import dataclass
from typing import Optional

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
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables"""
        return cls(
            ollama_endpoint=os.getenv('OLLAMA_ENDPOINT', cls.ollama_endpoint),
            default_model=os.getenv('DEFAULT_MODEL', cls.default_model),
            default_temperature=float(os.getenv('DEFAULT_TEMPERATURE', cls.default_temperature)),
            database_path=os.getenv('DATABASE_PATH', cls.database_path),
            flask_host=os.getenv('FLASK_HOST', cls.flask_host),
            flask_port=int(os.getenv('FLASK_PORT', cls.flask_port)),
            flask_debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        )

# Global configuration instance
config = AppConfig.from_env()