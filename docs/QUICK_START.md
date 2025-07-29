# 🚀 Quick Start Guide

**Get up and running with Prompt Manager in 5 minutes!**

## 🎯 **What You'll Learn**
- Basic prompt management
- Task-Master project integration  
- Browser extension setup
- Essential daily workflows

## 📦 **Step 1: Installation (2 minutes)**

```bash
# Clone and enter directory
git clone https://github.com/your-username/promptManager.git
cd promptManager

# Install Python dependencies
pip install flask flask-cors requests numpy

# Make CLI tools executable
chmod +x prompt_manager.py pmcli setup_integration.sh

# Quick setup (optional - adds shell shortcuts)
./setup_integration.sh
```

## 💡 **Step 2: Your First Prompt (1 minute)**

```bash
# Add a prompt for daily standups
./prompt_manager.py add --manual "Daily Standup" "Help me prepare for standup: 1) What I completed yesterday 2) What I'm working on today 3) Any blockers" -c productivity

# Use it immediately
./prompt_manager.py copy 1
# ✅ Copied to clipboard - paste into Claude, ChatGPT, etc.
```

## 🔧 **Step 3: Task-Master Integration (1 minute)**

```bash
# Add your first project (replace with your actual project path)
python3 src/project_registry.py add "My Project" ~/projects/my-app

# Get instant project context
cd ~/projects/my-app
pmcli
# ✅ Copies full project context: PRD, requirements, current task, git branch
```

## 🌐 **Step 4: Browser Extension (1 minute)**

```bash
# Start the API server (keep this running)
python3 src/prompt_api.py &

# Then in Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"  
# 3. Click "Load unpacked" → select browser_extension/ folder
# 4. Visit Claude.ai → See prompt suggestions appear! ✨
```

## 🎮 **Essential Daily Workflows**

### **Morning Project Setup**
```bash
# Get perfect project context for AI conversations
cd ~/your-project
pmcli  # Instant context with PRD, requirements, tasks

# Paste into Claude Code → Perfect context every time!
```

### **Quick Prompt Access**
```bash
# List your prompts
./prompt_manager.py list

# Copy any prompt by ID
./prompt_manager.py copy 2

# Search for specific prompts
./prompt_manager.py list -s "code review"
```

### **Browser Magic**
1. **Visit Claude.ai, ChatGPT, or GitHub**
2. **Focus on text area** → See prompt suggestions
3. **Press Ctrl+Shift+P** → Quick access popup
4. **Click 📂** → Choose Task-Master project
5. **Click suggestion** → Perfect prompt with context!

## 🎯 **Common Use Cases**

### **Code Review**
```bash
# Add code review prompt
./prompt_manager.py add --manual "Code Review" "Review this code for: security, performance, best practices. Code: {code}" -c development

# Use with specific code
./prompt_manager.py copy 1 -v code="function login(user, pass) { return user === 'admin'; }"
```

### **Bug Investigation**
```bash
# Add debugging prompt
./prompt_manager.py add --manual "Debug Issue" "Help debug this issue: {description}. Error: {error}. Environment: {env}" -c debugging

# Use it
./prompt_manager.py copy 2 -v description="Login fails" error="TypeError: undefined" env="production"
```

### **Team Standup**
```bash
# Your standup prompt from Step 2
./prompt_manager.py copy 1
# Paste in Claude → Get structured standup talking points
```

## 🆘 **Need Help?**

### **Built-in Help**
```bash
./prompt_manager.py help           # Interactive help system
./prompt_manager.py help commands  # All CLI commands
pmcli --help                 # Task-Master integration help
```

### **Common Issues**

**"Command not found"**
```bash
# Make sure files are executable
chmod +x prompt_manager.py tm-prompt
```

**"No projects found"**
```bash
# Add a project manually
python3 src/project_registry.py add "My Project" /path/to/project
```

**"Browser extension not working"**
```bash
# Make sure API server is running
python3 src/prompt_api.py

# Check extension permissions in Chrome settings
```

## 🚀 **Next Steps**

### **Become a Power User**
- 📖 **[CLI Usage Guide](CLI_USAGE.md)** - Master all commands
- 🔧 **[Task-Master Integration](TASK_MASTER_INTEGRATION.md)** - Deep project integration
- 🌐 **[Browser Extension Guide](BROWSER_EXTENSION.md)** - Advanced browser features

### **Advanced Workflows**
- 📂 **[Multi-Project Management](MULTI_PROJECT_GUIDE.md)** - Handle multiple projects
- 🎛️ **[Project Management](PROJECT_MANAGEMENT_GUIDE.md)** - Manual project control
- 👥 **[Team Workflows](examples/TEAM_WORKFLOWS.md)** - Team collaboration

## 📊 **What You've Accomplished**

✅ **Installed Prompt Manager** - Core system ready  
✅ **Created your first prompt** - Daily workflow tool  
✅ **Set up Task-Master integration** - Project context automation  
✅ **Installed browser extension** - Cross-platform AI assistance  
✅ **Learned essential commands** - Daily productivity boost  

**🎉 You're now ready to work smarter with AI!**

---

**Pro Tip**: Run `./prompt_manager.py help` anytime for interactive guidance and discover more features as you go!

[⬅️ Back to README](../README.md) | [➡️ CLI Usage Guide](CLI_USAGE.md)