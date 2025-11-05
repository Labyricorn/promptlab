# 🧪 PromptLab

A local-first prompt engineering environment for creating, refining, testing, and managing AI prompts with an intuitive three-panel interface.

## ✨ Features

- **🎯 Objective-to-Prompt Refinement**: Transform simple objectives into detailed system prompts using AI assistance
- **📝 Advanced Prompt Editor**: Monaco Editor with syntax highlighting and auto-save functionality
- **🧪 Interactive Testing**: Test prompts with configurable parameters against local AI models
- **📚 Prompt Library**: Organize and search your prompt collection with metadata
- **🔄 Import/Export**: Backup and share your prompt libraries with conflict resolution
- **⚙️ Flexible Configuration**: Easy setup with automatic Ollama integration and connection testing
- **🌙 Dark Mode**: Toggle between light and dark themes with persistent preferences
- **📋 Copy to Clipboard**: Easy copying of system prompts and configurations
- **🔔 Smart Notifications**: Toast notifications and loading indicators for better UX
- **💾 Auto-Save Protection**: Warns about unsaved changes and prevents data loss
- **🌐 Browser-Based**: No additional client installations required

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (Required)
- **Ollama** (Recommended for AI features)
  - Install from [ollama.ai](https://ollama.ai)
  - Pull at least one model: `ollama pull llama2`

### Installation

1. **Download PromptLab**
   ```bash
   # Clone the repository or download the source code
   git clone <repository-url>
   cd promptlab
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Start PromptLab**
   ```bash
   python run.py
   ```

That's it! The startup script will:
- ✅ Check system requirements
- 📦 Install dependencies automatically
- 🗄️ Initialize the database
- 🤖 Test Ollama connection
- 🌐 Open your browser to the application

## 🎮 Usage Guide

### New Features & Improvements

**Recent Updates:**
- **🌙 Dark Mode**: Toggle between light and dark themes in settings
- **📋 Copy to Clipboard**: Copy button next to system prompts with visual feedback
- **🔔 Enhanced Notifications**: Toast messages for all operations with success/error states
- **⚙️ Better Settings**: Improved configuration modal with connection testing
- **🔄 Smart Import/Export**: Conflict resolution dialog for duplicate prompts
- **💾 Unsaved Changes Protection**: Warns before losing work
- **🎨 UI Polish**: Improved panel sizing, green accent colors, and responsive design
- **🔗 Attribution**: "Built with Kiro" link acknowledging the development platform

### Getting Started

1. **Launch the Application**
   - Run `python run.py`
   - Your browser will open to `http://localhost:5000`

2. **Configure Ollama** (First Time)
   - Click the ⚙️ Settings button
   - Verify Ollama endpoint (default: `http://localhost:11434`)
   - Test connection and refresh model list

3. **Create Your First Prompt**
   - Click "New Prompt" in the Library Panel
   - Enter an objective in the Workbench Panel
   - Click "Refine" to generate a detailed system prompt
   - Edit the prompt as needed
   - Save with a descriptive name

### Interface Overview

#### 📚 Library Panel (Left)
- **Search Bar**: Filter prompts by name or description with real-time results
- **Prompt List**: Browse your saved prompts with metadata
- **Actions**: New, Load, Delete prompts with confirmation dialogs
- **Import/Export**: Backup and restore your library with conflict resolution
- **Connection Status**: Shows "Ollama Connected" with endpoint information

#### 🛠️ Workbench Panel (Center)
- **Objective Input**: Enter simple prompt ideas for AI refinement
- **Refine Button**: AI-powered prompt enhancement with loading indicators
- **Monaco Editor**: Advanced prompt editing with syntax highlighting and auto-save detection
- **Save Controls**: Save new prompts or update existing ones with dirty state warnings
- **Copy Button**: Copy system prompts to clipboard with visual feedback

#### 🧪 Test Chamber (Right)
- **Test Input**: Enter messages to test your prompts
- **Parameters**: Adjust temperature (with green accent sliders) and select AI models
- **Run Test**: Execute prompts against Ollama with async feedback
- **Results**: View AI responses and copyable YAML configurations
- **Execution Time**: Shows test performance metrics

#### ⚙️ Settings Modal
- **Theme Toggle**: Switch between light and dark modes
- **Ollama Configuration**: Set endpoint URL with connection testing
- **Model Management**: Refresh and select available models
- **Built with Kiro**: Attribution link to development platform

### Example Workflow

1. **Start with an Objective**
   ```
   Create a helpful assistant for code reviews
   ```

2. **Refine to System Prompt**
   - Click "Refine" button (shows loading indicator)
   - AI generates detailed prompt in Monaco Editor
   ```
   You are an expert code reviewer with 10+ years of experience...
   [AI generates detailed prompt with syntax highlighting]
   ```

3. **Test the Prompt**
   - Input: "Review this Python function..."
   - Adjust temperature with green slider (0.1 for focused, 0.9 for creative)
   - Select model from dropdown
   - Run test and view response with execution time

4. **Save and Iterate**
   - Save as "Code Review Assistant v1" (gets confirmation toast)
   - Copy system prompt to clipboard if needed
   - Make improvements based on test results
   - Update existing prompt or save as new version
   - Export library for backup

5. **Theme and Settings**
   - Toggle dark mode for comfortable editing
   - Configure Ollama endpoint if using non-standard setup
   - Test connection and refresh model list

## 🔧 Configuration

### Application Settings

PromptLab can be configured through:

1. **Environment Variables**
   ```bash
   export OLLAMA_ENDPOINT="http://localhost:11434"
   export DEFAULT_MODEL="llama2"
   export DEFAULT_TEMPERATURE="0.7"
   export FLASK_HOST="127.0.0.1"
   export FLASK_PORT="5000"
   export DATABASE_PATH="promptlab.db"
   ```

2. **Configuration File** (config.json or config.yaml)
   ```json
   {
     "ollama_endpoint": "http://localhost:11434",
     "default_model": "llama2",
     "default_temperature": 0.7,
     "flask_host": "127.0.0.1",
     "flask_port": 5000,
     "database_path": "promptlab.db"
   }
   ```

3. **Settings UI** (Recommended)
   - Use the ⚙️ Settings button in the application
   - Test connections in real-time
   - Changes are saved automatically

### Ollama Setup

1. **Install Ollama**
   ```bash
   # Visit https://ollama.ai for installation instructions
   # Or use package managers:
   
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Pull Models**
   ```bash
   # Recommended models for prompt engineering
   ollama pull llama2          # General purpose
   ollama pull codellama       # Code-focused
   ollama pull mistral         # Fast and efficient
   ollama pull llama2:13b      # Larger model for better quality
   ```

## 📡 API Reference

### Prompt Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/prompts` | GET | List all prompts with optional search |
| `/api/prompts` | POST | Create a new prompt |
| `/api/prompts/{id}` | PUT | Update existing prompt |
| `/api/prompts/{id}` | DELETE | Delete prompt |

### AI Integration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/refine-prompt` | POST | Refine objective into system prompt |
| `/api/run-test` | POST | Test prompt with Ollama |
| `/api/models` | GET | Get available Ollama models |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health and status |
| `/api/config` | GET | Current configuration |
| `/api/system/info` | GET | System information |

### Library Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/export-library` | POST | Export all prompts to JSON format |
| `/api/import-library` | POST | Import prompt collection with conflict resolution |

### Configuration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Get current application configuration |
| `/api/config` | POST | Update configuration settings |

### Example API Usage

```javascript
// Create a new prompt
const response = await fetch('/api/prompts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Prompt',
    description: 'A helpful assistant',
    system_prompt: 'You are a helpful assistant...',
    model: 'llama2',
    temperature: 0.7
  })
});

// Test a prompt
const testResponse = await fetch('/api/run-test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    system_prompt: 'You are a helpful assistant...',
    user_input: 'Hello, how are you?',
    model: 'llama2',
    temperature: 0.7
  })
});
```

## 🗂️ Project Structure

```
promptlab/
├── 📁 backend/                 # Python backend
│   ├── 📁 api/                # REST API endpoints
│   │   ├── config.py          # Configuration API
│   │   ├── ollama.py          # Ollama integration API
│   │   └── prompts.py         # Prompt management API
│   ├── 📁 models/             # Database models
│   │   └── prompt.py          # Prompt data model
│   ├── 📁 services/           # Business logic
│   │   └── ollama_service.py  # Ollama communication service
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration management
│   └── database.py            # Database setup and utilities
├── 📁 frontend/               # Web frontend
│   ├── 📁 css/               # Stylesheets
│   │   └── styles.css        # Main application styles with dark mode support
│   ├── 📁 js/                # JavaScript modules
│   │   ├── 📁 components/    # UI components (LibraryPanel, WorkbenchPanel, TestChamberPanel, SettingsModal)
│   │   ├── 📁 controllers/   # Application controllers (AppController)
│   │   ├── 📁 services/      # API and service clients (ApiClient, ConfigService)
│   │   └── 📁 utils/         # Utility functions (ErrorHandler, ToastManager, LoadingManager, NotificationManager)
│   └── index.html            # Main application page
├── 📁 tests/                 # Test suite
│   ├── test_api_*.py         # API endpoint tests
│   ├── test_models.py        # Database model tests
│   └── test_*.py             # Additional test files
├── run.py                    # 🚀 Main startup script
├── requirements.txt          # Python dependencies
└── README.md                 # This documentation
```

## 🛠️ Development

### Running in Development Mode

```bash
# Enable debug mode
export FLASK_DEBUG=true
python run.py

# Or modify config directly
# Set flask_debug: true in configuration
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=backend tests/

# Run specific test file
pytest tests/test_api_prompts.py
```

### Database Management

```bash
# Database is created automatically
# Location: promptlab.db (configurable)

# Reset database (caution: deletes all data)
python -c "from backend.database import reset_database; reset_database()"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. **Port Already in Use**
```
Error: Port 5000 is already in use
```
**Solution:**
- Stop other applications using port 5000
- Or change the port: `export FLASK_PORT=8080`

#### 2. **Ollama Connection Failed**
```
⚠ Ollama connection failed: Connection refused
```
**Solutions:**
- Start Ollama: `ollama serve`
- Check endpoint in settings
- Verify firewall settings
- Try different port: `ollama serve --port 11435`

#### 3. **Python Version Error**
```
Error: Python 3.8 or higher is required
```
**Solution:**
- Install Python 3.8+ from [python.org](https://python.org)
- Use pyenv to manage versions: `pyenv install 3.11.0`

#### 4. **Dependencies Installation Failed**
```
❌ Failed to install dependencies
```
**Solutions:**
- Update pip: `python -m pip install --upgrade pip`
- Use virtual environment: `python -m venv venv`
- Install manually: `pip install -r requirements.txt`

#### 5. **Database Errors**
```
❌ Database initialization failed
```
**Solutions:**
- Check file permissions in project directory
- Delete `promptlab.db` and restart
- Ensure SQLite is available: `python -c "import sqlite3"`

#### 6. **Browser Doesn't Open**
```
⚠ Failed to open browser
```
**Solution:**
- Manually open: `http://localhost:5000`
- Check default browser settings
- Try different browser

#### 7. **Import/Export Issues**
```
❌ Import failed: Invalid format
```
**Solutions:**
- Ensure file is valid JSON format from PromptLab export
- Check for file corruption during transfer
- Use conflict resolution dialog for duplicate names
- Verify all required fields are present in import data

#### 8. **Dark Mode Not Persisting**
```
⚠ Theme resets on page reload
```
**Solution:**
- Check browser localStorage permissions
- Clear browser cache and try again
- Ensure JavaScript is enabled

### Getting Help

1. **Check Logs**: The startup script provides detailed logging
2. **Health Check**: Visit `/api/health` for system status
3. **System Info**: Visit `/api/system/info` for debugging details
4. **Reset Configuration**: Delete config files to restore defaults

### User Experience Features

**Smart Notifications:**
- **Toast Messages**: Non-intrusive notifications for all operations
- **Loading Indicators**: Visual feedback during AI operations and API calls
- **Error Handling**: Clear, actionable error messages with retry options
- **Success Confirmations**: Positive feedback for completed actions
- **Progress Tracking**: Real-time progress for import/export operations

**Data Protection:**
- **Unsaved Changes Warning**: Prevents accidental data loss
- **Conflict Resolution**: Smart handling of duplicate names during import
- **Auto-Save Detection**: Visual indicators when prompts have been modified
- **Backup Reminders**: Easy export functionality for data safety

### Performance Tips

- **Use SSD**: SQLite performs better on solid-state drives
- **Close Unused Models**: Ollama uses memory for loaded models
- **Adjust Temperature**: Lower values (0.1-0.3) for consistent results, higher (0.7-0.9) for creativity
- **Model Selection**: Smaller models (7B) are faster than larger ones (13B+)
- **Search Optimization**: Search is debounced for better performance with large libraries
- **Theme Performance**: Dark mode reduces eye strain during long editing sessions
- **Copy Operations**: Use the built-in copy buttons for reliable clipboard operations

## 📋 Example Prompts

### Code Review Assistant
```
**Objective:** Help developers review code for best practices

**Refined Prompt:**
You are an expert code reviewer with 10+ years of experience in software development. Your role is to provide constructive, actionable feedback on code submissions.

Guidelines:
- Focus on code quality, security, and maintainability
- Suggest specific improvements with examples
- Highlight both strengths and areas for improvement
- Consider performance implications
- Ensure adherence to coding standards
```

### Technical Writer
```
**Objective:** Create clear technical documentation

**Refined Prompt:**
You are a technical writing specialist who excels at making complex topics accessible. Your task is to create clear, comprehensive documentation.

Guidelines:
- Use simple, direct language
- Structure information logically
- Include practical examples
- Anticipate user questions
- Maintain consistency in terminology
```

### API Design Consultant
```
**Objective:** Design RESTful APIs following best practices

**Refined Prompt:**
You are an API design expert specializing in RESTful services. You help developers create well-structured, maintainable APIs.

Guidelines:
- Follow REST principles and HTTP standards
- Design intuitive resource hierarchies
- Recommend appropriate status codes
- Consider versioning strategies
- Address security and authentication
```

## 🤝 Contributing

PromptLab is designed to be extensible and welcomes contributions:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests
4. **Run the test suite**: `pytest`
5. **Submit a pull request**

### Development Setup

```bash
# Clone your fork
git clone <your-fork-url>
cd promptlab

# Create development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest

# Format code
black backend/ tests/

# Lint code
flake8 backend/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama Team** for the excellent local AI platform
- **Monaco Editor** for the powerful code editing experience
- **Flask Community** for the robust web framework
- **SQLAlchemy** for elegant database management

---

**Happy Prompt Engineering! 🚀**

For questions, issues, or feature requests, please use the project's issue tracker.