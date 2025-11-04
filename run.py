#!/usr/bin/env python3
"""
PromptLab Startup Script
Single-command launch for the complete application
"""

import os
import sys
import webbrowser
import time
import threading
from pathlib import Path

def check_python_version():
    """Ensure Python 3.8+ is being used"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def setup_virtual_environment():
    """Check if we're in a virtual environment, suggest creating one if not"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not running in a virtual environment")
        print("Consider creating one with: python -m venv venv")
        print("Then activate it and run: pip install -r requirements.txt")
        print()

def install_dependencies():
    """Install required Python packages"""
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        print("Installing dependencies...")
        os.system(f"{sys.executable} -m pip install -r requirements.txt")
    else:
        print("Warning: requirements.txt not found")

def open_browser_delayed(url, delay=2):
    """Open browser after a delay to ensure server is ready"""
    def delayed_open():
        time.sleep(delay)
        print(f"Opening browser at {url}")
        webbrowser.open(url)
    
    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def main():
    """Main startup function"""
    print("=" * 50)
    print("PromptLab - Prompt Engineering Environment")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Check virtual environment
    setup_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Add backend to Python path
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        # Import and create Flask app
        from backend.app import create_app
        from backend.config import config
        
        app = create_app()
        
        # Schedule browser opening
        url = f"http://{config.flask_host}:{config.flask_port}"
        open_browser_delayed(url)
        
        print(f"Starting PromptLab server...")
        print(f"Server will be available at: {url}")
        print("Press Ctrl+C to stop the server")
        print()
        
        # Start the Flask application
        app.run(
            host=config.flask_host,
            port=config.flask_port,
            debug=config.flask_debug
        )
        
    except ImportError as e:
        print(f"Error importing backend modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down PromptLab...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting PromptLab: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()