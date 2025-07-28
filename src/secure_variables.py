#!/usr/bin/env python3

"""
Secure Variables Manager for Prompt Manager
Handles encrypted storage and management of sensitive variables
"""

import os
import json
import getpass
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from secure_session import SecureSession, get_session_ttl_from_config
from secure_crypto import SecureCrypto


class SecureVariableManager:
    """Manages encrypted secure variables separately from regular variables"""
    
    def __init__(self, data_file: str = "prompts.json"):
        self.data_file = data_file  
        self.secure_data_file = data_file.replace('.json', '_secure.json')
        self.session = SecureSession(get_session_ttl_from_config())
        self.crypto = SecureCrypto()
        self.audit_log = []
        
    def _load_secure_data(self) -> Dict[str, Any]:
        """Load secure variables data file"""
        if os.path.exists(self.secure_data_file):
            try:
                with open(self.secure_data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            'secure_variables': {},
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
    
    def _save_secure_data(self, data: Dict[str, Any]):
        """Save secure variables data file with restricted permissions"""
        with open(self.secure_data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set restrictive permissions (600 - owner read/write only)
        os.chmod(self.secure_data_file, 0o600)
    
    def _get_password_hash(self) -> Optional[str]:
        """Get current session password hash"""
        session_data = self.session._get_session_data()
        if session_data:
            return session_data.get('password_hash')
        return None
    
    def _log_audit_event(self, action: str, variable_name: str, success: bool = True, 
                        details: str = None):
        """Log audit event for secure variable operations"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'variable_name': variable_name,
            'success': success,
            'user': os.getenv('USER', 'unknown'),
            'details': details
        }
        self.audit_log.append(event)
        
        # Keep only last 100 events in memory
        if len(self.audit_log) > 100:
            self.audit_log = self.audit_log[-100:]
    
    def add_secure_variable(self, name: str, description: str, value: str, 
                           default_value: str = None) -> bool:
        """Add a new secure variable with encryption"""
        # Require authentication
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                self._log_audit_event('add_secure_variable', name, False, 'Authentication failed')
                return False
        
        password_hash = self._get_password_hash()
        if not password_hash:
            self._log_audit_event('add_secure_variable', name, False, 'No password hash')
            return False
        
        try:
            # Load current secure data
            secure_data = self._load_secure_data()
            
            # Check if variable already exists
            if name in secure_data['secure_variables']:
                print(f"⚠️  Secure variable '{name}' already exists")
                overwrite = input("Overwrite? (y/N): ").strip().lower()
                if overwrite != 'y':
                    self._log_audit_event('add_secure_variable', name, False, 'User cancelled overwrite')
                    return False
            
            # Encrypt the value
            encrypted_value = self.crypto.encrypt(value, password_hash)
            
            # Create metadata
            metadata = self.crypto.create_encrypted_metadata(description, password_hash, default_value)
            
            # Store encrypted variable
            secure_data['secure_variables'][name] = {
                'encrypted_value': encrypted_value,
                **metadata
            }
            
            # Update last modified
            secure_data['metadata']['last_modified'] = datetime.now().isoformat()
            
            # Save to disk
            self._save_secure_data(secure_data)
            
            print(f"✅ Added secure variable '{name}'")
            self._log_audit_event('add_secure_variable', name, True)
            return True
            
        except Exception as e:
            print(f"❌ Failed to add secure variable: {e}")
            self._log_audit_event('add_secure_variable', name, False, str(e))
            return False
    
    def get_secure_variable(self, name: str) -> Optional[str]:
        """Get decrypted value of secure variable (runtime use only)"""
        # Require authentication
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                self._log_audit_event('get_secure_variable', name, False, 'Authentication failed')
                return None
        
        password_hash = self._get_password_hash()
        if not password_hash:
            return None
        
        try:
            secure_data = self._load_secure_data()
            
            if name not in secure_data['secure_variables']:
                return None
            
            var_data = secure_data['secure_variables'][name]
            
            # Decrypt the value
            decrypted_value = self.crypto.decrypt(var_data['encrypted_value'], password_hash)
            
            if decrypted_value is not None:
                # Update usage stats
                var_data['used_count'] = var_data.get('used_count', 0) + 1
                var_data['last_accessed'] = datetime.now().isoformat()
                
                # Save updated stats
                self._save_secure_data(secure_data)
                
                self._log_audit_event('get_secure_variable', name, True)
                return decrypted_value
            else:
                self._log_audit_event('get_secure_variable', name, False, 'Decryption failed')
                return None
                
        except Exception as e:
            self._log_audit_event('get_secure_variable', name, False, str(e))
            return None
    
    def list_secure_variables(self, show_values: bool = False) -> List[Dict[str, Any]]:
        """List all secure variables with metadata (values hidden by default)"""
        # Require authentication for listing
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                return []
        
        password_hash = self._get_password_hash()
        secure_data = self._load_secure_data()
        
        variables = []
        for name, var_data in secure_data['secure_variables'].items():
            # Decrypt metadata for display
            decrypted_metadata = self.crypto.decrypt_metadata(var_data, password_hash)
            
            var_info = {
                'name': name,
                'description': decrypted_metadata.get('description', '[ENCRYPTED]'),
                'is_secure': True,
                'created_at': var_data.get('created_at'),
                'used_count': var_data.get('used_count', 0),
                'last_accessed': var_data.get('last_accessed'),
                'has_default': 'encrypted_default' in var_data
            }
            
            # Only show actual values if explicitly requested (dangerous)
            if show_values and password_hash:
                decrypted_value = self.crypto.decrypt(var_data['encrypted_value'], password_hash)
                var_info['value'] = decrypted_value if decrypted_value else '[DECRYPT_FAILED]'
                var_info['default_value'] = decrypted_metadata.get('default_value', None)
            else:
                var_info['value'] = self.crypto.get_encrypted_value_placeholder()
                var_info['default_value'] = self.crypto.get_encrypted_value_placeholder() if var_info['has_default'] else None
            
            variables.append(var_info)
        
        self._log_audit_event('list_secure_variables', 'ALL', True, f'Listed {len(variables)} variables')
        return variables
    
    def update_secure_variable(self, name: str, description: str = None, 
                              value: str = None, default_value: str = None) -> bool:
        """Update a secure variable"""
        # Require authentication
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                return False
        
        password_hash = self._get_password_hash()
        if not password_hash:
            return False
        
        try:
            secure_data = self._load_secure_data()
            
            if name not in secure_data['secure_variables']:
                print(f"❌ Secure variable '{name}' not found")
                return False
            
            var_data = secure_data['secure_variables'][name]
            
            # Update description if provided
            if description:
                var_data['encrypted_description'] = self.crypto.encrypt(description, password_hash)
            
            # Update value if provided  
            if value:
                var_data['encrypted_value'] = self.crypto.encrypt(value, password_hash)
            
            # Update default value if provided
            if default_value is not None:
                if default_value:
                    var_data['encrypted_default'] = self.crypto.encrypt(default_value, password_hash)
                else:
                    # Remove default if empty string provided
                    var_data.pop('encrypted_default', None)
            
            # Update metadata
            var_data['last_modified'] = datetime.now().isoformat()
            secure_data['metadata']['last_modified'] = datetime.now().isoformat()
            
            self._save_secure_data(secure_data)
            
            print(f"✅ Updated secure variable '{name}'")
            self._log_audit_event('update_secure_variable', name, True)
            return True
            
        except Exception as e:
            print(f"❌ Failed to update secure variable: {e}")
            self._log_audit_event('update_secure_variable', name, False, str(e))
            return False
    
    def delete_secure_variable(self, name: str, force: bool = False) -> bool:
        """Delete a secure variable"""
        # Require authentication
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                return False
        
        try:
            secure_data = self._load_secure_data()
            
            if name not in secure_data['secure_variables']:
                print(f"❌ Secure variable '{name}' not found")
                return False
            
            # Confirm deletion unless forced
            if not force:
                print(f"⚠️  This will permanently delete secure variable '{name}'")
                confirm = input("Are you sure? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("Deletion cancelled")
                    return False
            
            # Remove the variable
            del secure_data['secure_variables'][name]
            secure_data['metadata']['last_modified'] = datetime.now().isoformat()
            
            self._save_secure_data(secure_data)
            
            print(f"✅ Deleted secure variable '{name}'")
            self._log_audit_event('delete_secure_variable', name, True)
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete secure variable: {e}")
            self._log_audit_event('delete_secure_variable', name, False, str(e))
            return False
    
    def get_variable_for_prompt(self, name: str) -> Optional[str]:
        """Get variable value for prompt rendering (checks both regular and secure)"""
        # First check if it's a secure variable
        secure_value = self.get_secure_variable(name)
        if secure_value is not None:
            return secure_value
        
        # If not secure, fall back to regular variable handling
        # (This would be handled by the main PromptManager)
        return None
    
    def export_secure_variables_encrypted(self, export_file: str) -> bool:
        """Export secure variables in encrypted format (for backup)"""
        if not self.session.is_authenticated():
            if not self.session.authenticate():
                return False
        
        try:
            secure_data = self._load_secure_data()
            
            # Add export metadata
            export_data = {
                **secure_data,
                'export_metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'exported_by': os.getenv('USER', 'unknown'),
                    'version': '1.0'
                }
            }
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            os.chmod(export_file, 0o600)
            
            print(f"✅ Exported secure variables to {export_file}")
            self._log_audit_event('export_secure_variables', 'ALL', True, f'Exported to {export_file}')
            return True
            
        except Exception as e:
            print(f"❌ Failed to export secure variables: {e}")
            self._log_audit_event('export_secure_variables', 'ALL', False, str(e))
            return False
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get audit log of secure variable operations"""
        return self.audit_log.copy()
    
    def print_audit_log(self, limit: int = 20):
        """Print recent audit log entries"""
        if not self.audit_log:
            print("No audit log entries")
            return
        
        print(f"\n📋 Recent Secure Variable Audit Log (last {limit} entries):")
        print("-" * 80)
        
        recent_logs = self.audit_log[-limit:] if len(self.audit_log) > limit else self.audit_log
        
        for entry in recent_logs:
            status = "✅" if entry['success'] else "❌"
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            action = entry['action']
            variable = entry['variable_name']
            
            print(f"{status} {timestamp} | {action:<20} | {variable}")
            if entry.get('details'):
                print(f"    Details: {entry['details']}")


def interactive_setup():
    """Interactive setup for secure variables"""
    print("🔐 Secure Variables Setup")
    print("=" * 50)
    
    svm = SecureVariableManager()
    
    # Test encryption capability
    capable, message = svm.crypto.verify_encryption_capability()
    print(f"Encryption: {message}")
    
    if not capable:
        print("❌ Cannot proceed without encryption capability")
        return False
    
    # Authenticate/setup
    if not svm.session.authenticate():
        print("❌ Authentication failed")
        return False
    
    print("✅ Secure variables are ready to use")
    
    # Show session info
    session_info = svm.session.get_session_info()
    if session_info:
        print(f"📅 Session expires in {session_info['time_remaining_minutes']} minutes")
    
    return True


if __name__ == "__main__":
    # Test secure variable manager
    print("Testing SecureVariableManager...")
    
    svm = SecureVariableManager("test_prompts.json")
    
    # Test adding a secure variable
    if svm.add_secure_variable("test_api_key", "Test API key", "secret_key_12345", "default_key"):
        print("✅ Added test secure variable")
        
        # Test listing
        variables = svm.list_secure_variables()
        print(f"Secure variables: {len(variables)}")
        for var in variables:
            print(f"  {var['name']}: {var['description']} (used: {var['used_count']})")
        
        # Test getting value
        value = svm.get_secure_variable("test_api_key")
        print(f"Retrieved value: {value}")
        
        # Test audit log
        svm.print_audit_log()
        
        # Cleanup
        svm.delete_secure_variable("test_api_key", force=True)
    
    print("Test completed")