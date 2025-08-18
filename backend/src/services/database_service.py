"""Database service for MongoDB operations"""

import os
from typing import Optional, Dict, Any, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, OperationFailure
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for MongoDB database operations"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._connection_string = None
        self._database_name = None
        self._is_connected = False
    
    def initialize(self, connection_string: str = None, database_name: str = None) -> bool:
        """Initialize database connection"""
        try:
            # Use provided parameters or environment variables
            self._connection_string = connection_string or os.getenv(
                'MONGODB_URI', 
                'mongodb://localhost:27017'
            )
            self._database_name = database_name or os.getenv(
                'MONGODB_DATABASE', 
                'mindframe_app'
            )
            
            # Create MongoDB client
            self.client = MongoClient(
                self._connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connection timeout
                socketTimeoutMS=20000,   # 20 second socket timeout
                maxPoolSize=50,          # Maximum connection pool size
                retryWrites=True
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[self._database_name]
            
            # Create indexes
            self._create_indexes()
            
            self._is_connected = True
            logger.info(f"Connected to MongoDB database: {self._database_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self._is_connected = False
            return False
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # PDF documents indexes
            pdf_collection = self.get_collection('pdf_documents')
            pdf_collection.create_index('filename')
            pdf_collection.create_index('user_id')
            pdf_collection.create_index('created_at')
            pdf_collection.create_index('status')
            pdf_collection.create_index('expires_at')
            pdf_collection.create_index([('user_id', 1), ('created_at', -1)])
            
            # Templates indexes
            template_collection = self.get_collection('templates')
            template_collection.create_index('name', unique=True)
            template_collection.create_index('category')
            template_collection.create_index('status')
            template_collection.create_index('created_at')
            template_collection.create_index([('category', 1), ('status', 1)])
            
            # Users indexes
            user_collection = self.get_collection('users')
            user_collection.create_index('username', unique=True)
            user_collection.create_index('email', unique=True)
            user_collection.create_index('api_key')
            user_collection.create_index('is_active')
            user_collection.create_index('created_at')
            
            # Psychological reports indexes
            report_collection = self.get_collection('psychological_reports')
            report_collection.create_index('report_number', unique=True)
            report_collection.create_index('client_info.client_id')
            report_collection.create_index('psychologist_name')
            report_collection.create_index('status')
            report_collection.create_index('session_date')
            report_collection.create_index('created_at')
            report_collection.create_index([('client_info.client_id', 1), ('session_date', -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get a MongoDB collection"""
        if not self.database:
            raise RuntimeError("Database not initialized")
        return self.database[collection_name]
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        if not self._is_connected or not self.client:
            return False
        
        try:
            # Ping the database to check connection
            self.client.admin.command('ping')
            return True
        except Exception:
            self._is_connected = False
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            if not self.client:
                return {
                    "status": "error",
                    "message": "Database client not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test connection
            start_time = datetime.utcnow()
            result = self.client.admin.command('ping')
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Get server info
            server_info = self.client.server_info()
            
            # Get database stats
            db_stats = self.database.command('dbStats') if self.database else {}
            
            return {
                "status": "healthy",
                "message": "Database connection is healthy",
                "response_time_ms": round(response_time, 2),
                "server_version": server_info.get('version', 'unknown'),
                "database_name": self._database_name,
                "collections_count": len(self.database.list_collection_names()) if self.database else 0,
                "storage_size_mb": round(db_stats.get('storageSize', 0) / 1024 / 1024, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ConnectionFailure:
            return {
                "status": "error",
                "message": "Database connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document"""
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        collection = self.get_collection(collection_name)
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    def find_one(self, collection_name: str, filter_dict: Dict[str, Any] = None, 
                 projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        collection = self.get_collection(collection_name)
        return collection.find_one(filter_dict or {}, projection)
    
    def find_many(self, collection_name: str, filter_dict: Dict[str, Any] = None,
                  projection: Dict[str, Any] = None, sort: List[tuple] = None,
                  limit: int = None, skip: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        collection = self.get_collection(collection_name)
        cursor = collection.find(filter_dict or {}, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def update_one(self, collection_name: str, filter_dict: Dict[str, Any],
                   update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        """Update a single document"""
        collection = self.get_collection(collection_name)
        result = collection.update_one(filter_dict, update_dict, upsert=upsert)
        return result.modified_count > 0 or (upsert and result.upserted_id is not None)
    
    def update_many(self, collection_name: str, filter_dict: Dict[str, Any],
                    update_dict: Dict[str, Any]) -> int:
        """Update multiple documents"""
        collection = self.get_collection(collection_name)
        result = collection.update_many(filter_dict, update_dict)
        return result.modified_count
    
    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document"""
        collection = self.get_collection(collection_name)
        result = collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents"""
        collection = self.get_collection(collection_name)
        result = collection.delete_many(filter_dict)
        return result.deleted_count
    
    def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in collection"""
        collection = self.get_collection(collection_name)
        return collection.count_documents(filter_dict or {})
    
    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute aggregation pipeline"""
        collection = self.get_collection(collection_name)
        return list(collection.aggregate(pipeline))
    
    def create_index(self, collection_name: str, keys: List[tuple], **kwargs):
        """Create an index on a collection"""
        collection = self.get_collection(collection_name)
        return collection.create_index(keys, **kwargs)
    
    def drop_collection(self, collection_name: str):
        """Drop a collection"""
        if self.database:
            self.database.drop_collection(collection_name)
    
    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        if not self.database:
            return []
        return self.database.list_collection_names()
    
    def backup_collection(self, collection_name: str, backup_path: str):
        """Backup a collection to a file"""
        import json
        
        collection = self.get_collection(collection_name)
        documents = list(collection.find())
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        with open(backup_path, 'w') as f:
            json.dump(documents, f, default=str, indent=2)
        
        logger.info(f"Backed up {len(documents)} documents from {collection_name} to {backup_path}")
    
    def restore_collection(self, collection_name: str, backup_path: str):
        """Restore a collection from a backup file"""
        import json
        from bson import ObjectId
        
        with open(backup_path, 'r') as f:
            documents = json.load(f)
        
        # Convert string IDs back to ObjectId
        for doc in documents:
            if '_id' in doc and isinstance(doc['_id'], str):
                try:
                    doc['_id'] = ObjectId(doc['_id'])
                except Exception:
                    # If conversion fails, remove the _id and let MongoDB generate a new one
                    del doc['_id']
        
        collection = self.get_collection(collection_name)
        if documents:
            collection.insert_many(documents)
        
        logger.info(f"Restored {len(documents)} documents to {collection_name} from {backup_path}")
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self._is_connected = False
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global database service instance
db_service = DatabaseService()