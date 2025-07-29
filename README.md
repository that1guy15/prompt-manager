# 💡 Prompt Manager

**AI Prompt Management and Task-Master Integration System**

Intelligent prompt management with context-aware suggestions, multi-project support, and seamless browser integration. Designed for developers, content creators, and teams who work with AI assistants across multiple projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Chrome Extension](https://img.shields.io/badge/chrome-extension-green.svg)](https://developer.chrome.com/docs/extensions/)

## 🚀 **Features**

### **Intelligent Prompt Management**
- 📝 **Template System** - Variables, categories, and reusable prompts
- 🔐 **Secure Variables** - AES-256 encrypted storage for API keys and sensitive data
- 🧹 **Log Sanitization** - Intelligently filter repetitive patterns from verbose logs
- 🎯 **Context-Aware Suggestions** - Smart prompt recommendations based on current task
- 📊 **Usage Analytics** - Track prompt effectiveness and success rates
- 🔍 **Search & Filter** - Find prompts by category, tags, or content

### **Task-Master Integration**
- 🔗 **Multi-Project Support** - Manage multiple Task-Master projects
- 🤖 **Auto-Context Extraction** - Automatically fills PRD locations, requirements, success criteria
- 📂 **Project Registry** - Manual and automatic project discovery
- ⚡ **One-Command Context** - `pmcli` instantly copies perfect project context

### **Browser Extension**
- 🌐 **Cross-Platform** - Works on Claude.ai, ChatGPT, GitHub, Notion, Linear, Slack
- 💫 **Grammarly-Style Integration** - Unobtrusive suggestions when you need them
- 📱 **Visual Project Picker** - Choose projects with rich metadata
- ⌨️ **Keyboard Shortcuts** - Quick access with Ctrl+Shift+P

### **Security & Enterprise Ready**
- 🔐 **Military-Grade Encryption** - AES-256 encryption for sensitive variables
- 🔑 **Session Management** - Time-limited authentication with configurable TTL
- 📋 **Audit Logging** - Complete trail of all secure variable operations
- 🏢 **Enterprise Features** - Secure storage, access controls, and compliance ready

### **Developer-Friendly**
- 🛠️ **CLI Tools** - Full command-line interface for all features
- 🔌 **REST API** - Integrate with any tool or workflow
- 🎨 **Customizable** - Themes, settings, and extensible architecture
- 👥 **Team Support** - Shared prompts and project configurations

## 🚀 **Getting Started**

Transform your AI workflow in under 5 minutes! Choose your preferred setup method:

### **⚡ Express Setup (2 minutes)**
```bash
# 1. Clone and install
git clone https://github.com/your-username/promptManager.git
cd promptManager
make install

# 2. Start API server
prompt-api &

# 3. Add your first prompt
prompt-manager add --manual "Daily Standup" "Help me prepare for standup: 1) What I completed yesterday 2) What I'm working on today 3) Any blockers"

# 4. Use it instantly
prompt-manager copy 1  # ✅ Copied to clipboard!
```

### **📦 Complete Installation**

#### **🎯 Professional CLI Installation (Recommended)**
```bash
# Clone the repository
git clone https://github.com/your-username/promptManager.git
cd promptManager

# Production installation
make install

# Or development installation (includes dev tools)
make develop
```

**Available Commands After Installation:**
- `prompt-manager` (or short alias `pm`) - Main CLI interface
- `pmcli` - Task-Master integration
- `prompt-api` - API server
- `project-registry` - Project management

#### **📜 Legacy Script Installation**
```bash
# If you prefer the original script approach
pip install flask flask-cors requests numpy
chmod +x prompt_manager.py pmcli setup_integration.sh
./setup_integration.sh
```

#### **🌐 Chrome Browser Extension Installation**

**Step 1: Start API Server**
```bash
# Navigate to promptManager directory
cd promptManager

# Start the API server (keep this running)
python3 src/prompt_api.py
```

**Step 2: Install Extension in Chrome**
1. **Open Chrome Extensions**: Go to `chrome://extensions/`
2. **Enable Developer Mode**: Toggle switch in top-right corner
3. **Load Extension**: 
   - Click "Load unpacked" button
   - Navigate to and select: `promptManager/browser_extension/`
   - Click "Select Folder"
4. **Pin Extension**: Click puzzle piece icon → pin Prompt Manager

**Step 3: Configure Extension**
1. **Right-click extension icon** → "Options"
2. **Test Connection** - Should show ✅ if API server is running
3. **Add a project** using "Add Manually" button
4. **Enable desired settings** (auto-suggest, show widget, etc.)

**Step 4: Test It Out**
1. **Visit Claude.ai**
2. **Focus on text input** → See prompt suggestions appear! ✨
3. **Press Ctrl+Shift+P** → Quick access popup
4. **Click 📂** → Choose Task-Master project for context

### **🎯 First Steps**

#### **CLI Quick Start**
```bash
# Add your first prompt
prompt-manager add --manual "Code Review" "Review this code for security, performance, and best practices: {code}" -c development

# List your prompts
prompt-manager list

# Copy prompt with variables  
prompt-manager copy 1 -v code="function login() { return true; }"

# Get interactive help
prompt-manager help
```

#### **Task-Master Integration**
```bash
# Add your first project
project-registry add "My Project" ~/path/to/project

# Get instant project context
cd ~/path/to/project
pmcli  # ✅ Copies: PRD, requirements, tasks, git branch, success criteria
```

#### **Browser Magic**
1. **Visit any supported site** (Claude.ai, ChatGPT, GitHub, Notion, Linear, Slack)
2. **Focus text area** → Auto-suggestions appear
3. **Use shortcuts**: `Ctrl+Shift+P` for quick access
4. **Choose projects** with 📂 for context-aware prompts

## 🔐 **Secure Variables - Enterprise-Grade Security**

Store sensitive data like API keys, passwords, and tokens with military-grade security that rivals enterprise password managers.

### **🛡️ Security Architecture**

**Encryption Standards:**
- **AES-256 Encryption** - Same standard used by banks and government agencies
- **PBKDF2 Key Derivation** - 100,000 iterations to prevent brute-force attacks
- **System Keychain Integration** - Leverages macOS Keychain for password storage
- **Secure Memory Handling** - Values cleared immediately after use

**Access Control:**
- **Session-based Authentication** - Time-limited access (1-hour default)
- **Write-only Storage** - Values cannot be retrieved in plaintext after creation
- **Runtime-only Decryption** - Secrets only decrypted when actually used in prompts
- **Audit Trail** - Complete logging of all operations for compliance

### **🚀 Quick Start with Secure Variables**

```bash
# Add sensitive API key (interactive password prompt)
./pmcli svar add openai_key "OpenAI API Key"

# List all variables (secure ones marked with 🔒)
./pmcli var list

# Use in prompts (automatic authentication if needed)
./pmcli copy 1  # Secure variables automatically filled

# Session management
./pmcli svar session info    # Check authentication status
./pmcli svar session logout  # End session for security
```

### **🎯 Use Cases for Secure Variables**

**API Integration Prompts:**
```
Test the {endpoint} API:
Authorization: Bearer {api_token}  # ← Secure variable
Method: {method}
Expected: {expected_response}
```

**Database Operations:**
```
Connect to production database:
Host: {db_host}
Password: {db_password}  # ← Secure variable
Execute: {query}
```

**CI/CD Workflows:**
```
Deploy to {environment}:
GitHub Token: {github_token}  # ← Secure variable  
Docker Registry: {registry_token}  # ← Secure variable
Slack Webhook: {slack_webhook}  # ← Secure variable
```

### **🔒 Security Features Detail**

| Feature | Description | Security Level |
|---------|-------------|----------------|
| **Encryption** | AES-256-CBC with random IV/salt | Military Grade |
| **Key Derivation** | PBKDF2-SHA256, 100K iterations | Bank Standard |
| **Password Storage** | System keychain or encrypted file | Hardware Secured |
| **Session Management** | Configurable TTL with auto-expire | Enterprise Standard |
| **Audit Logging** | All operations logged with timestamps | Compliance Ready |
| **Memory Security** | Immediate cleanup after use | Government Standard |

### **📋 Complete Command Reference**

```bash
# Secure Variable Management
./pmcli svar add <name> "description"       # Add with password prompt
./pmcli svar list [--show-values]           # List (--show-values is DANGEROUS)
./pmcli svar update <name> [-d "desc"]      # Update description/value
./pmcli svar delete <name> [-f]             # Delete (force flag available)

# Session Management  
./pmcli svar session info                   # Show authentication status
./pmcli svar session logout                 # End secure session
./pmcli svar session extend                 # Extend session time

# Security & Compliance
./pmcli svar audit [-n 50]                  # View audit log
./pmcli svar export backup.json             # Export encrypted backup
```

**⚠️ Security Notes:**
- Passwords are **never stored** - only secure hashes
- Values are **write-only** after creation - cannot be retrieved in plaintext
- Sessions **auto-expire** after configured time (default: 1 hour)
- All operations are **audited** for security compliance

**📖 Complete Security Documentation:**
- [**Secure Variables Guide**](SECURE_VARIABLES.md) - User guide and quick reference
- [**Security Architecture**](docs/SECURITY_ARCHITECTURE.md) - Technical implementation details and compliance information

## 🧹 **Log Sanitization - Save Tokens & Time**

Clean up verbose logs before using them in AI prompts - automatically filters repetitive patterns while preserving important information.

### **Quick Example**
```bash
# Your clipboard has 500 lines of repetitive logs
./pmcli sanitize

✅ Sanitized content copied to clipboard!
   Reduced from 500 to 45 lines (91% reduction)
```

### **Key Features**
- **Intelligent Pattern Detection** - Finds similar lines even with slight variations
- **Smart Summarization** - Replaces repetitive blocks with concise summaries
- **Sensitive Data Warning** - Alerts you to potential API keys or passwords
- **Flexible I/O** - Works with clipboard, files, or piped input

### **Common Use Cases**
```bash
# Docker logs
docker-compose logs | ./pmcli sanitize

# Server logs with custom threshold
./pmcli sanitize -i server.log -t 0.8 -s

# Preview without modifying
./pmcli sanitize -p
```

**📖 [Full Log Sanitization Guide](LOG_SANITIZATION.md)** - Complete documentation with examples and best practices

## 📚 **Documentation**

### **Quick Access Help**
```bash
# CLI help - available anytime
prompt-manager help             # Interactive help system
pmcli --help               # Task-Master integration help
project-registry --help       # Project management help

# Start here
prompt-manager help quick-start # 5-minute tutorial
```

### **Complete Guides**
- 🎯 [**Quick Start Tutorial**](docs/QUICK_START.md) - Get up and running in 5 minutes
- 🔐 [**Secure Variables Guide**](SECURE_VARIABLES.md) - Enterprise security for sensitive data
- 🧹 [**Log Sanitization Guide**](LOG_SANITIZATION.md) - Clean up verbose logs for AI prompts
- 🎮 [**CLI Command Reference**](docs/CLI_USAGE.md) - Every command explained with examples
- 🌐 [**Browser Extension Guide**](docs/BROWSER_EXTENSION.md) - Installation, usage, and tips
- 🔧 [**Task-Master Integration**](docs/TASK_MASTER_INTEGRATION.md) - Project context automation

### **Advanced Topics**
- 📂 [**Multi-Project Management**](docs/MULTI_PROJECT_GUIDE.md) - Handle multiple projects like a pro
- 🎛️ [**Project Management**](docs/PROJECT_MANAGEMENT_GUIDE.md) - Manual project control and settings
- 🔒 [**Security Architecture**](docs/SECURITY_ARCHITECTURE.md) - Technical implementation, compliance, and threat model
- 🤖 [**API Reference**](docs/API_REFERENCE.md) - REST API for custom integrations
- ⚙️ [**Configuration Guide**](docs/CONFIGURATION.md) - Settings, environment variables, and customization

### **Examples & Tutorials**
- 💼 [**Team Workflows**](docs/examples/TEAM_WORKFLOWS.md) - Multi-user scenarios and best practices
- 🏢 [**Enterprise Setup**](docs/examples/ENTERPRISE.md) - Large organization deployment
- 🎨 [**Custom Integration**](docs/examples/CUSTOM_INTEGRATION.md) - Building your own integrations

## 🎯 **Use Cases**

### **For Individual Developers**
```bash
# Morning routine: Get project context instantly
cd ~/projects/my-app
pmcli  # Copies full project context for AI chat

# Code review: Use standardized review prompts
prompt-manager copy 1  # "Code Review Request" prompt

# Bug investigation: Context-aware debugging prompts
# Extension auto-suggests debugging prompts when "error" detected
```

### **For Teams**
```bash
# Team lead: Set up shared project contexts
project-registry add "Team Project" /shared/team-project
project-registry add "Client Work" /shared/client-work

# Developers: Consistent project context across team
pmcli  # Everyone gets same PRD locations, requirements, success criteria
```

### **For Content Creators**
- **Blog Writing**: Prompts for different article types and audiences  
- **Social Media**: Platform-specific content generation prompts
- **Documentation**: Technical writing and API documentation prompts
- **Marketing**: Campaign ideas, ad copy, and engagement prompts

## 🆘 **Getting Help**

### **Built-in Help System**
```bash
# Interactive help - start here!
prompt-manager help

# Available help topics:
prompt-manager help quick-start     # 5-minute getting started
prompt-manager help commands        # All CLI commands
prompt-manager help task-master     # Task-Master integration
prompt-manager help browser         # Browser extension setup
prompt-manager help examples        # Common use cases
prompt-manager help troubleshooting # Fix common issues
```

### **Browser Extension Help**
- **Right-click extension icon** → "Options" → "Help" tab
- **Built-in tutorials** and troubleshooting guides
- **Connection testing** and diagnostics
- **Visual setup wizards** for common tasks

### **Online Resources**
- 📖 **Full Documentation**: Browse the [docs/](docs/) directory
- 💬 **Issues**: [GitHub Issues](https://github.com/your-username/promptManager/issues)
- 🐛 **Bug Reports**: Use our issue templates
- 💡 **Feature Requests**: We love new ideas!

## 🏗️ **Project Structure**

```
promptManager/
├── 📄 README.md                 # You are here
├── 🔐 SECURE_VARIABLES.md       # Security documentation
├── 🔧 prompt_manager.py          # Core CLI tool
├── ⚡ pmcli                      # Task-Master integration + secure variables
├── 📁 src/
│   ├── 🌐 prompt_api.py         # REST API server
│   ├── 📂 project_registry.py   # Multi-project management
│   ├── 🔗 task_master_*.py      # Task-Master integration
│   ├── 🔐 secure_session.py     # Session management
│   ├── 🔐 secure_crypto.py      # AES-256 encryption
│   ├── 🔐 secure_variables.py   # Secure variable manager
│   ├── 🧹 log_sanitizer.py      # Log pattern filtering
│   └── 🧠 opus_reasoning.py     # AI-powered optimization
├── 🌐 browser_extension/        # Chrome/Firefox extension
│   ├── manifest.json
│   ├── content.js              # Page integration magic
│   ├── options.html            # Settings page
│   └── popup.html              # Extension popup
├── 📚 docs/                    # Complete documentation
│   ├── QUICK_START.md          # Start here
│   ├── CLI_USAGE.md            # Command reference
│   ├── BROWSER_EXTENSION.md    # Extension guide
│   ├── TASK_MASTER_INTEGRATION.md
│   ├── MULTI_PROJECT_GUIDE.md
│   ├── PROJECT_MANAGEMENT_GUIDE.md
│   └── examples/               # Real-world examples
├── 💾 prompts.json             # Your prompt database
├── 🔐 prompts_secure.json       # Encrypted secure variables (auto-created)
└── ⚙️ setup_integration.sh     # Easy setup script
```

## 🚀 **30-Second Demo**

### **CLI Power User**
```bash
# Setup takes 30 seconds
make install

# Add a project in 5 seconds  
project-registry add "My Project" ~/projects/my-app

# Get perfect AI context in 1 command
pmcli
# ✅ Copies: PRD location, requirements, success criteria, current task, git branch

# Paste into Claude Code → Perfect context every time! 
```

### **Browser Extension Magic**
1. **Install extension** (2 clicks)
2. **Visit Claude.ai**
3. **Focus text area** → See prompt suggestions appear 💫
4. **Click 📂** → Choose your project
5. **Click suggestion** → Perfect prompt with full project context!

**Just like Grammarly, but for AI prompts!**

## 🎛️ **Key Commands**

### **Essential CLI Commands**
```bash
# Prompt Management
prompt-manager help                         # Interactive help system
prompt-manager add --manual "Title" "Content"  # Add prompt
prompt-manager list                         # List all prompts
prompt-manager copy 1                       # Copy prompt to clipboard

# Secure Variables (NEW!)
pmcli svar add api_key "API Key Description"   # Add secure variable
pmcli svar list                             # List secure variables (🔒 marked)
pmcli var list                              # List all variables (regular + secure)
pmcli svar session info                     # Check authentication status

# Log Sanitization (NEW!)
pmcli sanitize                              # Clean clipboard logs (removes repetition)
pmcli sanitize -i app.log -o clean.log      # Sanitize log file
pmcli sanitize -p -s                        # Preview with statistics

# Task-Master Integration  
pmcli                                   # Auto-detect project and copy context
pmcli --list-projects                   # Show available projects
pmcli --select-project                  # Choose project interactively

# Project Management
project-registry add "Name" /path          # Add project manually
project-registry list                      # List all projects
project-registry disable project-id        # Hide project temporarily

# API Server
prompt-api                                  # Start REST API for browser extension
```

### **Browser Extension**
- **Ctrl+Shift+P** - Quick access popup
- **Click 📂** - Choose project for Task-Master prompts
- **Right-click icon** → "Options" - Full settings and project management

## 🤝 **Contributing**

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `python -m pytest`
5. **Submit a pull request**

### **Development Setup**
```bash
# Install in development mode with all dev tools
make develop

# Run tests
make test

# Format code
make format

# Start development API server
prompt-api --debug

# Load extension in Chrome developer mode
# Point to browser_extension/ directory
```

## 📈 **Roadmap**

### **v1.1 - AI Enhancement** 
- [ ] Opus-powered prompt optimization
- [ ] Success rate learning and improvement  
- [ ] Automatic prompt generation from usage patterns

### **v1.2 - Team Features**
- [ ] Shared prompt libraries
- [ ] Team analytics and insights
- [ ] Role-based access control

### **v1.3 - Platform Expansion**
- [ ] VS Code extension
- [ ] Slack bot integration
- [ ] API webhooks and automation

### **v2.0 - Enterprise**
- [ ] SSO authentication
- [ ] Audit logs and compliance
- [ ] Advanced analytics dashboard

## 🔧 **Configuration**

### **Backend URL Configuration**

**CLI Tools** - Configure via environment variable or command-line flag:
```bash
# Environment variable (recommended)
export PROMPT_API_URL="http://localhost:5000/api"

# Or use command-line flag for individual commands
prompt-manager --api-url "http://your-server:5000/api" list
pmcli --api-url "http://your-server:5000/api"
```

**Browser Extension** - Configure via options page:
1. Right-click extension icon → "Options"
2. Update "API URL" field 
3. Click "Test Connection" to verify

### **Environment Variables**
```bash
# API Configuration
export PROMPT_API_URL="http://localhost:5000/api"
export PROMPT_MANAGER_DIR="/path/to/promptManager"

# Secure Variables Configuration
export PM_SECURE_SESSION_TTL=60              # Session timeout in minutes
export PM_SECURE_ENCRYPTION_BACKEND="auto"   # Encryption backend preference

# Task-Master Integration  
export TASK_MASTER_DIR="/path/to/task-master"

# AI Service Keys (DEPRECATED - Use Secure Variables Instead!)
# Migrate these to secure variables for better security:
# ./pmcli svar add anthropic_api_key "Anthropic API Key"
# ./pmcli svar add openrouter_api_key "OpenRouter API Key"
export ANTHROPIC_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"
```

### **Shell Integration**
```bash
# Add to ~/.bashrc or ~/.zshrc for power-user shortcuts
source ~/promptManager/src/claude_integration.sh

# Quick commands now available:
# pms - prompt suggest     pmu - prompt use  
# pml - prompt list       pmf - prompt find
# tm  - task-master prompt
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Inspired by tools like Grammarly for seamless user experience
- Built for the Claude Code and Task-Master workflow
- Thanks to the open-source community for the amazing libraries

---

## 🎉 **Ready to Supercharge Your AI Workflow?**

### **Next Steps:**
1. 🚀 **[Quick Start](docs/QUICK_START.md)** - Get running in 5 minutes
2. 🎮 **Try the CLI**: `prompt-manager help quick-start`
3. 🌐 **Install Browser Extension** - Like Grammarly for AI prompts
4. 📚 **Explore [Full Documentation](docs/)** - Become a power user

**Join thousands of developers, writers, and teams who use Prompt Manager to work smarter with AI.**

[🚀 **Get Started Now**](docs/QUICK_START.md) | [📖 **Full Docs**](docs/) | [🌐 **Browser Extension**](browser_extension/) | [💻 **API Reference**](docs/API_REFERENCE.md)