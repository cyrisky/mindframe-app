"""Logging utilities for the mindframe application"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Any, Dict, Optional, Union, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import traceback
import functools
import time


class LogLevel(Enum):
    """Log levels"""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class LogFormat(Enum):
    """Log formats"""
    SIMPLE = 'simple'
    DETAILED = 'detailed'
    JSON = 'json'
    STRUCTURED = 'structured'


@dataclass
class LogConfig:
    """Logging configuration"""
    level: str = 'INFO'
    format_type: str = 'detailed'
    log_file: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_output: bool = True
    json_output: bool = False
    include_caller_info: bool = True
    include_process_info: bool = False
    include_thread_info: bool = False
    date_format: str = '%Y-%m-%d %H:%M:%S'
    timezone: str = 'UTC'
    sensitive_fields: List[str] = field(default_factory=lambda: ['password', 'token', 'secret', 'key'])


class JSONFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def __init__(self, include_caller_info: bool = True, include_process_info: bool = False, 
                 include_thread_info: bool = False, sensitive_fields: List[str] = None):
        super().__init__()
        self.include_caller_info = include_caller_info
        self.include_process_info = include_process_info
        self.include_thread_info = include_thread_info
        self.sensitive_fields = sensitive_fields or []
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON
        
        Args:
            record: Log record
            
        Returns:
            str: JSON formatted log message
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # Add caller information
        if self.include_caller_info:
            log_data.update({
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'pathname': record.pathname
            })
        
        # Add process information
        if self.include_process_info:
            log_data.update({
                'process': record.process,
                'process_name': record.processName
            })
        
        # Add thread information
        if self.include_thread_info:
            log_data.update({
                'thread': record.thread,
                'thread_name': record.threadName
            })
        
        # Add exception information
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                # Sanitize sensitive fields
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    log_data[key] = '[REDACTED]'
                else:
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)


class StructuredFormatter(logging.Formatter):
    """Structured log formatter"""
    
    def __init__(self, include_caller_info: bool = True, sensitive_fields: List[str] = None):
        super().__init__()
        self.include_caller_info = include_caller_info
        self.sensitive_fields = sensitive_fields or []
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record in structured format
        
        Args:
            record: Log record
            
        Returns:
            str: Structured log message
        """
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        parts = [
            f"[{timestamp}]",
            f"[{record.levelname}]",
            f"[{record.name}]"
        ]
        
        if self.include_caller_info:
            parts.append(f"[{record.module}:{record.funcName}:{record.lineno}]")
        
        parts.append(record.getMessage())
        
        # Add extra fields
        extra_fields = []
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                # Sanitize sensitive fields
                if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    extra_fields.append(f"{key}=[REDACTED]")
                else:
                    extra_fields.append(f"{key}={value}")
        
        if extra_fields:
            parts.append(f"[{', '.join(extra_fields)}]")
        
        message = ' '.join(parts)
        
        # Add exception information
        if record.exc_info:
            message += '\n' + ''.join(traceback.format_exception(*record.exc_info))
        
        return message


class LoggingUtils:
    """Utility class for logging operations"""
    
    _loggers: Dict[str, logging.Logger] = {}
    _config: Optional[LogConfig] = None
    
    @classmethod
    def setup_logging(cls, config: LogConfig) -> None:
        """Setup logging configuration
        
        Args:
            config: Logging configuration
        """
        cls._config = config
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Setup formatters
        formatters = cls._create_formatters(config)
        
        # Setup console handler
        if config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.level.upper()))
            
            if config.json_output:
                console_handler.setFormatter(formatters['json'])
            else:
                console_handler.setFormatter(formatters[config.format_type])
            
            root_logger.addHandler(console_handler)
        
        # Setup file handler
        if config.log_file:
            cls._setup_file_handler(config, formatters)
    
    @classmethod
    def _create_formatters(cls, config: LogConfig) -> Dict[str, logging.Formatter]:
        """Create log formatters
        
        Args:
            config: Logging configuration
            
        Returns:
            Dict: Formatters dictionary
        """
        formatters = {}
        
        # Simple formatter
        formatters['simple'] = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt=config.date_format
        )
        
        # Detailed formatter
        formatters['detailed'] = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt=config.date_format
        )
        
        # JSON formatter
        formatters['json'] = JSONFormatter(
            include_caller_info=config.include_caller_info,
            include_process_info=config.include_process_info,
            include_thread_info=config.include_thread_info,
            sensitive_fields=config.sensitive_fields
        )
        
        # Structured formatter
        formatters['structured'] = StructuredFormatter(
            include_caller_info=config.include_caller_info,
            sensitive_fields=config.sensitive_fields
        )
        
        return formatters
    
    @classmethod
    def _setup_file_handler(cls, config: LogConfig, formatters: Dict[str, logging.Formatter]) -> None:
        """Setup file handler
        
        Args:
            config: Logging configuration
            formatters: Available formatters
        """
        log_file = Path(config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.log_file,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count,
            encoding='utf-8'
        )
        
        file_handler.setLevel(getattr(logging, config.level.upper()))
        
        if config.json_output:
            file_handler.setFormatter(formatters['json'])
        else:
            file_handler.setFormatter(formatters[config.format_type])
        
        logging.getLogger().addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create logger
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: Logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]
    
    @classmethod
    def log_function_call(cls, logger: logging.Logger = None, level: str = 'DEBUG', 
                         include_args: bool = True, include_result: bool = True,
                         exclude_args: List[str] = None):
        """Decorator to log function calls
        
        Args:
            logger: Logger to use (default: function module logger)
            level: Log level
            include_args: Whether to include function arguments
            include_result: Whether to include function result
            exclude_args: Arguments to exclude from logging
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Get logger
                func_logger = logger or cls.get_logger(func.__module__)
                log_level = getattr(logging, level.upper())
                
                # Prepare function info
                func_name = f"{func.__module__}.{func.__qualname__}"
                exclude_list = exclude_args or []
                
                # Log function entry
                if include_args:
                    # Filter sensitive arguments
                    safe_args = []
                    for i, arg in enumerate(args):
                        if i < len(exclude_list) and exclude_list[i]:
                            safe_args.append('[REDACTED]')
                        else:
                            safe_args.append(repr(arg))
                    
                    safe_kwargs = {}
                    for key, value in kwargs.items():
                        if key in exclude_list or any(sensitive in key.lower() 
                                                     for sensitive in cls._config.sensitive_fields if cls._config):
                            safe_kwargs[key] = '[REDACTED]'
                        else:
                            safe_kwargs[key] = repr(value)
                    
                    func_logger.log(log_level, f"Calling {func_name} with args={safe_args}, kwargs={safe_kwargs}")
                else:
                    func_logger.log(log_level, f"Calling {func_name}")
                
                # Execute function
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log function exit
                    if include_result:
                        func_logger.log(log_level, f"{func_name} completed in {execution_time:.3f}s with result: {repr(result)}")
                    else:
                        func_logger.log(log_level, f"{func_name} completed in {execution_time:.3f}s")
                    
                    return result
                
                except Exception as e:
                    execution_time = time.time() - start_time
                    func_logger.log(logging.ERROR, f"{func_name} failed after {execution_time:.3f}s with error: {str(e)}")
                    raise
            
            return wrapper
        return decorator
    
    @classmethod
    def log_performance(cls, logger: logging.Logger = None, level: str = 'INFO', 
                       threshold_seconds: float = 1.0):
        """Decorator to log function performance
        
        Args:
            logger: Logger to use
            level: Log level
            threshold_seconds: Only log if execution time exceeds threshold
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_logger = logger or cls.get_logger(func.__module__)
                log_level = getattr(logging, level.upper())
                
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if execution_time >= threshold_seconds:
                    func_name = f"{func.__module__}.{func.__qualname__}"
                    func_logger.log(log_level, f"Performance: {func_name} took {execution_time:.3f}s")
                
                return result
            
            return wrapper
        return decorator
    
    @classmethod
    def log_exception(cls, logger: logging.Logger, message: str = None, 
                     exc_info: bool = True, extra: Dict[str, Any] = None) -> None:
        """Log exception with context
        
        Args:
            logger: Logger to use
            message: Custom message
            exc_info: Include exception info
            extra: Extra context data
        """
        log_message = message or "An exception occurred"
        
        if extra:
            # Sanitize extra data
            safe_extra = {}
            sensitive_fields = cls._config.sensitive_fields if cls._config else []
            
            for key, value in extra.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    safe_extra[key] = '[REDACTED]'
                else:
                    safe_extra[key] = value
            
            logger.error(log_message, exc_info=exc_info, extra=safe_extra)
        else:
            logger.error(log_message, exc_info=exc_info)
    
    @classmethod
    def create_context_logger(cls, base_logger: logging.Logger, context: Dict[str, Any]) -> logging.LoggerAdapter:
        """Create logger with context
        
        Args:
            base_logger: Base logger
            context: Context data to include in all log messages
            
        Returns:
            logging.LoggerAdapter: Logger adapter with context
        """
        # Sanitize context
        safe_context = {}
        sensitive_fields = cls._config.sensitive_fields if cls._config else []
        
        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                safe_context[key] = '[REDACTED]'
            else:
                safe_context[key] = value
        
        return logging.LoggerAdapter(base_logger, safe_context)
    
    @classmethod
    def setup_request_logging(cls, app) -> None:
        """Setup request logging for Flask app
        
        Args:
            app: Flask application
        """
        request_logger = cls.get_logger('mindframe.requests')
        
        @app.before_request
        def log_request_start():
            from flask import request, g
            g.start_time = time.time()
            
            request_logger.info(
                "Request started",
                extra={
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'request_id': getattr(g, 'request_id', None)
                }
            )
        
        @app.after_request
        def log_request_end(response):
            from flask import g
            
            execution_time = time.time() - getattr(g, 'start_time', time.time())
            
            request_logger.info(
                "Request completed",
                extra={
                    'status_code': response.status_code,
                    'execution_time': execution_time,
                    'content_length': response.content_length,
                    'request_id': getattr(g, 'request_id', None)
                }
            )
            
            return response
    
    @classmethod
    def get_log_stats(cls) -> Dict[str, Any]:
        """Get logging statistics
        
        Returns:
            Dict: Logging statistics
        """
        stats = {
            'active_loggers': len(cls._loggers),
            'logger_names': list(cls._loggers.keys()),
            'root_level': logging.getLogger().level,
            'handlers_count': len(logging.getLogger().handlers)
        }
        
        if cls._config:
            stats.update({
                'config_level': cls._config.level,
                'log_file': cls._config.log_file,
                'console_output': cls._config.console_output,
                'json_output': cls._config.json_output
            })
        
        return stats
    
    @classmethod
    def cleanup_old_logs(cls, log_directory: Union[str, Path], days_to_keep: int = 30) -> int:
        """Clean up old log files
        
        Args:
            log_directory: Directory containing log files
            days_to_keep: Number of days to keep logs
            
        Returns:
            int: Number of files deleted
        """
        log_dir = Path(log_directory)
        if not log_dir.exists():
            return 0
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for log_file in log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except OSError:
                    pass  # File might be in use
        
        return deleted_count