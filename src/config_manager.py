#!/usr/bin/env python3
"""
Configuration Manager for Prompt Manager
Handles provider settings, API keys, and model selection
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import getpass

class ConfigManager:
    """Manages configuration for API providers and settings"""
    
    SUPPORTED_PROVIDERS = {
        'anthropic': {
            'name': 'Anthropic',
            'api_key_env': 'ANTHROPIC_API_KEY',
            'models': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
                'claude-2.1',
                'claude-2.0'
            ],
            'default_model': 'claude-3-opus-20240229',
            'base_url': 'https://api.anthropic.com/v1'
        },
        'openrouter': {
            'name': 'OpenRouter',
            'api_key_env': 'OPENROUTER_API_KEY',
            'models': [
                'anthropic/claude-3-opus',
                'anthropic/claude-3-sonnet',
                'anthropic/claude-2.1',
                'openai/gpt-4-turbo-preview',
                'google/gemini-pro',
                'meta-llama/llama-2-70b-chat'
            ],
            'default_model': 'anthropic/claude-3-opus',
            'base_url': 'https://openrouter.ai/api/v1'
        },
        'requesty': {
            'name': 'Requesty',
            'api_key_env': 'REQUESTY_API_KEY',
            'models': [
                'claude-3-opus',
                'claude-3-sonnet',
                'gpt-4-turbo',
                'gpt-3.5-turbo'
            ],
            'default_model': 'claude-3-opus',
            'base_url': 'https://api.requesty.ai/v1'
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize config manager with optional custom config directory"""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.prompt_manager'
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Return default config
        return {
            'provider': None,
            'api_keys': {},
            'models': {},
            'settings': {
                'auto_save': True,
                'verify_ssl': True
            }
        }
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_wizard(self):
        """Interactive setup wizard for first-time configuration"""
        print("\n🚀 Welcome to Prompt Manager Setup!")
        print("=" * 50)
        
        # Provider selection
        print("\n📡 Select your AI provider:")
        providers = list(self.SUPPORTED_PROVIDERS.keys())
        for i, provider in enumerate(providers, 1):
            print(f"{i}. {self.SUPPORTED_PROVIDERS[provider]['name']}")
        
        while True:
            try:
                choice = input(f"\nSelect provider [1-{len(providers)}]: ").strip()
                provider_idx = int(choice) - 1
                if 0 <= provider_idx < len(providers):
                    selected_provider = providers[provider_idx]
                    break
                print("❌ Invalid selection. Please try again.")
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Setup cancelled.")
                return False
        
        self.config['provider'] = selected_provider
        provider_info = self.SUPPORTED_PROVIDERS[selected_provider]
        
        # API key configuration
        print(f"\n🔑 {provider_info['name']} API Key Configuration")
        print(f"You can get your API key from: {self._get_api_key_url(selected_provider)}")
        
        # Check if API key exists in environment
        env_key = os.environ.get(provider_info['api_key_env'])
        if env_key:
            print(f"✅ Found existing API key in environment variable: {provider_info['api_key_env']}")
            use_env = input("Use this key? (Y/n): ").strip().lower()
            if use_env != 'n':
                self.config['api_keys'][selected_provider] = 'env'
            else:
                api_key = getpass.getpass("Enter API key: ")
                self.config['api_keys'][selected_provider] = api_key
        else:
            api_key = getpass.getpass("Enter API key: ")
            self.config['api_keys'][selected_provider] = api_key
        
        # Model selection
        print(f"\n🤖 Select default model for {provider_info['name']}:")
        models = provider_info['models']
        for i, model in enumerate(models, 1):
            default = " (default)" if model == provider_info['default_model'] else ""
            print(f"{i}. {model}{default}")
        
        while True:
            try:
                choice = input(f"\nSelect model [1-{len(models)}] or press Enter for default: ").strip()
                if not choice:
                    selected_model = provider_info['default_model']
                    break
                model_idx = int(choice) - 1
                if 0 <= model_idx < len(models):
                    selected_model = models[model_idx]
                    break
                print("❌ Invalid selection. Please try again.")
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
        
        self.config['models'][selected_provider] = selected_model
        
        # Save configuration
        self._save_config()
        
        # Test the configuration
        print("\n🔍 Testing provider connection...")
        if self._test_provider_connection():
            print("✅ Provider connection successful!")
        else:
            print("⚠️  Provider test failed. Please check your API key.")
            print("You can update it with: pmcli config set --api-key <key>")
        
        print(f"\n📁 Configuration saved to: {self.config_file}")
        
        # Show recommended commands
        self._show_quick_start_commands()
        
        return True
    
    def _test_provider_connection(self) -> bool:
        """Test the provider connection with a simple request"""
        try:
            # Simple test - just check if we can make a basic call
            provider = self.get_current_provider()
            api_key = self.get_api_key(provider)
            
            if not provider or not api_key:
                return False
            
            # Quick validation based on provider
            if provider == 'anthropic':
                # Check if API key format looks valid
                return api_key.startswith('sk-ant-')
            elif provider == 'openrouter':
                # OpenRouter keys are typically longer
                return len(api_key) > 20
            elif provider == 'requesty':
                # Requesty key validation
                return len(api_key) > 10
                
            return True
        except:
            return False
    
    def _show_quick_start_commands(self):
        """Show recommended commands after setup"""
        print("\n🚀 Quick Start - Top Commands:")
        print("=" * 50)
        print("\n1️⃣  List available prompts:")
        print("   pmcli list\n")
        print("2️⃣  Get project context for AI chat:")
        print("   pmcli  # Auto-detects current project\n")
        print("3️⃣  Add a new prompt:")
        print("   pmcli add --manual \"Title\" \"Prompt content with {variables}\"\n")
        print("\n💡 For more commands: pmcli --help")
        print("📖 Full documentation: https://github.com/your-username/promptManager")
    
    def _get_api_key_url(self, provider: str) -> str:
        """Get URL for obtaining API keys"""
        urls = {
            'anthropic': 'https://console.anthropic.com/account/keys',
            'openrouter': 'https://openrouter.ai/keys',
            'requesty': 'https://requesty.ai/dashboard/keys'
        }
        return urls.get(provider, 'provider website')
    
    def get_current_provider(self) -> Optional[str]:
        """Get the currently configured provider"""
        return self.config.get('provider')
    
    def get_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Get API key for provider"""
        if not provider:
            provider = self.get_current_provider()
        
        if not provider:
            return None
        
        key_value = self.config.get('api_keys', {}).get(provider)
        
        # If key is 'env', get from environment
        if key_value == 'env':
            provider_info = self.SUPPORTED_PROVIDERS.get(provider, {})
            return os.environ.get(provider_info.get('api_key_env'))
        
        # Use secure variables if available
        if not key_value:
            try:
                from secure_variables import SecureVariableManager
                svm = SecureVariableManager()
                secure_key = f"{provider}_api_key"
                return svm.get_secure_variable(secure_key)
            except:
                pass
        
        return key_value
    
    def get_model(self, provider: Optional[str] = None) -> Optional[str]:
        """Get selected model for provider"""
        if not provider:
            provider = self.get_current_provider()
        
        if not provider:
            return None
        
        return self.config.get('models', {}).get(
            provider,
            self.SUPPORTED_PROVIDERS[provider]['default_model']
        )
    
    def update_provider(self, provider: str, api_key: Optional[str] = None, model: Optional[str] = None):
        """Update provider configuration"""
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.config['provider'] = provider
        
        if api_key is not None:
            if 'api_keys' not in self.config:
                self.config['api_keys'] = {}
            self.config['api_keys'][provider] = api_key
        
        if model is not None:
            if 'models' not in self.config:
                self.config['models'] = {}
            self.config['models'][provider] = model
        
        self._save_config()
    
    def get_provider_info(self, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get full provider information"""
        if not provider:
            provider = self.get_current_provider()
        
        if not provider:
            return None
        
        info = self.SUPPORTED_PROVIDERS.get(provider, {}).copy()
        info['api_key'] = self.get_api_key(provider)
        info['selected_model'] = self.get_model(provider)
        return info
    
    def is_configured(self) -> bool:
        """Check if configuration is complete"""
        provider = self.get_current_provider()
        if not provider:
            return False
        
        api_key = self.get_api_key(provider)
        return bool(api_key)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return {
            'provider': self.get_current_provider(),
            'model': self.get_model(),
            'configured': self.is_configured(),
            'config_file': str(self.config_file),
            'providers': list(self.SUPPORTED_PROVIDERS.keys())
        }
    
    def export_config(self, include_keys: bool = False) -> Dict[str, Any]:
        """Export configuration (optionally without sensitive data)"""
        config_copy = self.config.copy()
        
        if not include_keys and 'api_keys' in config_copy:
            # Replace actual keys with masked versions
            config_copy['api_keys'] = {
                k: '***' if v != 'env' else 'env'
                for k, v in config_copy['api_keys'].items()
            }
        
        return config_copy