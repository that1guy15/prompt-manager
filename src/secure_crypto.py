#!/usr/bin/env python3

"""
Secure Cryptographic Utilities for Prompt Manager
Handles AES-256 encryption/decryption for sensitive variables
"""

import os
import base64
import hashlib
from typing import Optional, Tuple
from datetime import datetime


class SecureCrypto:
    """Handles encryption/decryption of sensitive data"""
    
    def __init__(self):
        self.key_size = 32  # 256 bits
        self.iv_size = 16   # 128 bits for AES
    
    def _derive_key(self, password_hash: str, salt: bytes) -> bytes:
        """Derive encryption key from password hash and salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password_hash.encode(),
            salt,
            100000,  # iterations
            self.key_size
        )
    
    def encrypt(self, plaintext: str, password_hash: str) -> str:
        """Encrypt plaintext using AES-256-CBC"""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            # Fallback to simpler encryption if cryptography is not available
            return self._simple_encrypt(plaintext, password_hash)
        
        # Generate random salt and IV
        salt = os.urandom(16)
        iv = os.urandom(self.iv_size)
        
        # Derive key from password hash
        key = self._derive_key(password_hash, salt)
        
        # Pad plaintext to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine salt + iv + ciphertext and encode
        encrypted_data = salt + iv + ciphertext
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str, password_hash: str) -> Optional[str]:
        """Decrypt encrypted data using AES-256-CBC"""
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            # Fallback to simpler decryption
            return self._simple_decrypt(encrypted_data, password_hash)
        
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode())
            
            # Extract salt, IV, and ciphertext
            salt = data[:16]
            iv = data[16:32]
            ciphertext = data[32:]
            
            # Derive key
            key = self._derive_key(password_hash, salt)
            
            # Decrypt
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext.decode()
            
        except Exception as e:
            # Return None for any decryption errors (wrong password, corrupted data, etc.)
            return None
    
    def _simple_encrypt(self, plaintext: str, password_hash: str) -> str:
        """Simple XOR-based encryption fallback (less secure)"""
        # Generate salt
        salt = os.urandom(16)
        
        # Create key from password hash and salt
        key_material = (password_hash + salt.hex()).encode()
        key = hashlib.sha256(key_material).digest()
        
        # XOR encryption
        plaintext_bytes = plaintext.encode()
        encrypted = bytearray()
        
        for i, byte in enumerate(plaintext_bytes):
            encrypted.append(byte ^ key[i % len(key)])
        
        # Combine salt + encrypted data
        result = salt + bytes(encrypted)
        return base64.b64encode(result).decode()
    
    def _simple_decrypt(self, encrypted_data: str, password_hash: str) -> Optional[str]:
        """Simple XOR-based decryption fallback"""
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode())
            
            # Extract salt and encrypted data
            salt = data[:16]
            encrypted = data[16:]
            
            # Recreate key
            key_material = (password_hash + salt.hex()).encode()
            key = hashlib.sha256(key_material).digest()
            
            # XOR decryption
            decrypted = bytearray()
            for i, byte in enumerate(encrypted):
                decrypted.append(byte ^ key[i % len(key)])
            
            return bytes(decrypted).decode()
            
        except Exception:
            return None
    
    def create_encrypted_metadata(self, description: str, password_hash: str, 
                                 default_value: str = None) -> dict:
        """Create encrypted metadata for secure variable"""
        encrypted_desc = self.encrypt(description, password_hash)
        
        metadata = {
            'encrypted_description': encrypted_desc,
            'is_secure': True,
            'created_at': datetime.now().isoformat(),  
            'used_count': 0,
            'last_accessed': None
        }
        
        if default_value:
            metadata['encrypted_default'] = self.encrypt(default_value, password_hash)
        
        return metadata
    
    def decrypt_metadata(self, metadata: dict, password_hash: str) -> dict:
        """Decrypt metadata for display"""
        result = metadata.copy()
        
        # Decrypt description
        if 'encrypted_description' in metadata:
            decrypted_desc = self.decrypt(metadata['encrypted_description'], password_hash)
            if decrypted_desc:
                result['description'] = decrypted_desc
            else:
                result['description'] = '[ENCRYPTED - CANNOT DECRYPT]'
        
        # Decrypt default value if present
        if 'encrypted_default' in metadata:
            decrypted_default = self.decrypt(metadata['encrypted_default'], password_hash)
            if decrypted_default:
                result['default_value'] = decrypted_default
            else:
                result['default_value'] = '[ENCRYPTED]'
        
        return result
    
    def get_encrypted_value_placeholder(self) -> str:
        """Get placeholder text for encrypted values"""
        return "•••••••••••••••"
    
    def verify_encryption_capability(self) -> Tuple[bool, str]:
        """Verify that encryption is working properly"""
        test_data = "test_encryption_capability"
        test_password = "test_password_hash"
        
        # Test encryption/decryption cycle
        try:
            encrypted = self.encrypt(test_data, test_password)
            decrypted = self.decrypt(encrypted, test_password)
            
            if decrypted == test_data:
                try:
                    from cryptography.hazmat.primitives.ciphers import Cipher
                    return True, "AES-256 encryption available"
                except ImportError:
                    return True, "Fallback encryption available (less secure)"
            else:
                return False, "Encryption test failed"
                
        except Exception as e:
            return False, f"Encryption error: {str(e)}"


def test_encryption():
    """Test encryption functionality"""
    crypto = SecureCrypto()
    
    # Test basic encryption
    plaintext = "This is a secret API key: abc123xyz789"
    password_hash = "test_password_hash_12345"
    
    print("Testing encryption...")
    encrypted = crypto.encrypt(plaintext, password_hash)
    print(f"Encrypted: {encrypted}")
    
    decrypted = crypto.decrypt(encrypted, password_hash)
    print(f"Decrypted: {decrypted}")
    
    print(f"Success: {plaintext == decrypted}")
    
    # Test wrong password
    wrong_decrypted = crypto.decrypt(encrypted, "wrong_password")
    print(f"Wrong password result: {wrong_decrypted}")
    
    # Test metadata creation
    metadata = crypto.create_encrypted_metadata(
        "API Key for Service X", 
        password_hash, 
        "default_api_key_value"
    )
    print(f"Encrypted metadata: {metadata}")
    
    decrypted_metadata = crypto.decrypt_metadata(metadata, password_hash)
    print(f"Decrypted metadata: {decrypted_metadata}")
    
    # Test encryption capability
    capable, message = crypto.verify_encryption_capability()
    print(f"Encryption capability: {capable} - {message}")


if __name__ == "__main__":
    test_encryption()