"""Storage service for file management and cloud storage integration"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import hashlib
import mimetypes
import logging
from google.cloud import storage as gcs
from google.cloud.exceptions import NotFound, GoogleCloudError

logger = logging.getLogger(__name__)


class StorageService:
    """Service for file storage operations (local and cloud)"""
    
    def __init__(self):
        self.local_storage_path = None
        self.gcs_client = None
        self.gcs_bucket = None
        self.bucket_name = None
        self._initialized = False
    
    def initialize(self, local_storage_path: str = None, 
                   gcs_credentials_path: str = None,
                   gcs_bucket_name: str = None) -> bool:
        """Initialize storage service"""
        try:
            # Setup local storage
            self.local_storage_path = Path(local_storage_path or os.getenv(
                'LOCAL_STORAGE_PATH', 
                '/tmp/mindframe_storage'
            ))
            
            # Create local storage directory
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.local_storage_path / 'pdfs').mkdir(exist_ok=True)
            (self.local_storage_path / 'templates').mkdir(exist_ok=True)
            (self.local_storage_path / 'uploads').mkdir(exist_ok=True)
            (self.local_storage_path / 'temp').mkdir(exist_ok=True)
            
            # Setup Google Cloud Storage if credentials provided
            gcs_creds = gcs_credentials_path or os.getenv('GOOGLE_CLOUD_CREDENTIALS')
            self.bucket_name = gcs_bucket_name or os.getenv('GCS_BUCKET_NAME')
            
            if gcs_creds and self.bucket_name:
                try:
                    if gcs_creds and os.path.exists(gcs_creds):
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcs_creds
                    
                    self.gcs_client = gcs.Client()
                    self.gcs_bucket = self.gcs_client.bucket(self.bucket_name)
                    
                    # Test bucket access
                    self.gcs_bucket.exists()
                    logger.info(f"Connected to Google Cloud Storage bucket: {self.bucket_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize Google Cloud Storage: {e}")
                    self.gcs_client = None
                    self.gcs_bucket = None
            
            self._initialized = True
            logger.info(f"Storage service initialized with local path: {self.local_storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize storage service: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform storage health check"""
        try:
            health_info = {
                "status": "healthy",
                "local_storage": {
                    "available": True,
                    "path": str(self.local_storage_path),
                    "writable": os.access(self.local_storage_path, os.W_OK),
                    "free_space_mb": 0
                },
                "cloud_storage": {
                    "available": self.gcs_bucket is not None,
                    "bucket_name": self.bucket_name
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check local storage space
            if self.local_storage_path.exists():
                stat = shutil.disk_usage(self.local_storage_path)
                health_info["local_storage"]["free_space_mb"] = round(stat.free / 1024 / 1024, 2)
            
            # Test cloud storage if available
            if self.gcs_bucket:
                try:
                    self.gcs_bucket.exists()
                    health_info["cloud_storage"]["accessible"] = True
                except Exception as e:
                    health_info["cloud_storage"]["accessible"] = False
                    health_info["cloud_storage"]["error"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Storage health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        if not file_path.exists():
            return {}
        
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "mime_type": mime_type,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": self._generate_file_hash(file_path)
        }
    
    # Local storage operations
    def save_file(self, file_data: bytes, filename: str, 
                  subdirectory: str = "uploads") -> Dict[str, Any]:
        """Save file to local storage"""
        try:
            # Create subdirectory if it doesn't exist
            storage_dir = self.local_storage_path / subdirectory
            storage_dir.mkdir(exist_ok=True)
            
            # Generate unique filename if file exists
            file_path = storage_dir / filename
            counter = 1
            base_name = file_path.stem
            extension = file_path.suffix
            
            while file_path.exists():
                new_name = f"{base_name}_{counter}{extension}"
                file_path = storage_dir / new_name
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Get file info
            file_info = self._get_file_info(file_path)
            file_info.update({
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.local_storage_path)),
                "subdirectory": subdirectory,
                "url": f"/storage/{subdirectory}/{file_path.name}"
            })
            
            logger.info(f"Saved file: {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise
    
    def save_file_from_stream(self, file_stream: BinaryIO, filename: str,
                             subdirectory: str = "uploads") -> Dict[str, Any]:
        """Save file from stream to local storage"""
        file_data = file_stream.read()
        return self.save_file(file_data, filename, subdirectory)
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """Get file content from local storage"""
        try:
            full_path = self.local_storage_path / file_path
            if not full_path.exists():
                return None
            
            with open(full_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            full_path = self.local_storage_path / file_path
            if not full_path.exists():
                return None
            
            return self._get_file_info(full_path)
            
        except Exception as e:
            logger.error(f"Error getting file info {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self.local_storage_path / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {full_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def list_files(self, subdirectory: str = None, 
                   pattern: str = "*") -> List[Dict[str, Any]]:
        """List files in storage"""
        try:
            if subdirectory:
                search_path = self.local_storage_path / subdirectory
            else:
                search_path = self.local_storage_path
            
            if not search_path.exists():
                return []
            
            files = []
            for file_path in search_path.glob(pattern):
                if file_path.is_file():
                    file_info = self._get_file_info(file_path)
                    file_info.update({
                        "path": str(file_path),
                        "relative_path": str(file_path.relative_to(self.local_storage_path)),
                        "subdirectory": file_path.parent.name
                    })
                    files.append(file_info)
            
            return sorted(files, key=lambda x: x["modified_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing files in {subdirectory}: {e}")
            return []
    
    def move_file(self, source_path: str, destination_path: str) -> bool:
        """Move file within local storage"""
        try:
            source = self.local_storage_path / source_path
            destination = self.local_storage_path / destination_path
            
            if not source.exists():
                return False
            
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source), str(destination))
            logger.info(f"Moved file from {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return False
    
    def copy_file(self, source_path: str, destination_path: str) -> bool:
        """Copy file within local storage"""
        try:
            source = self.local_storage_path / source_path
            destination = self.local_storage_path / destination_path
            
            if not source.exists():
                return False
            
            # Create destination directory if needed
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(str(source), str(destination))
            logger.info(f"Copied file from {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file from {source_path} to {destination_path}: {e}")
            return False
    
    # Cloud storage operations
    def upload_to_cloud(self, local_file_path: str, 
                       cloud_file_path: str = None) -> Optional[str]:
        """Upload file to Google Cloud Storage"""
        if not self.gcs_bucket:
            logger.warning("Google Cloud Storage not configured")
            return None
        
        try:
            full_local_path = self.local_storage_path / local_file_path
            if not full_local_path.exists():
                logger.error(f"Local file not found: {full_local_path}")
                return None
            
            # Use local path as cloud path if not specified
            if not cloud_file_path:
                cloud_file_path = local_file_path
            
            blob = self.gcs_bucket.blob(cloud_file_path)
            blob.upload_from_filename(str(full_local_path))
            
            logger.info(f"Uploaded {local_file_path} to cloud as {cloud_file_path}")
            return f"gs://{self.bucket_name}/{cloud_file_path}"
            
        except Exception as e:
            logger.error(f"Error uploading to cloud: {e}")
            return None
    
    def download_from_cloud(self, cloud_file_path: str, 
                           local_file_path: str = None) -> Optional[str]:
        """Download file from Google Cloud Storage"""
        if not self.gcs_bucket:
            logger.warning("Google Cloud Storage not configured")
            return None
        
        try:
            # Use cloud path as local path if not specified
            if not local_file_path:
                local_file_path = cloud_file_path
            
            full_local_path = self.local_storage_path / local_file_path
            
            # Create directory if needed
            full_local_path.parent.mkdir(parents=True, exist_ok=True)
            
            blob = self.gcs_bucket.blob(cloud_file_path)
            blob.download_to_filename(str(full_local_path))
            
            logger.info(f"Downloaded {cloud_file_path} from cloud to {local_file_path}")
            return str(full_local_path)
            
        except NotFound:
            logger.error(f"Cloud file not found: {cloud_file_path}")
            return None
        except Exception as e:
            logger.error(f"Error downloading from cloud: {e}")
            return None
    
    def delete_from_cloud(self, cloud_file_path: str) -> bool:
        """Delete file from Google Cloud Storage"""
        if not self.gcs_bucket:
            logger.warning("Google Cloud Storage not configured")
            return False
        
        try:
            blob = self.gcs_bucket.blob(cloud_file_path)
            blob.delete()
            
            logger.info(f"Deleted {cloud_file_path} from cloud")
            return True
            
        except NotFound:
            logger.warning(f"Cloud file not found for deletion: {cloud_file_path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting from cloud: {e}")
            return False
    
    def list_cloud_files(self, prefix: str = None) -> List[Dict[str, Any]]:
        """List files in Google Cloud Storage"""
        if not self.gcs_bucket:
            logger.warning("Google Cloud Storage not configured")
            return []
        
        try:
            blobs = self.gcs_bucket.list_blobs(prefix=prefix)
            files = []
            
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "created_at": blob.time_created.isoformat() if blob.time_created else None,
                    "updated_at": blob.updated.isoformat() if blob.updated else None,
                    "content_type": blob.content_type,
                    "md5_hash": blob.md5_hash,
                    "public_url": blob.public_url
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing cloud files: {e}")
            return []
    
    # Utility methods
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours"""
        try:
            temp_dir = self.local_storage_path / 'temp'
            if not temp_dir.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
            deleted_count = 0
            
            for file_path in temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} temporary files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            usage = {
                "total_files": 0,
                "total_size_mb": 0,
                "by_subdirectory": {}
            }
            
            for subdir in self.local_storage_path.iterdir():
                if subdir.is_dir():
                    subdir_files = 0
                    subdir_size = 0
                    
                    for file_path in subdir.rglob('*'):
                        if file_path.is_file():
                            subdir_files += 1
                            subdir_size += file_path.stat().st_size
                    
                    usage["by_subdirectory"][subdir.name] = {
                        "files": subdir_files,
                        "size_mb": round(subdir_size / 1024 / 1024, 2)
                    }
                    
                    usage["total_files"] += subdir_files
                    usage["total_size_mb"] += subdir_size / 1024 / 1024
            
            usage["total_size_mb"] = round(usage["total_size_mb"], 2)
            return usage
            
        except Exception as e:
            logger.error(f"Error getting storage usage: {e}")
            return {}
    
    def create_backup(self, backup_name: str = None) -> Optional[str]:
        """Create backup of local storage"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = self.local_storage_path.parent / f"{backup_name}.tar.gz"
            
            import tarfile
            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(self.local_storage_path, arcname=backup_name)
            
            logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None


# Global storage service instance
storage_service = StorageService()