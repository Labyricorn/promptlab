"""
Test configuration and fixtures for PromptLab tests
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models.prompt import Prompt

@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create test engine
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestSessionLocal, engine
    
    # Cleanup - dispose engine first to close connections
    engine.dispose()
    try:
        os.unlink(db_path)
    except (OSError, PermissionError):
        # On Windows, sometimes the file is still locked
        pass

@pytest.fixture
def db_session(test_db):
    """Create a database session for testing"""
    TestSessionLocal, engine = test_db
    session = TestSessionLocal()
    
    yield session
    
    session.close()

@pytest.fixture
def sample_prompt_data():
    """Sample prompt data for testing"""
    return {
        'name': 'Test Prompt',
        'description': 'A test prompt for unit testing',
        'system_prompt': 'You are a helpful assistant for testing purposes.',
        'model': 'llama2',
        'temperature': 0.7
    }

@pytest.fixture
def sample_prompt(db_session, sample_prompt_data):
    """Create a sample prompt in the database"""
    prompt = Prompt(**sample_prompt_data)
    db_session.add(prompt)
    db_session.commit()
    db_session.refresh(prompt)
    return prompt