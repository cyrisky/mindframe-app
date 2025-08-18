"""Security utilities for the mindframe application"""

import hashlib
import hmac
import secrets
import base64
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import jwt


class SecurityUtils:
    """Utility class for security operations"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token
        
        Args:
            length: Length of the token in bytes
            
        Returns:
            str: Secure random token as hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password
        
        Args:
            length: Length of the password
            
        Returns:
            str: Secure random password
        """
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generate a random salt
        
        Args:
            length: Length of the salt in bytes
            
        Returns:
            str: Random salt as hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_data(data: str, salt: str = None) -> str:
        """Hash data using SHA-256
        
        Args:
            data: Data to hash
            salt: Optional salt to add
            
        Returns:
            str: Hashed data as hex string
        """
        if salt:
            data = data + salt
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_hmac(data: str, secret_key: str) -> str:
        """Generate HMAC for data
        
        Args:
            data: Data to generate HMAC for
            secret_key: Secret key for HMAC
            
        Returns:
            str: HMAC as hex string
        """
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_hmac(data: str, secret_key: str, provided_hmac: str) -> bool:
        """Verify HMAC for data
        
        Args:
            data: Original data
            secret_key: Secret key used for HMAC
            provided_hmac: HMAC to verify
            
        Returns:
            bool: True if HMAC is valid, False otherwise
        """
        expected_hmac = SecurityUtils.generate_hmac(data, secret_key)
        return hmac.compare_digest(expected_hmac, provided_hmac)
    
    @staticmethod
    def encrypt_data(data: str, key: str = None) -> tuple[str, str]:
        """Encrypt data using Fernet symmetric encryption
        
        Args:
            data: Data to encrypt
            key: Optional encryption key (will generate if not provided)
            
        Returns:
            tuple: (encrypted_data, encryption_key)
        """
        if not key:
            key = Fernet.generate_key().decode()
        
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        encrypted_data = fernet.encrypt(data.encode('utf-8'))
        return base64.b64encode(encrypted_data).decode(), key
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> Optional[str]:
        """Decrypt data using Fernet symmetric encryption
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            key: Encryption key
            
        Returns:
            Optional[str]: Decrypted data or None if decryption fails
        """
        try:
            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception:
            return None
    
    @staticmethod
    def generate_encryption_key_from_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """Generate encryption key from password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Optional salt (will generate if not provided)
            
        Returns:
            tuple: (base64_encoded_key, salt)
        """
        if not salt:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Sanitize user input to prevent injection attacks
        
        Args:
            input_string: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized input string
        """
        if not isinstance(input_string, str):
            input_string = str(input_string)
        
        # Remove null bytes
        input_string = input_string.replace('\x00', '')
        
        # Limit length
        if len(input_string) > max_length:
            input_string = input_string[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        
        return input_string.strip()
    
    @staticmethod
    def validate_csrf_token(token: str, secret_key: str, max_age: int = 3600) -> bool:
        """Validate CSRF token
        
        Args:
            token: CSRF token to validate
            secret_key: Secret key used to generate token
            max_age: Maximum age of token in seconds
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Decode the token
            decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            # Check if token has expired
            issued_at = decoded_token.get('iat')
            if not issued_at:
                return False
            
            token_age = datetime.utcnow().timestamp() - issued_at
            return token_age <= max_age
        except Exception:
            return False
    
    @staticmethod
    def generate_csrf_token(secret_key: str) -> str:
        """Generate CSRF token
        
        Args:
            secret_key: Secret key for token generation
            
        Returns:
            str: CSRF token
        """
        payload = {
            'iat': datetime.utcnow().timestamp(),
            'csrf': secrets.token_hex(16)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        """Check password strength and provide feedback
        
        Args:
            password: Password to check
            
        Returns:
            Dict: Password strength analysis
        """
        result = {
            'score': 0,
            'strength': 'Very Weak',
            'feedback': [],
            'is_strong': False
        }
        
        if len(password) < 8:
            result['feedback'].append('Password should be at least 8 characters long')
        else:
            result['score'] += 1
        
        if not any(c.islower() for c in password):
            result['feedback'].append('Password should contain lowercase letters')
        else:
            result['score'] += 1
        
        if not any(c.isupper() for c in password):
            result['feedback'].append('Password should contain uppercase letters')
        else:
            result['score'] += 1
        
        if not any(c.isdigit() for c in password):
            result['feedback'].append('Password should contain numbers')
        else:
            result['score'] += 1
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            result['feedback'].append('Password should contain special characters')
        else:
            result['score'] += 1
        
        # Determine strength level
        if result['score'] >= 5:
            result['strength'] = 'Very Strong'
            result['is_strong'] = True
        elif result['score'] >= 4:
            result['strength'] = 'Strong'
            result['is_strong'] = True
        elif result['score'] >= 3:
            result['strength'] = 'Medium'
        elif result['score'] >= 2:
            result['strength'] = 'Weak'
        else:
            result['strength'] = 'Very Weak'
        
        return result
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
        """Mask sensitive data for logging or display
        
        Args:
            data: Sensitive data to mask
            mask_char: Character to use for masking
            visible_chars: Number of characters to leave visible at the end
            
        Returns:
            str: Masked data
        """
        if not data or len(data) <= visible_chars:
            return mask_char * len(data) if data else ''
        
        masked_length = len(data) - visible_chars
        return mask_char * masked_length + data[-visible_chars:]
    
    @staticmethod
    def generate_api_key(prefix: str = 'mk', length: int = 32) -> str:
        """Generate API key with prefix
        
        Args:
            prefix: Prefix for the API key
            length: Length of the random part
            
        Returns:
            str: Generated API key
        """
        random_part = secrets.token_hex(length)
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def validate_api_key_format(api_key: str, expected_prefix: str = 'mk') -> bool:
        """Validate API key format
        
        Args:
            api_key: API key to validate
            expected_prefix: Expected prefix
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not api_key or '_' not in api_key:
            return False
        
        prefix, key_part = api_key.split('_', 1)
        return prefix == expected_prefix and len(key_part) >= 32
    
    @staticmethod
    def rate_limit_key(identifier: str, action: str) -> str:
        """Generate rate limiting key
        
        Args:
            identifier: User or IP identifier
            action: Action being rate limited
            
        Returns:
            str: Rate limiting key
        """
        return f"rate_limit:{action}:{identifier}"
    
    @staticmethod
    def secure_compare(a: str, b: str) -> bool:
        """Perform timing-safe string comparison
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            bool: True if strings are equal, False otherwise
        """
        return hmac.compare_digest(a, b)