"""
PromptLab Database Configuration and Initialization
SQLAlchemy setup with SQLite database connection
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from backend.config import config

# Create declarative base for models
Base = declarative_base()

# Database engine and session configuration
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection and create tables"""
    global engine, SessionLocal
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(config.database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Create SQLite engine with proper configuration
    database_url = f"sqlite:///{config.database_path}"
    engine = create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        connect_args={"check_same_thread": False}  # Allow SQLite to work with multiple threads
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if 'sqlite' in str(dbapi_connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Import models to ensure they are registered with Base
    from backend.models.prompt import Prompt
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine

def get_db_session():
    """Get database session with proper cleanup"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = SessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise

def close_db_session(session):
    """Close database session properly"""
    if session:
        session.close()

def reset_database():
    """Reset database by dropping and recreating all tables"""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    # Import models to ensure they are registered
    from backend.models.prompt import Prompt
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Recreate all tables
    Base.metadata.create_all(bind=engine)

def check_database_health():
    """Check if database is accessible and properly configured"""
    try:
        session = get_db_session()
        # Simple query to test connection
        session.execute("SELECT 1")
        close_db_session(session)
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False