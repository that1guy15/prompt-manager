#!/usr/bin/env python3

"""
Secure Session Manager for Prompt Manager
Handles authentication sessions with configurable TTL for secure variables
"""

import os
import json
import time
import getpass
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path


class SecureSession:
    """Manages secure authentication sessions for sensitive variables"""
    
    def __init__(self, session_ttl_minutes: int = 60):
        self.session_ttl_minutes = session_ttl_minutes
        self.session_file = os.path.join(tempfile.gettempdir(), '.pm_secure_session')
        self.max_attempts = 3
        
    def _get_session_data(self) -> Optional[Dict[str, Any]]:
        """Get current session data if exists and valid"""
        try:
            if not os.path.exists(self.session_file):
                return None
                
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                
            # Check if session has expired
            expires_at = datetime.fromisoformat(data.get('expires_at', ''))
            if datetime.now() > expires_at:
                # Clean up expired session
                os.remove(self.session_file)
                return None
                
            return data
            
        except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
            # Clean up corrupted session file
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return None
    
    def _create_session(self, password_hash: str) -> Dict[str, Any]:
        """Create a new secure session"""
        expires_at = datetime.now() + timedelta(minutes=self.session_ttl_minutes)
        session_data = {
            'password_hash': password_hash,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'access_count': 0
        }
        
        # Write session to temp file with restricted permissions
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Set file permissions to owner-only (600)
        os.chmod(self.session_file, 0o600)
        
        return session_data
    
    def _prompt_for_password(self, is_setup: bool = False) -> str:
        """Prompt user for secure variables password"""
        if is_setup:
            print("🔐 Set up secure variables protection")
            print("This password will be required to access sensitive variables.")
            print("Choose a strong password - it won't be stored anywhere.")
            password = getpass.getpass("Enter password for secure variables: ")
            confirm = getpass.getpass("Confirm password: ")
            
            if password != confirm:
                print("❌ Passwords don't match")
                return ""
            
            if len(password) < 8:
                print("❌ Password must be at least 8 characters")
                return ""
                
            return password
        else:
            print("🔐 Authentication required for secure variables")
            return getpass.getpass("Enter password: ")
    
    def _hash_password(self, password: str) -> str:
        """Create secure hash of password"""
        # Use a simple salt based on username and system
        salt = f"{os.getenv('USER', 'default')}_{os.uname().nodename}".encode()
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()
    
    def authenticate(self, force_new: bool = False) -> bool:
        """Authenticate user for secure variables access"""
        # Check for existing valid session
        if not force_new:
            session_data = self._get_session_data()
            if session_data:
                # Update access count
                session_data['access_count'] += 1
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f)
                return True
        
        # Need to authenticate
        # Check if this is first time setup (no keychain entry)
        stored_hash = self._get_stored_password_hash()
        is_setup = stored_hash is None
        
        attempts = 0
        while attempts < self.max_attempts:
            password = self._prompt_for_password(is_setup)
            
            if not password:
                attempts += 1
                continue
                
            password_hash = self._hash_password(password)
            
            if is_setup:
                # First time setup - store hash and create session
                if self._store_password_hash(password_hash):
                    self._create_session(password_hash)
                    print("✅ Secure variables protection enabled")
                    return True
                else:
                    print("❌ Failed to store password securely")
                    return False
            else:
                # Verify against stored hash
                if password_hash == stored_hash:
                    self._create_session(password_hash)
                    print("✅ Authentication successful")
                    return True
                else:
                    attempts += 1
                    print(f"❌ Invalid password ({self.max_attempts - attempts} attempts remaining)")
        
        print("❌ Authentication failed - too many attempts")
        return False
    
    def _get_stored_password_hash(self) -> Optional[str]:
        """Get stored password hash from secure location"""
        # Try to get from macOS keychain first
        if os.system("which security > /dev/null 2>&1") == 0:
            try:
                result = os.popen(
                    "security find-generic-password -s 'prompt-manager-secure' -w 2>/dev/null"
                ).read().strip()
                return result if result else None
            except:
                pass
        
        # Fallback to encrypted file in user's home directory
        hash_file = os.path.expanduser("~/.pm_secure_hash")
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        
        return None
    
    def _store_password_hash(self, password_hash: str) -> bool:
        """Store password hash in secure location"""
        # Try macOS keychain first
        if os.system("which security > /dev/null 2>&1") == 0:
            cmd = f"security add-generic-password -s 'prompt-manager-secure' -a '{os.getenv('USER', 'default')}' -w '{password_hash}' 2>/dev/null"
            if os.system(cmd) == 0:
                return True
        
        # Fallback to encrypted file
        hash_file = os.path.expanduser("~/.pm_secure_hash")
        try:
            with open(hash_file, 'w') as f:
                f.write(password_hash)
            os.chmod(hash_file, 0o600)
            return True
        except:
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user has valid authentication session"""
        return self._get_session_data() is not None
    
    def logout(self) -> bool:
        """End current secure session"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            print("✅ Secure session ended")
            return True
        except:
            return False
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""
        session_data = self._get_session_data()
        if not session_data:
            return None
        
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        time_remaining = expires_at - datetime.now()
        
        return {
            'authenticated': True,
            'expires_at': session_data['expires_at'],
            'time_remaining_minutes': int(time_remaining.total_seconds() / 60),
            'access_count': session_data.get('access_count', 0),
            'created_at': session_data['created_at']
        }
    
    def extend_session(self, additional_minutes: int = None) -> bool:
        """Extend current session by additional time"""
        session_data = self._get_session_data()
        if not session_data:
            return False
        
        if additional_minutes is None:
            additional_minutes = self.session_ttl_minutes
        
        current_expires = datetime.fromisoformat(session_data['expires_at'])
        new_expires = current_expires + timedelta(minutes=additional_minutes)
        session_data['expires_at'] = new_expires.isoformat()
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            return True
        except:
            return False


# Configuration helper
def get_session_ttl_from_config() -> int:
    """Get session TTL from configuration or environment"""
    # Check environment variable first
    env_ttl = os.getenv('PM_SECURE_SESSION_TTL')
    if env_ttl:
        try:
            return int(env_ttl)
        except ValueError:
            pass
    
    # Check config file
    config_file = os.path.expanduser("~/.pm_config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('secure_session_ttl_minutes', 60)
        except:
            pass
    
    return 60  # Default 1 hour


if __name__ == "__main__":
    # Test the session manager
    session = SecureSession(session_ttl_minutes=1)  # 1 minute for testing
    
    print("Testing secure session...")
    if session.authenticate():
        info = session.get_session_info()
        print(f"Session info: {info}")
        
        print("Waiting 30 seconds...")
        time.sleep(30)
        
        print(f"Still authenticated: {session.is_authenticated()}")
        session.logout()