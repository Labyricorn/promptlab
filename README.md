# PromptLab

A local-first prompt engineering environment for creating, refining, testing, and managing AI prompts.

## Quick Start

1. **Prerequisites**
   - Python 3.8 or higher
   - Local Ollama installation (optional for initial setup)

2. **Setup**
   ```bash
   # Clone or download the project
   cd promptlab
   
   # Create virtual environment (recommended)
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Run PromptLab**
   ```bash
   python run.py
   ```

The application will automatically:
- Install required dependencies
- Start the backend server
- Open your default browser to the PromptLab interface

## Project Structure

```
promptlab/
├── backend/           # Python backend
│   ├── api/          # REST API endpoints
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   ├── app.py        # Flask application
│   └── config.py     # Configuration management
├── frontend/         # Web frontend
│   ├── css/         # Stylesheets
│   ├── js/          # JavaScript modules
│   └── index.html   # Main page
├── run.py           # Startup script
├── requirements.txt # Python dependencies
└── README.md       # This file
```

## Development

- Backend runs on `http://localhost:5000`
- Frontend is served from the same port
- SQLite database will be created automatically
- CORS is configured for local development

## Next Steps

After running the application, you can:
1. Configure your Ollama endpoint in settings
2. Create your first prompt
3. Test prompts with local AI models
4. Build your prompt library

For detailed usage instructions, see the application interface.