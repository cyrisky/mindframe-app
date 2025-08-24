import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from rq import get_current_job
from rq.job import Job
from .config import get_pdf_queue

# Import database services
from src.services.database_service import DatabaseService
from src.services.pdf_job_service import PDFJobService

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
_db_service = None
_pdf_job_service = None

def get_database_service():
    """Get database service with lazy initialization"""
    global _db_service
    if _db_service is None:
        try:
            import os
            _db_service = DatabaseService()
            # Initialize with environment variables
            connection_string = os.getenv('MONGODB_URI')
            database_name = os.getenv('MONGODB_DB', 'mindframe_app')
            
            if not _db_service.initialize(connection_string, database_name):
                logger.warning("Database service initialization failed")
                _db_service = None
                return None
                
            logger.info("Database service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            _db_service = None
            return None
    return _db_service

def get_pdf_job_service():
    """Get PDF job service with lazy initialization"""
    global _pdf_job_service
    if _pdf_job_service is None:
        db_service = get_database_service()
        if db_service is None:
            logger.error("Cannot initialize PDF job service: database not available")
            return None
        try:
            _pdf_job_service = PDFJobService(db_service)
        except Exception as e:
            logger.error(f"Failed to initialize PDF job service: {e}")
            return None
    return _pdf_job_service

def generate_job_id() -> str:
    """Generate a unique job ID"""
    return str(uuid.uuid4())

def submit_pdf_job(code: str, 
                   product_id: str, 
                   user_email: Optional[str] = None,
                   user_name: Optional[str] = None,
                   callback_url: Optional[str] = None) -> Dict[str, Any]:
    """Submit a PDF generation job to the queue
    
    Args:
        code: Test code to generate PDF for
        product_id: Product configuration ID
        user_email: Optional user email
        user_name: Optional user name
        callback_url: Optional webhook URL for completion notification
        
    Returns:
        Dict containing job information
    """
    queue = get_pdf_queue()
    
    # Submit job to queue with new worker function
    job = queue.enqueue(
        'job_queue.workers.generate_pdf_worker',
        code,
        product_id,
        user_email=user_email,
        user_name=user_name,
        callback_url=callback_url,
        job_timeout='30m',
        result_ttl=86400  # Keep results for 24 hours
    )
    
    # Create database record
    pdf_job_service = get_pdf_job_service()
    if pdf_job_service:
        try:
            pdf_job_service.create_job(
                job_id=job.id,
                code=code,
                product_id=product_id,
                user_email=user_email,
                user_name=user_name,
                callback_url=callback_url,
                metadata={'code': code, 'product_id': product_id}
            )
            logger.info(f"Created database record for PDF job {job.id}")
        except Exception as e:
            logger.error(f"Failed to create database record for job {job.id}: {e}")
    else:
        logger.warning(f"PDF job service not available, skipping database record for job {job.id}")
    
    # Return job information
    return {
        'job_id': job.id,
        'status': 'queued',
        'created_at': datetime.utcnow().isoformat(),
        'estimated_completion': None  # Could be calculated based on queue length
    }

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status and result
    
    Args:
        job_id: The job ID to check
        
    Returns:
        Dict containing job status information
    """
    from .config import get_pdf_queue
    
    try:
        # First check database for job status
        pdf_job_service = get_pdf_job_service()
        if pdf_job_service:
            job_result = pdf_job_service.get_job_by_id(job_id)
            if job_result:
                # Calculate progress based on status
                progress = 0
                if job_result.status == 'queued':
                    progress = 0
                elif job_result.status == 'started':
                    progress = 50
                elif job_result.status in ['completed', 'failed']:
                    progress = 100
                
                # Prepare result data
                result_data = None
                if job_result.status == 'completed' and job_result.google_drive_webview_link:
                    result_data = {
                        'pdf_url': job_result.google_drive_webview_link,
                        'pdf_filename': job_result.pdf_filename,
                        'google_drive_link': job_result.google_drive_webview_link
                    }
                
                return {
                    'job_id': job_id,
                    'status': job_result.status,
                    'progress': progress,
                    'message': f'Job status: {job_result.status}',
                    'result': result_data,
                    'error': job_result.error_message,
                    'created_at': job_result.created_at.isoformat() if job_result.created_at else None,
                    'updated_at': job_result.updated_at.isoformat() if hasattr(job_result, 'updated_at') and job_result.updated_at else None,
                    'completed_at': job_result.completed_at.isoformat() if job_result.completed_at else None
                }
        
        # Fallback to queue check
        queue = get_pdf_queue()
        
        # Check if job exists in queue
        if job_id in queue.job_ids:
            return {
                'job_id': job_id,
                'status': 'queued',
                'progress': 0,
                'message': 'Job is queued for processing',
                'result': None,
                'error': None,
                'created_at': None,
                'updated_at': None,
                'completed_at': None
            }
        
        # For now, if not in queue, assume it's not found
        # TODO: Check other registries (started, finished, failed) when serialization issue is resolved
        return None
        
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return None

def cancel_job(job_id: str) -> bool:
    """Cancel a queued or running job
    
    Args:
        job_id: The job ID to cancel
        
    Returns:
        bool: True if job was canceled, False otherwise
    """
    from .config import get_pdf_queue
    
    try:
        queue = get_pdf_queue()
        job = queue.fetch_job(job_id)
        if job and not job.is_finished:
            job.cancel()
            return True
        return False
    except Exception:
        return False