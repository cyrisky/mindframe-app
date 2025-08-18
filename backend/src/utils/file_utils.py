"""File utility functions"""

import os
import shutil
import hashlib
import mimetypes
import tempfile
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime
import uuid
import logging
import zipfile
import tarfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileUtils:
    """Utility class for file operations"""
    
    # Allowed file extensions for different types
    ALLOWED_EXTENSIONS = {
        'pdf': ['.pdf'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'document': ['.doc', '.docx', '.txt', '.rtf', '.odt'],
        'template': ['.html', '.htm', '.jinja2', '.j2'],
        'data': ['.json', '.xml', '.csv', '.xlsx', '.xls'],
        'archive': ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.rar']
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'pdf': 50 * 1024 * 1024,  # 50MB
        'image': 10 * 1024 * 1024,  # 10MB
        'document': 25 * 1024 * 1024,  # 25MB
        'template': 5 * 1024 * 1024,  # 5MB
        'data': 100 * 1024 * 1024,  # 100MB
        'archive': 200 * 1024 * 1024  # 200MB
    }
    
    @staticmethod
    def ensure_directory(directory_path: Union[str, Path]) -> bool:
        """Ensure directory exists, create if it doesn't"""
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create a safe filename by removing/replacing dangerous characters"""
        # Remove or replace dangerous characters
        safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        safe_name = ''.join(c for c in filename if c in safe_chars)
        
        # Remove multiple spaces and replace with single space
        safe_name = ' '.join(safe_name.split())
        
        # Ensure filename is not empty
        if not safe_name.strip():
            safe_name = f"file_{uuid.uuid4().hex[:8]}"
        
        # Limit length
        if len(safe_name) > 200:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:200-len(ext)] + ext
        
        return safe_name
    
    @staticmethod
    def generate_unique_filename(base_name: str, extension: str = None, 
                               directory: str = None) -> str:
        """Generate a unique filename"""
        if extension and not extension.startswith('.'):
            extension = f'.{extension}'
        
        # Clean base name
        clean_base = FileUtils.safe_filename(base_name)
        if extension:
            clean_base = os.path.splitext(clean_base)[0]
        
        # Add timestamp and UUID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        filename = f"{clean_base}_{timestamp}_{unique_id}"
        if extension:
            filename += extension
        
        # Ensure uniqueness in directory
        if directory:
            counter = 1
            original_filename = filename
            while os.path.exists(os.path.join(directory, filename)):
                name, ext = os.path.splitext(original_filename)
                filename = f"{name}_{counter}{ext}"
                counter += 1
        
        return filename
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        try:
            hash_func = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            path = Path(file_path)
            stat = path.stat()
            
            # Get MIME type
            mime_type, encoding = mimetypes.guess_type(str(path))
            
            return {
                'name': path.name,
                'stem': path.stem,
                'suffix': path.suffix,
                'size': stat.st_size,
                'size_human': FileUtils.format_file_size(stat.st_size),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'mime_type': mime_type,
                'encoding': encoding,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'exists': path.exists(),
                'absolute_path': str(path.absolute()),
                'hash_sha256': FileUtils.get_file_hash(path, 'sha256') if path.is_file() else None
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {}
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def validate_file_type(file_path: Union[str, Path], 
                          allowed_types: List[str]) -> Dict[str, Any]:
        """Validate file type against allowed types"""
        try:
            path = Path(file_path)
            extension = path.suffix.lower()
            
            # Check against allowed extensions
            allowed_extensions = []
            for file_type in allowed_types:
                if file_type in FileUtils.ALLOWED_EXTENSIONS:
                    allowed_extensions.extend(FileUtils.ALLOWED_EXTENSIONS[file_type])
            
            is_valid = extension in allowed_extensions
            
            return {
                'valid': is_valid,
                'extension': extension,
                'allowed_extensions': allowed_extensions,
                'file_type': FileUtils.get_file_type_from_extension(extension)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def validate_file_size(file_path: Union[str, Path], 
                          file_type: str = None) -> Dict[str, Any]:
        """Validate file size against limits"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {'valid': False, 'error': 'File does not exist'}
            
            file_size = path.stat().st_size
            
            # Determine file type if not provided
            if not file_type:
                extension = path.suffix.lower()
                file_type = FileUtils.get_file_type_from_extension(extension)
            
            # Get size limit
            max_size = FileUtils.MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)  # Default 10MB
            
            is_valid = file_size <= max_size
            
            return {
                'valid': is_valid,
                'file_size': file_size,
                'file_size_human': FileUtils.format_file_size(file_size),
                'max_size': max_size,
                'max_size_human': FileUtils.format_file_size(max_size),
                'file_type': file_type
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_file_type_from_extension(extension: str) -> str:
        """Get file type category from extension"""
        extension = extension.lower()
        for file_type, extensions in FileUtils.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        return 'unknown'
    
    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path], 
                 create_dirs: bool = True) -> bool:
        """Copy file from source to destination"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, dest_path)
            logger.info(f"File copied from {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def move_file(source: Union[str, Path], destination: Union[str, Path], 
                 create_dirs: bool = True) -> bool:
        """Move file from source to destination"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source}")
                return False
            
            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            logger.info(f"File moved from {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file from {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """Delete file safely"""
        try:
            path = Path(file_path)
            if path.exists():
                if path.is_file():
                    path.unlink()
                    logger.info(f"File deleted: {file_path}")
                    return True
                else:
                    logger.error(f"Path is not a file: {file_path}")
                    return False
            else:
                logger.warning(f"File does not exist: {file_path}")
                return True  # Consider it successful if file doesn't exist
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    @staticmethod
    def delete_directory(directory_path: Union[str, Path], 
                        recursive: bool = False) -> bool:
        """Delete directory"""
        try:
            path = Path(directory_path)
            if path.exists():
                if path.is_dir():
                    if recursive:
                        shutil.rmtree(path)
                    else:
                        path.rmdir()  # Only works if directory is empty
                    logger.info(f"Directory deleted: {directory_path}")
                    return True
                else:
                    logger.error(f"Path is not a directory: {directory_path}")
                    return False
            else:
                logger.warning(f"Directory does not exist: {directory_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete directory {directory_path}: {e}")
            return False
    
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", 
                  recursive: bool = False) -> List[Dict[str, Any]]:
        """List files in directory with information"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return []
            
            if recursive:
                files = path.rglob(pattern)
            else:
                files = path.glob(pattern)
            
            file_list = []
            for file_path in files:
                if file_path.is_file():
                    file_info = FileUtils.get_file_info(file_path)
                    file_info['relative_path'] = str(file_path.relative_to(path))
                    file_list.append(file_info)
            
            return sorted(file_list, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    @staticmethod
    def create_archive(source_path: Union[str, Path], 
                      archive_path: Union[str, Path],
                      archive_type: str = 'zip') -> bool:
        """Create archive from source path"""
        try:
            source = Path(source_path)
            archive = Path(archive_path)
            
            if not source.exists():
                logger.error(f"Source path does not exist: {source}")
                return False
            
            # Ensure archive directory exists
            archive.parent.mkdir(parents=True, exist_ok=True)
            
            if archive_type.lower() == 'zip':
                with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if source.is_file():
                        zipf.write(source, source.name)
                    else:
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(source.parent)
                                zipf.write(file_path, arcname)
            
            elif archive_type.lower() in ['tar', 'tar.gz', 'tgz']:
                mode = 'w:gz' if archive_type.lower() in ['tar.gz', 'tgz'] else 'w'
                with tarfile.open(archive, mode) as tarf:
                    tarf.add(source, arcname=source.name)
            
            else:
                logger.error(f"Unsupported archive type: {archive_type}")
                return False
            
            logger.info(f"Archive created: {archive}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create archive: {e}")
            return False
    
    @staticmethod
    def extract_archive(archive_path: Union[str, Path], 
                       extract_path: Union[str, Path]) -> bool:
        """Extract archive to specified path"""
        try:
            archive = Path(archive_path)
            extract_dir = Path(extract_path)
            
            if not archive.exists():
                logger.error(f"Archive does not exist: {archive}")
                return False
            
            # Ensure extract directory exists
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            if archive.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive, 'r') as zipf:
                    zipf.extractall(extract_dir)
            
            elif archive.suffix.lower() in ['.tar', '.gz', '.bz2']:
                with tarfile.open(archive, 'r:*') as tarf:
                    tarf.extractall(extract_dir)
            
            else:
                logger.error(f"Unsupported archive format: {archive.suffix}")
                return False
            
            logger.info(f"Archive extracted to: {extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            return False
    
    @staticmethod
    @contextmanager
    def temporary_file(suffix: str = None, prefix: str = None, 
                      delete: bool = True):
        """Context manager for temporary files"""
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=suffix, prefix=prefix, delete=delete
            )
            yield temp_file
        finally:
            if temp_file and not temp_file.closed:
                temp_file.close()
    
    @staticmethod
    @contextmanager
    def temporary_directory(prefix: str = None):
        """Context manager for temporary directories"""
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            yield temp_dir
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    @staticmethod
    def cleanup_old_files(directory: Union[str, Path], 
                         max_age_days: int = 30,
                         pattern: str = "*") -> int:
        """Clean up old files in directory"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete old file {file_path}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old files from {directory}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files in {directory}: {e}")
            return 0
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """Get total size of directory in bytes"""
        try:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                return 0
            
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get directory size for {directory}: {e}")
            return 0
    
    @staticmethod
    def read_file_content(file_path: Union[str, Path], 
                         encoding: str = 'utf-8') -> Optional[str]:
        """Read file content as string"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    @staticmethod
    def write_file_content(file_path: Union[str, Path], content: str,
                          encoding: str = 'utf-8', create_dirs: bool = True) -> bool:
        """Write content to file"""
        try:
            path = Path(file_path)
            
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"Content written to file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False