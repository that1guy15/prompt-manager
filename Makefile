# Prompt Manager - Professional AI Prompt Management CLI
# 
# Usage:
#   make install     - Install in production mode
#   make develop     - Install in development mode
#   make uninstall   - Uninstall the package
#   make clean       - Clean build artifacts
#   make test        - Run tests
#   make lint        - Run linting

SHELL := /bin/bash
PYTHON := python3
PIP := $(PYTHON) -m pip

.PHONY: help install develop uninstall clean test lint format build upload

# Default target
help:
	@echo "🧶 Prompt Manager - AI Prompt Management CLI"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install in production mode"
	@echo "  make develop     - Install in development mode with editable install"
	@echo "  make uninstall   - Uninstall the package"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make test        - Run tests (requires dev dependencies)"
	@echo "  make lint        - Run linting (requires dev dependencies)"
	@echo "  make format      - Format code with black"
	@echo "  make build       - Build distribution packages"
	@echo "  make check       - Check package integrity"
	@echo ""
	@echo "Quick setup:"
	@echo "  make develop     # Install for development"
	@echo "  prompt-manager   # Test the CLI"
	@echo "  prompt-api       # Start the API server"

# Production installation
install: clean
	@echo "🔧 Installing Prompt Manager..."
	$(PIP) install -r requirements.txt
	$(PIP) install .
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Available commands:"
	@echo "  prompt-manager   - Main CLI (also available as 'pm')"
	@echo "  pmcli        - Task-Master integration"
	@echo "  prompt-api       - API server"
	@echo "  project-registry - Project management"

# Development installation
develop: clean
	@echo "🔧 Installing Prompt Manager in development mode..."
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"
	@echo "✅ Development installation complete!"
	@echo ""
	@echo "Available commands:"
	@echo "  prompt-manager   - Main CLI (also available as 'pm')"
	@echo "  pmcli        - Task-Master integration"
	@echo "  prompt-api       - API server"
	@echo "  project-registry - Project management"
	@echo ""
	@echo "Development tools:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"

# Uninstall
uninstall:
	@echo "🗑️  Uninstalling Prompt Manager..."
	$(PIP) uninstall prompt-manager -y || true
	@echo "✅ Uninstalled successfully!"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf prompt_manager.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Cleaned!"

# Run tests
test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "✅ Tests completed!"

# Run linting
lint:
	@echo "🔍 Running linters..."
	@echo "Running flake8..."
	$(PYTHON) -m flake8 prompt_manager/ --max-line-length=100 --ignore=E501,W503
	@echo "Running mypy..."
	$(PYTHON) -m mypy prompt_manager/ --ignore-missing-imports
	@echo "✅ Linting completed!"

# Format code
format:
	@echo "🎨 Formatting code with black..."
	$(PYTHON) -m black prompt_manager/ --line-length=100
	@echo "✅ Code formatted!"

# Build distribution packages
build: clean
	@echo "📦 Building distribution packages..."
	$(PYTHON) -m build
	@echo "✅ Build completed!"

# Check package integrity
check: build
	@echo "🔍 Checking package integrity..."
	$(PYTHON) -m twine check dist/*
	@echo "✅ Package check completed!"

# Install from local build
install-local: build
	@echo "🔧 Installing from local build..."
	$(PIP) install dist/*.whl --force-reinstall
	@echo "✅ Local installation complete!"

# Quick development setup
quick-setup: develop
	@echo ""
	@echo "🎉 Quick setup complete!"
	@echo ""
	@echo "Try these commands:"
	@echo "  prompt-manager help"
	@echo "  prompt-api --help"
	@echo "  pmcli --help"

# Create example configuration
example-config:
	@echo "📝 Creating example configuration..."
	@mkdir -p ~/.config/prompt-manager
	@echo "# Prompt Manager Configuration" > ~/.config/prompt-manager/config.yaml
	@echo "api_url: http://localhost:5000/api" >> ~/.config/prompt-manager/config.yaml
	@echo "auto_discovery: true" >> ~/.config/prompt-manager/config.yaml
	@echo "✅ Example config created at ~/.config/prompt-manager/config.yaml"

# System-wide installation (requires sudo)
install-system: 
	@echo "🔧 Installing system-wide (requires sudo)..."
	sudo $(PIP) install -r requirements.txt
	sudo $(PIP) install .
	@echo "✅ System-wide installation complete!"

# Development tools setup
dev-tools:
	@echo "🛠️  Setting up development tools..."
	$(PIP) install black flake8 mypy pytest build twine
	@echo "✅ Development tools installed!"

# Show package info
info:
	@echo "📋 Package Information:"
	@echo "Name: prompt-manager"
	@echo "Version: 1.0.0"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo ""
	@$(PIP) show prompt-manager || echo "Package not installed"