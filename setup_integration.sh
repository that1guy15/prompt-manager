#!/bin/bash

# Setup script for Prompt Manager integrations

echo "🚀 Setting up Prompt Manager integrations..."

# Make scripts executable
chmod +x prompt_manager.py
chmod +x src/interactive_cli.py
chmod +x src/task_master_plugin.py
chmod +x src/claude_integration.sh

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install flask flask-cors requests numpy

# Source shell integration
echo "🐚 Setting up shell integration..."
echo "" >> ~/.bashrc
echo "# Prompt Manager Integration" >> ~/.bashrc
echo "source $(pwd)/src/claude_integration.sh" >> ~/.bashrc

echo "" >> ~/.zshrc
echo "# Prompt Manager Integration" >> ~/.zshrc
echo "source $(pwd)/src/claude_integration.sh" >> ~/.zshrc

# Create systemd service for API (optional)
if command -v systemctl &> /dev/null; then
    echo "🔧 Creating systemd service..."
    cat > prompt-manager-api.service <<EOF
[Unit]
Description=Prompt Manager API Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/src/prompt_api.py
Restart=on-failure
Environment="PROMPT_MANAGER_DIR=$(pwd)"

[Install]
WantedBy=multi-user.target
EOF
    
    echo "To install as system service, run:"
    echo "sudo cp prompt-manager-api.service /etc/systemd/system/"
    echo "sudo systemctl enable prompt-manager-api"
    echo "sudo systemctl start prompt-manager-api"
fi

# Create launch script
cat > launch_prompt_manager.sh <<'EOF'
#!/bin/bash

# Launch Prompt Manager components

# Start API server in background
echo "🌐 Starting API server..."
python3 src/prompt_api.py &
API_PID=$!

# Give API time to start
sleep 2

# Launch interactive CLI
echo "💻 Launching interactive CLI..."
python3 src/interactive_cli.py

# Cleanup on exit
trap "kill $API_PID 2>/dev/null" EXIT
EOF

chmod +x launch_prompt_manager.sh

# Create example .env file
if [ ! -f .env ]; then
    cat > .env <<EOF
# Prompt Manager Configuration

# API Keys (optional - for Opus reasoning engine)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Task-Master Integration
TASK_MASTER_DIR=/path/to/task-master

# API Configuration
PROMPT_API_URL=http://localhost:5000/api
EOF
    echo "📝 Created .env file - please add your API keys"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Quick Start:"
echo "1. Add your API keys to .env file (optional, for Opus integration)"
echo "2. Source your shell config: source ~/.bashrc (or ~/.zshrc)"
echo "3. Launch interactive mode: ./launch_prompt_manager.sh"
echo "4. Or use shell commands: pms, pmu, pml, pmf"
echo ""
echo "📚 Integration Options:"
echo "- Interactive CLI: ./src/interactive_cli.py"
echo "- Task-Master Plugin: ./src/task_master_plugin.py"
echo "- API Server: python3 src/prompt_api.py"
echo "- Shell Functions: source src/claude_integration.sh"