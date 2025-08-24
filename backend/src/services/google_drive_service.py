#!/usr/bin/env python3
"""
Google Drive Service for uploading files
Handles authentication and file upload operations to Google Drive
"""

import os
import logging
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveService:
    """
    Service class for Google Drive operations
    Handles authentication and file upload using service account credentials
    """
    
    def __init__(self, credentials_path: str, folder_id: Optional[str] = None):
        """
        Initialize Google Drive service
        
        Args:
            credentials_path (str): Path to service account JSON credentials file
            folder_id (str, optional): Default folder ID for uploads
        """
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = None
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        
        # Initialize the service
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Authenticate with Google Drive API using service account credentials
        """
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.scopes
            )
            
            # Build the Drive service
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Successfully authenticated with Google Drive API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Drive: {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if the Google Drive service is working properly
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            if not self.service:
                return False
            
            # Try to list files (limit to 1 to minimize API usage)
            self.service.files().list(pageSize=1, supportsAllDrives=True).execute()
            return True
            
        except Exception as e:
            logger.error(f"Google Drive health check failed: {str(e)}")
            return False
    
    def upload_file(
        self, 
        file_path: str, 
        file_name: Optional[str] = None,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive
        
        Args:
            file_path (str): Local path to the file to upload
            file_name (str, optional): Name for the file in Drive (defaults to original filename)
            folder_id (str, optional): Folder ID to upload to (defaults to instance folder_id)
            mime_type (str, optional): MIME type of the file (auto-detected if not provided)
        
        Returns:
            Dict[str, Any]: Upload result containing file ID, name, and web view link
        
        Raises:
            FileNotFoundError: If the local file doesn't exist
            HttpError: If the upload fails
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not self.service:
                raise RuntimeError("Google Drive service not initialized")
            
            # Use provided file name or extract from path
            if not file_name:
                file_name = os.path.basename(file_path)
            
            # Use provided folder ID or instance default
            target_folder_id = folder_id or self.folder_id
            
            # Prepare file metadata
            file_metadata = {
                'name': file_name
            }
            
            # Add parent folder if specified
            if target_folder_id:
                file_metadata['parents'] = [target_folder_id]
            
            # Create media upload object
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload the file
            logger.info(f"Uploading file: {file_name} to Google Drive")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size,mimeType,createdTime',
                supportsAllDrives=True
            ).execute()
            
            logger.info(f"Successfully uploaded file: {file.get('name')} (ID: {file.get('id')})")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_view_link': file.get('webViewLink'),
                'size': file.get('size'),
                'mime_type': file.get('mimeType'),
                'created_time': file.get('createdTime'),
                'message': f"File '{file.get('name')}' uploaded successfully"
            }
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'File not found'
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to upload file to Google Drive'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Unexpected error during file upload'
            }
    
    def list_files(self, folder_id: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
        """
        List files in Google Drive
        
        Args:
            folder_id (str, optional): Folder ID to list files from
            max_results (int): Maximum number of files to return
        
        Returns:
            Dict[str, Any]: List of files with metadata
        """
        try:
            if not self.service:
                raise RuntimeError("Google Drive service not initialized")
            
            # Build query
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            # List files
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id,name,size,mimeType,createdTime,webViewLink)",
                supportsAllDrives=True
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'success': True,
                'files': files,
                'count': len(files),
                'message': f"Found {len(files)} files"
            }
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to list files'
            }
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a file from Google Drive
        
        Args:
            file_id (str): ID of the file to delete
        
        Returns:
            Dict[str, Any]: Deletion result
        """
        try:
            if not self.service:
                raise RuntimeError("Google Drive service not initialized")
            
            # Delete the file
            self.service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            
            logger.info(f"Successfully deleted file with ID: {file_id}")
            
            return {
                'success': True,
                'file_id': file_id,
                'message': f"File with ID '{file_id}' deleted successfully"
            }
            
        except HttpError as e:
            logger.error(f"Google Drive API error during deletion: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to delete file from Google Drive'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during file deletion: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Unexpected error during file deletion'
            }