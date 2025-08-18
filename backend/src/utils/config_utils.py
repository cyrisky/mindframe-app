"""Configuration utilities for the mindframe application"""

import os
import json
import yaml
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
from configparser import ConfigParser
import logging
from urllib.parse import urlparse


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = 'localhost'
    port: int = 27017
    database: str = 'mindframe'
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    ssl: bool = False
    auth_source: str = 'admin'
    replica_set: Optional[str] = None
    max_pool_size: int = 100
    min_pool_size: int = 0
    connect_timeout_ms: int = 20000
    server_selection_timeout_ms: int = 30000


@dataclass
class RedisConfig:
    """Redis configuration"""
    host: str = 'localhost'
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    ssl: bool = False
    connection_pool_max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class StorageConfig:
    """Storage configuration"""
    provider: str = 'local'  # 'local' or 'gcs'
    local_path: str = './storage'
    gcs_bucket: Optional[str] = None
    gcs_credentials_path: Optional[str] = None
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = field(default_factory=lambda: ['pdf', 'doc', 'docx', 'txt'])
    cleanup_interval_hours: int = 24


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str = 'localhost'
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    from_email: str = 'noreply@mindframe.com'
    from_name: str = 'Mindframe'
    template_path: str = './templates/email'
    max_recipients: int = 100
    rate_limit_per_hour: int = 1000


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = 'your-secret-key-change-this'
    jwt_secret: str = 'your-jwt-secret-change-this'
    jwt_access_token_expires: int = 3600  # 1 hour
    jwt_refresh_token_expires: int = 2592000  # 30 days
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    csrf_token_expires: int = 3600
    api_rate_limit_per_minute: int = 60


@dataclass
class AppConfig:
    """Application configuration"""
    name: str = 'Mindframe'
    version: str = '1.0.0'
    debug: bool = False
    host: str = '0.0.0.0'
    port: int = 8000
    base_url: str = 'http://localhost:8000'
    timezone: str = 'UTC'
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    max_workers: int = 4
    request_timeout: int = 30
    cors_origins: List[str] = field(default_factory=lambda: ['*'])
    cors_methods: List[str] = field(default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])


class ConfigUtils:
    """Utility class for configuration management"""
    
    @staticmethod
    def load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables
        
        Returns:
            Dict: Configuration dictionary
        """
        config = {}
        
        # Database configuration
        config['database'] = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '27017')),
            'database': os.getenv('DB_NAME', 'mindframe'),
            'username': os.getenv('DB_USERNAME'),
            'password': os.getenv('DB_PASSWORD'),
            'connection_string': os.getenv('DB_CONNECTION_STRING'),
            'ssl': os.getenv('DB_SSL', 'false').lower() == 'true',
            'auth_source': os.getenv('DB_AUTH_SOURCE', 'admin'),
            'replica_set': os.getenv('DB_REPLICA_SET'),
            'max_pool_size': int(os.getenv('DB_MAX_POOL_SIZE', '100')),
            'min_pool_size': int(os.getenv('DB_MIN_POOL_SIZE', '0')),
            'connect_timeout_ms': int(os.getenv('DB_CONNECT_TIMEOUT_MS', '20000')),
            'server_selection_timeout_ms': int(os.getenv('DB_SERVER_SELECTION_TIMEOUT_MS', '30000'))
        }
        
        # Redis configuration
        config['redis'] = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'database': int(os.getenv('REDIS_DB', '0')),
            'password': os.getenv('REDIS_PASSWORD'),
            'ssl': os.getenv('REDIS_SSL', 'false').lower() == 'true',
            'connection_pool_max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            'socket_timeout': int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            'socket_connect_timeout': int(os.getenv('REDIS_CONNECT_TIMEOUT', '5')),
            'retry_on_timeout': os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            'health_check_interval': int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30'))
        }
        
        # Storage configuration
        config['storage'] = {
            'provider': os.getenv('STORAGE_PROVIDER', 'local'),
            'local_path': os.getenv('STORAGE_LOCAL_PATH', './storage'),
            'gcs_bucket': os.getenv('STORAGE_GCS_BUCKET'),
            'gcs_credentials_path': os.getenv('STORAGE_GCS_CREDENTIALS_PATH'),
            'max_file_size_mb': int(os.getenv('STORAGE_MAX_FILE_SIZE_MB', '100')),
            'allowed_file_types': os.getenv('STORAGE_ALLOWED_FILE_TYPES', 'pdf,doc,docx,txt').split(','),
            'cleanup_interval_hours': int(os.getenv('STORAGE_CLEANUP_INTERVAL_HOURS', '24'))
        }
        
        # Email configuration
        config['email'] = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', 'localhost'),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'smtp_username': os.getenv('EMAIL_SMTP_USERNAME'),
            'smtp_password': os.getenv('EMAIL_SMTP_PASSWORD'),
            'use_tls': os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true',
            'from_email': os.getenv('EMAIL_FROM_EMAIL', 'noreply@mindframe.com'),
            'from_name': os.getenv('EMAIL_FROM_NAME', 'Mindframe'),
            'template_path': os.getenv('EMAIL_TEMPLATE_PATH', './templates/email'),
            'max_recipients': int(os.getenv('EMAIL_MAX_RECIPIENTS', '100')),
            'rate_limit_per_hour': int(os.getenv('EMAIL_RATE_LIMIT_PER_HOUR', '1000'))
        }
        
        # Security configuration
        config['security'] = {
            'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-change-this'),
            'jwt_secret': os.getenv('JWT_SECRET', 'your-jwt-secret-change-this'),
            'jwt_access_token_expires': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')),
            'jwt_refresh_token_expires': int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000')),
            'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            'password_require_uppercase': os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true',
            'password_require_lowercase': os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true',
            'password_require_numbers': os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true',
            'password_require_special': os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true',
            'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            'lockout_duration_minutes': int(os.getenv('LOCKOUT_DURATION_MINUTES', '30')),
            'session_timeout_minutes': int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')),
            'csrf_token_expires': int(os.getenv('CSRF_TOKEN_EXPIRES', '3600')),
            'api_rate_limit_per_minute': int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '60'))
        }
        
        # Application configuration
        config['app'] = {
            'name': os.getenv('APP_NAME', 'Mindframe'),
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '8000')),
            'base_url': os.getenv('BASE_URL', 'http://localhost:8000'),
            'timezone': os.getenv('TIMEZONE', 'UTC'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE'),
            'max_workers': int(os.getenv('MAX_WORKERS', '4')),
            'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
            'cors_origins': os.getenv('CORS_ORIGINS', '*').split(','),
            'cors_methods': os.getenv('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
        }
        
        return config
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path], file_format: str = 'auto') -> Dict[str, Any]:
        """Load configuration from file
        
        Args:
            file_path: Path to configuration file
            file_format: File format ('json', 'yaml', 'ini', or 'auto')
            
        Returns:
            Dict: Configuration dictionary
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Auto-detect format from extension
        if file_format == 'auto':
            extension = file_path.suffix.lower()
            if extension in ['.json']:
                file_format = 'json'
            elif extension in ['.yaml', '.yml']:
                file_format = 'yaml'
            elif extension in ['.ini', '.cfg']:
                file_format = 'ini'
            else:
                raise ValueError(f"Cannot auto-detect format for file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_format == 'json':
                return json.load(f)
            elif file_format == 'yaml':
                return yaml.safe_load(f)
            elif file_format == 'ini':
                parser = ConfigParser()
                parser.read_file(f)
                return {section: dict(parser[section]) for section in parser.sections()}
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
    
    @staticmethod
    def save_to_file(config: Dict[str, Any], file_path: Union[str, Path], file_format: str = 'auto') -> None:
        """Save configuration to file
        
        Args:
            config: Configuration dictionary
            file_path: Path to save configuration
            file_format: File format ('json', 'yaml', or 'auto')
        """
        file_path = Path(file_path)
        
        # Auto-detect format from extension
        if file_format == 'auto':
            extension = file_path.suffix.lower()
            if extension in ['.json']:
                file_format = 'json'
            elif extension in ['.yaml', '.yml']:
                file_format = 'yaml'
            else:
                file_format = 'json'  # Default to JSON
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_format == 'json':
                json.dump(config, f, indent=2, default=str)
            elif file_format == 'yaml':
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries
        
        Args:
            *configs: Configuration dictionaries to merge
            
        Returns:
            Dict: Merged configuration
        """
        merged = {}
        
        for config in configs:
            for key, value in config.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = ConfigUtils.merge_configs(merged[key], value)
                else:
                    merged[key] = value
        
        return merged
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """Validate configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # Validate required sections
        required_sections = ['app', 'database', 'security']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate app section
        if 'app' in config:
            app_config = config['app']
            if not app_config.get('secret_key') or app_config.get('secret_key') == 'your-secret-key-change-this':
                errors.append("App secret_key must be set to a secure value")
            
            if app_config.get('port', 0) <= 0 or app_config.get('port', 0) > 65535:
                errors.append("App port must be between 1 and 65535")
        
        # Validate security section
        if 'security' in config:
            security_config = config['security']
            if not security_config.get('jwt_secret') or security_config.get('jwt_secret') == 'your-jwt-secret-change-this':
                errors.append("Security jwt_secret must be set to a secure value")
            
            if security_config.get('password_min_length', 0) < 8:
                errors.append("Password minimum length should be at least 8")
        
        # Validate database section
        if 'database' in config:
            db_config = config['database']
            if not db_config.get('connection_string'):
                if not db_config.get('host'):
                    errors.append("Database host is required when connection_string is not provided")
                if not db_config.get('database'):
                    errors.append("Database name is required")
        
        return errors
    
    @staticmethod
    def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def set_config_value(config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set configuration value using dot notation
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., 'database.host')
            value: Value to set
        """
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    @staticmethod
    def parse_database_url(url: str) -> Dict[str, Any]:
        """Parse database URL into configuration components
        
        Args:
            url: Database URL (e.g., 'mongodb://user:pass@host:port/database')
            
        Returns:
            Dict: Database configuration
        """
        parsed = urlparse(url)
        
        config = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 27017,
            'database': parsed.path.lstrip('/') if parsed.path else 'mindframe',
            'username': parsed.username,
            'password': parsed.password,
            'connection_string': url
        }
        
        # Parse query parameters
        if parsed.query:
            from urllib.parse import parse_qs
            params = parse_qs(parsed.query)
            
            if 'ssl' in params:
                config['ssl'] = params['ssl'][0].lower() == 'true'
            if 'authSource' in params:
                config['auth_source'] = params['authSource'][0]
            if 'replicaSet' in params:
                config['replica_set'] = params['replicaSet'][0]
        
        return config
    
    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """Create default configuration
        
        Returns:
            Dict: Default configuration
        """
        return {
            'app': AppConfig().__dict__,
            'database': DatabaseConfig().__dict__,
            'redis': RedisConfig().__dict__,
            'storage': StorageConfig().__dict__,
            'email': EmailConfig().__dict__,
            'security': SecurityConfig().__dict__
        }
    
    @staticmethod
    def setup_logging(config: Dict[str, Any]) -> None:
        """Setup logging based on configuration
        
        Args:
            config: Configuration dictionary
        """
        log_level = ConfigUtils.get_config_value(config, 'app.log_level', 'INFO')
        log_file = ConfigUtils.get_config_value(config, 'app.log_file')
        
        # Configure logging
        logging_config = {
            'level': getattr(logging, log_level.upper()),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
        
        if log_file:
            logging_config['filename'] = log_file
            logging_config['filemode'] = 'a'
        
        logging.basicConfig(**logging_config)