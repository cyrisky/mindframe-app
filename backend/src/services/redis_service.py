"""Redis service for caching and session management"""

import os
import json
import pickle
from typing import Optional, Any, Dict, List
import redis
from redis.exceptions import ConnectionError, TimeoutError
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations including caching and session management"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connection_params = {}
        self._is_connected = False
    
    def initialize(self, host: str = None, port: int = None, password: str = None,
                   db: int = 0, decode_responses: bool = True) -> bool:
        """Initialize Redis connection"""
        try:
            # Use provided parameters or environment variables
            self._connection_params = {
                'host': host or os.getenv('REDIS_HOST', os.getenv('REDIS_URL', 'redis://localhost:6379').split('://')[1].split(':')[0] if '://' in os.getenv('REDIS_URL', 'redis://localhost:6379') else 'localhost'),
                'port': port or int(os.getenv('REDIS_PORT', 6379)),
                'password': password or os.getenv('REDIS_PASSWORD'),
                'db': db or int(os.getenv('REDIS_DB', 0)),
                'decode_responses': decode_responses,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            }
            
            # Remove None password if not provided
            if not self._connection_params['password']:
                del self._connection_params['password']
            
            # Create Redis client
            self.client = redis.Redis(**self._connection_params)
            
            # Test connection
            self.client.ping()
            
            self._is_connected = True
            logger.info(f"Connected to Redis at {self._connection_params['host']}:{self._connection_params['port']}")
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._is_connected = False
            return False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self._is_connected or not self.client:
            return False
        
        try:
            self.client.ping()
            return True
        except Exception:
            self._is_connected = False
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        try:
            if not self.client:
                return {
                    "status": "error",
                    "message": "Redis client not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test connection and measure response time
            start_time = datetime.utcnow()
            self.client.ping()
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = self.client.info()
            
            return {
                "status": "healthy",
                "message": "Redis connection is healthy",
                "response_time_ms": round(response_time, 2),
                "redis_version": info.get('redis_version', 'unknown'),
                "used_memory_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except (ConnectionError, TimeoutError):
            return {
                "status": "error",
                "message": "Redis connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Basic Redis operations
    def set(self, key: str, value: Any, ex: int = None, px: int = None, 
            nx: bool = False, xx: bool = False) -> bool:
        """Set a key-value pair"""
        if not self.client:
            return False
        
        try:
            # Serialize complex objects
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value)
            elif not isinstance(value, (str, int, float, bytes)):
                value = pickle.dumps(value)
            
            return self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by key"""
        if not self.client:
            return default
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Try to deserialize pickle
            try:
                return pickle.loads(value)
            except (pickle.PickleError, TypeError):
                pass
            
            # Return as string
            return value
            
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return default
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if not self.client:
            return 0
        
        try:
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting Redis keys {keys}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking Redis key existence {key}: {e}")
            return False
    
    def expire(self, key: str, time: int) -> bool:
        """Set expiration time for a key"""
        if not self.client:
            return False
        
        try:
            return self.client.expire(key, time)
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key"""
        if not self.client:
            return -1
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for Redis key {key}: {e}")
            return -1
    
    # Hash operations
    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields"""
        if not self.client:
            return 0
        
        try:
            # Serialize complex values
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list, tuple)):
                    serialized_mapping[k] = json.dumps(v)
                elif not isinstance(v, (str, int, float, bytes)):
                    serialized_mapping[k] = pickle.dumps(v)
                else:
                    serialized_mapping[k] = v
            
            return self.client.hset(name, mapping=serialized_mapping)
        except Exception as e:
            logger.error(f"Error setting Redis hash {name}: {e}")
            return 0
    
    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """Get hash field value"""
        if not self.client:
            return default
        
        try:
            value = self.client.hget(name, key)
            if value is None:
                return default
            
            # Try to deserialize
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            
            try:
                return pickle.loads(value)
            except (pickle.PickleError, TypeError):
                pass
            
            return value
            
        except Exception as e:
            logger.error(f"Error getting Redis hash field {name}.{key}: {e}")
            return default
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.client:
            return {}
        
        try:
            hash_data = self.client.hgetall(name)
            result = {}
            
            for k, v in hash_data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    try:
                        result[k] = pickle.loads(v)
                    except (pickle.PickleError, TypeError):
                        result[k] = v
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Redis hash {name}: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        if not self.client:
            return 0
        
        try:
            return self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Error deleting Redis hash fields {name}.{keys}: {e}")
            return 0
    
    # List operations
    def lpush(self, name: str, *values: Any) -> int:
        """Push values to the left of a list"""
        if not self.client:
            return 0
        
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, tuple)):
                    serialized_values.append(json.dumps(value))
                elif not isinstance(value, (str, int, float, bytes)):
                    serialized_values.append(pickle.dumps(value))
                else:
                    serialized_values.append(value)
            
            return self.client.lpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Error pushing to Redis list {name}: {e}")
            return 0
    
    def rpop(self, name: str, default: Any = None) -> Any:
        """Pop value from the right of a list"""
        if not self.client:
            return default
        
        try:
            value = self.client.rpop(name)
            if value is None:
                return default
            
            # Try to deserialize
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass
            
            try:
                return pickle.loads(value)
            except (pickle.PickleError, TypeError):
                pass
            
            return value
            
        except Exception as e:
            logger.error(f"Error popping from Redis list {name}: {e}")
            return default
    
    def llen(self, name: str) -> int:
        """Get list length"""
        if not self.client:
            return 0
        
        try:
            return self.client.llen(name)
        except Exception as e:
            logger.error(f"Error getting Redis list length {name}: {e}")
            return 0
    
    # Session management
    def create_session(self, session_id: str, user_data: Dict[str, Any], 
                      expiry_hours: int = 24) -> bool:
        """Create a user session"""
        session_key = f"session:{session_id}"
        expiry_seconds = expiry_hours * 3600
        
        session_data = {
            'user_data': user_data,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat()
        }
        
        return self.set(session_key, session_data, ex=expiry_seconds)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        session_key = f"session:{session_id}"
        return self.get(session_key)
    
    def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_key = f"session:{session_id}"
        session_data = self.get_session(session_id)
        
        if not session_data:
            return False
        
        session_data['user_data'].update(user_data)
        session_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Preserve existing TTL
        ttl_seconds = self.ttl(session_key)
        if ttl_seconds > 0:
            return self.set(session_key, session_data, ex=ttl_seconds)
        else:
            return self.set(session_key, session_data)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        session_key = f"session:{session_id}"
        return self.delete(session_key) > 0
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiry"""
        session_key = f"session:{session_id}"
        if self.exists(session_key):
            return self.expire(session_key, hours * 3600)
        return False
    
    # Cache management
    def cache_set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set cache with TTL"""
        cache_key = f"cache:{key}"
        return self.set(cache_key, value, ex=ttl_seconds)
    
    def cache_get(self, key: str, default: Any = None) -> Any:
        """Get cached value"""
        cache_key = f"cache:{key}"
        return self.get(cache_key, default)
    
    def cache_delete(self, key: str) -> bool:
        """Delete cached value"""
        cache_key = f"cache:{key}"
        return self.delete(cache_key) > 0
    
    def cache_clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            cache_pattern = f"cache:{pattern}"
            keys = self.client.keys(cache_pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0
    
    # Utility methods
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        if not self.client:
            return []
        
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting Redis keys with pattern {pattern}: {e}")
            return []
    
    def flushdb(self) -> bool:
        """Clear current database"""
        if not self.client:
            return False
        
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    def info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        if not self.client:
            return {}
        
        try:
            return self.client.info()
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {}
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("Redis connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global Redis service instance
redis_service = RedisService()