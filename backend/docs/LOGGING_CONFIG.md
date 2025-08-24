# Logging Configuration Guide

This document outlines the comprehensive logging system implemented in the Mindframe backend application.

## Overview

The application uses a structured logging system with multiple formatters, configurable output destinations, and comprehensive request tracking.

## Features

### 🔧 Logging Formatters
- **Simple**: Basic timestamp, level, and message
- **Detailed**: Includes module, function, and line number information
- **JSON**: Machine-readable JSON format for log aggregation
- **Structured**: Enhanced format with context information

### 📊 Request Logging
- Automatic request start/end logging
- Execution time tracking
- Request ID correlation
- User agent and IP address logging
- Response status and content length tracking

### 🔒 Security Features
- Automatic redaction of sensitive fields (passwords, tokens, secrets)
- Configurable sensitive field detection
- Safe context logging with data sanitization

### 📁 File Management
- Rotating log files with configurable size limits
- Automatic backup retention
- Log cleanup utilities
- Configurable log directory structure

## Environment Variables

### Core Configuration
```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log format (simple, detailed, json, structured)
LOG_FORMAT=structured

# Log file path (relative to backend directory)
LOG_FILE=logs/mindframe.log

# Enable JSON output for log aggregation
LOG_JSON=false

# Maximum log file size in MB
LOG_MAX_SIZE_MB=50

# Number of backup files to keep
LOG_BACKUP_COUNT=10
```

### Advanced Configuration
```bash
# Include process information in logs
LOG_INCLUDE_PROCESS=true

# Include thread information in logs
LOG_INCLUDE_THREAD=false

# Custom date format
LOG_DATE_FORMAT=%Y-%m-%d %H:%M:%S

# Timezone for log timestamps
LOG_TIMEZONE=UTC
```

## Usage Examples

### Basic Logging
```python
from src.utils.logging_utils import LoggingUtils

# Get a logger for your module
logger = LoggingUtils.get_logger('mindframe.service')

# Log messages
logger.info("Service started successfully")
logger.warning("Configuration value missing, using default")
logger.error("Failed to connect to database", extra={'retry_count': 3})
```

### Structured Logging with Context
```python
# Log with additional context
logger.info("User action completed", extra={
    'user_id': user.id,
    'action': 'report_generation',
    'duration_ms': 1250,
    'success': True
})
```

### Security-Aware Logging
```python
# Automatically redacts sensitive information
logger = LoggingUtils.get_contextual_logger('auth.service', {
    'user_id': '12345',
    'password': 'secret123',  # Will be redacted
    'api_key': 'key_abc'      # Will be redacted
})

logger.info("Authentication attempt")  # Sensitive data automatically redacted
```

### Performance Logging
```python
# Use the performance logging decorator
from src.utils.logging_utils import log_performance

@log_performance
def expensive_operation(data):
    # Function implementation
    return result
```

## Log Levels and Usage

### DEBUG
- Detailed diagnostic information
- Variable values and state changes
- Function entry/exit points
- Only enabled in development

### INFO
- General application flow
- Service startup/shutdown
- User actions and business events
- Request/response summaries

### WARNING
- Recoverable errors
- Deprecated feature usage
- Configuration issues
- Performance concerns

### ERROR
- Application errors
- Failed operations
- Exception handling
- Integration failures

### CRITICAL
- System failures
- Security incidents
- Data corruption
- Service unavailability

## Log File Structure

```
logs/
├── mindframe.log          # Current log file
├── mindframe.log.1        # Previous log file
├── mindframe.log.2        # Older log file
└── ...
```

## JSON Log Format

When `LOG_JSON=true`, logs are output in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "mindframe.service",
  "message": "User action completed",
  "module": "report_service",
  "function": "generate_report",
  "line": 145,
  "process": 12345,
  "user_id": "67890",
  "action": "report_generation",
  "duration_ms": 1250
}
```

## Request Logging Format

Request logs include comprehensive information:

```
2024-01-15 10:30:45 - mindframe.requests - INFO - Request started
  Method: POST
  URL: /api/reports/generate
  Remote Address: 192.168.1.100
  User Agent: Mozilla/5.0...
  Request ID: req_abc123

2024-01-15 10:30:46 - mindframe.requests - INFO - Request completed
  Status Code: 200
  Execution Time: 1.25s
  Content Length: 2048
  Request ID: req_abc123
```

## Production Recommendations

### Log Level Configuration
- **Development**: `DEBUG` or `INFO`
- **Staging**: `INFO`
- **Production**: `WARNING` or `ERROR`

### File Management
- Set appropriate `LOG_MAX_SIZE_MB` (50-100MB)
- Configure `LOG_BACKUP_COUNT` (10-20 files)
- Implement log rotation and archival
- Monitor disk space usage

### Performance Considerations
- Use `LOG_JSON=true` for log aggregation systems
- Disable `LOG_INCLUDE_THREAD` unless needed
- Set appropriate log levels to reduce I/O
- Consider async logging for high-traffic applications

### Security
- Regularly review sensitive field configurations
- Ensure log files have appropriate permissions
- Implement log encryption for sensitive environments
- Monitor logs for security events

## Integration with Monitoring

### Log Aggregation
The JSON format is compatible with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Fluentd
- Splunk
- CloudWatch Logs
- Datadog

### Alerting
Set up alerts for:
- ERROR and CRITICAL level messages
- High error rates
- Performance degradation
- Security events

## Troubleshooting

### Common Issues

1. **Log files not created**
   - Check directory permissions
   - Verify `LOG_FILE` path
   - Ensure parent directories exist

2. **Logs not appearing**
   - Check `LOG_LEVEL` configuration
   - Verify logger name matches
   - Check console output settings

3. **Performance issues**
   - Reduce log level in production
   - Disable unnecessary context information
   - Consider async logging

4. **Sensitive data in logs**
   - Review sensitive field configuration
   - Use contextual loggers
   - Implement custom sanitization

### Log Analysis Commands

```bash
# View recent logs
tail -f logs/mindframe.log

# Search for errors
grep "ERROR\|CRITICAL" logs/mindframe.log

# Analyze request patterns
grep "Request completed" logs/mindframe.log | awk '{print $NF}'

# Count log levels
grep -o "INFO\|WARNING\|ERROR\|CRITICAL" logs/mindframe.log | sort | uniq -c
```

## Testing Logging

```python
# Test logging configuration
from src.utils.logging_utils import LoggingUtils

# Get logging statistics
stats = LoggingUtils.get_log_stats()
print(f"Active loggers: {stats['active_loggers']}")
print(f"Log level: {stats['config_level']}")

# Test log cleanup
deleted_count = LoggingUtils.cleanup_old_logs('logs/', days_to_keep=30)
print(f"Cleaned up {deleted_count} old log files")
```

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Flask Logging](https://flask.palletsprojects.com/en/2.3.x/logging/)
- [Structured Logging Best Practices](https://www.structlog.org/)
- [JSON Logging Standards](https://jsonlines.org/)