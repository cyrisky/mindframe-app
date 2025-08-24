import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from rq import get_current_job
from dotenv import load_dotenv

# Import database services
import sys
import os

# Add both src and backend directories to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, backend_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(backend_dir, '.env'))

# Import with absolute paths to avoid relative import issues
try:
    from src.services.database_service import DatabaseService
    from src.services.pdf_job_service import PDFJobService
    from src.services.pdf_service import PDFService
    from src.services.product_report_service import ProductReportService
    from src.utils.logging_utils import LoggingUtils
except ImportError:
    # Fallback to direct imports if src prefix doesn't work
    from services.database_service import DatabaseService
    from services.pdf_job_service import PDFJobService
    from services.pdf_service import PDFService
    from services.product_report_service import ProductReportService
    from utils.logging_utils import LoggingUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = LoggingUtils.get_logger(__name__)

# Global variables for lazy initialization
_db_service = None
_pdf_job_service = None
_pdf_service = None
_product_report_service = None

def get_database_service():
    """Get database service with lazy initialization"""
    global _db_service
    if _db_service is None:
        try:
            import os
            _db_service = DatabaseService()
            # Initialize with environment variables
            connection_string = os.getenv('MONGODB_URI')
            database_name = os.getenv('MONGODB_DB', 'mindframe')
            
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

def get_pdf_service():
    """Get PDF service with lazy initialization"""
    global _pdf_service
    if _pdf_service is None:
        try:
            _pdf_service = PDFService()
        except Exception as e:
            logger.error(f"Failed to initialize PDF service: {e}")
            return None
    return _pdf_service

def get_product_report_service():
    """Get product report service with lazy initialization"""
    global _product_report_service
    if _product_report_service is None:
        try:
            _product_report_service = ProductReportService()
        except Exception as e:
            logger.error(f"Failed to initialize product report service: {e}")
            return None
    return _product_report_service

def generate_pdf_worker(code: str, 
                       product_id: str, 
                       user_email: Optional[str] = None,
                       user_name: Optional[str] = None,
                       callback_url: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
    """Worker function to generate PDF reports"""
    
    # Get current job ID from RQ context
    current_job = get_current_job()
    job_id = current_job.id if current_job else "unknown"
    
    logger.info(f"Starting PDF generation worker", extra={
        'job_id': job_id,
        'code': code,
        'product_id': product_id,
        'user_email': user_email
    })
    
    try:
        # Get services with lazy initialization
        pdf_job_service = get_pdf_job_service()
        pdf_service = get_pdf_service()
        product_report_service = get_product_report_service()
        
        # Validate services are available
        if not all([pdf_job_service, pdf_service, product_report_service]):
            error_msg = "Required services not initialized"
            logger.error(error_msg, extra={'job_id': job_id})
            
            if pdf_job_service:
                pdf_job_service.mark_job_failed(job_id, error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'job_id': job_id
            }
        
        # Mark job as started
        pdf_job_service.mark_job_started(job_id)
        
        # Step 1: Call the API endpoint to generate the product report
        logger.info(f"Calling product report API", extra={'job_id': job_id, 'code': code, 'product_id': product_id})
        
        import requests
        import os
        
        # Get the API base URL from environment or use default
        api_base_url = os.getenv('API_BASE_URL', os.getenv('BASE_URL', 'http://localhost:5001'))
        api_url = f"{api_base_url}/api/reports/generate-product-report"
        
        # Prepare the request payload
        payload = {
            'code': code,
            'productId': product_id
        }
        
        try:
            # Make HTTP request to the API endpoint
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=300  # 5 minute timeout for PDF generation
            )
            
            if response.status_code == 200:
                api_result = response.json()
                if api_result.get('success'):
                    logger.info(f"Product report generated successfully", extra={
                        'job_id': job_id,
                        'pdf_filename': api_result.get('filename')
                    })
                    
                    # Extract PDF details from API response
                    pdf_filename = api_result.get('filename')
                    google_drive_info = api_result.get('google_drive', {})
                    
                    if not pdf_filename:
                        error_msg = "PDF filename missing from API response"
                        logger.error(error_msg, extra={'job_id': job_id, 'api_result': api_result})
                        
                        pdf_job_service.mark_job_failed(job_id, error_msg, {
                            'api_result': api_result
                        })
                        
                        return {
                            'success': False,
                            'error': error_msg,
                            'job_id': job_id
                        }
                    
                    # Set pdf_result for the next step
                    pdf_result = {
                        'success': True,
                        'filename': pdf_filename,
                        'google_drive': google_drive_info
                    }
                    
                else:
                    error_msg = api_result.get('error', 'API returned failure')
                    logger.error(f"API returned failure", extra={
                        'job_id': job_id,
                        'error': error_msg,
                        'error_type': api_result.get('error_type')
                    })
                    
                    pdf_job_service.mark_job_failed(job_id, error_msg, {
                        'api_result': api_result
                    })
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'job_id': job_id
                    }
            else:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(f"API request failed", extra={
                    'job_id': job_id,
                    'status_code': response.status_code,
                    'response_text': response.text[:500]  # Limit response text length
                })
                
                pdf_job_service.mark_job_failed(job_id, error_msg, {
                    'status_code': response.status_code,
                    'response_text': response.text[:500]
                })
                
                return {
                    'success': False,
                    'error': error_msg,
                    'job_id': job_id
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to call product report API: {str(e)}"
            logger.error(f"API request exception", extra={
                'job_id': job_id,
                'error': str(e)
            })
            
            pdf_job_service.mark_job_failed(job_id, error_msg, {
                'exception': str(e)
            })
            
            return {
                'success': False,
                'error': error_msg,
                'job_id': job_id
            }
        
        # Step 4: Upload to Google Drive
        logger.info(f"Uploading to Google Drive", extra={'job_id': job_id})
        
        # Extract PDF details from result
        pdf_filename = pdf_result.get('filename')
        
        if not pdf_filename:
            error_msg = "PDF filename missing from generation result"
            logger.error(error_msg, extra={'job_id': job_id, 'pdf_result': pdf_result})
            
            pdf_job_service.mark_job_failed(job_id, error_msg, {
                'pdf_result': pdf_result
            })
            
            return {
                'success': False,
                'error': error_msg,
                'job_id': job_id
            }
        
        # Get Google Drive info from pdf_result (already uploaded in ProductReportService)
        google_drive_info = pdf_result.get('google_drive', {})
        
        if not google_drive_info or not google_drive_info.get('success'):
            error_msg = google_drive_info.get('error', 'Google Drive upload failed') if google_drive_info else 'Google Drive upload failed'
            logger.error(f"Google Drive upload failed", extra={
                'job_id': job_id,
                'error': error_msg
            })
            
            pdf_job_service.mark_job_failed(job_id, error_msg, {
                'pdf_result': pdf_result,
                'google_drive_info': google_drive_info
            })
            
            return {
                'success': False,
                'error': error_msg,
                'job_id': job_id
            }
        
        # Step 5: Mark job as completed
        google_drive_file_id = google_drive_info.get('file_id')
        google_drive_webview_link = google_drive_info.get('webview_link')
        
        logger.info(f"Marking job as completed", extra={
            'job_id': job_id,
            'google_drive_file_id': google_drive_file_id,
            'google_drive_webview_link': google_drive_webview_link
        })
        
        pdf_job_service.mark_job_completed(
            job_id=job_id,
            pdf_filename=pdf_filename,
            pdf_file_size=0,  # File size not available since file is cleaned up after upload
            google_drive_file_id=google_drive_file_id
        )
        
        # Step 6: Send webhook callback if provided
        if callback_url:
            try:
                send_webhook_callback(
                    callback_url=callback_url,
                    job_id=job_id,
                    status='completed',
                    result={
                        'google_drive_file_id': google_drive_file_id,
                        'pdf_filename': pdf_filename,
                        'pdf_file_size': 0  # File size not available since file is cleaned up after upload
                    }
                )
            except Exception as webhook_error:
                logger.warning(f"Webhook callback failed", extra={
                    'job_id': job_id,
                    'callback_url': callback_url,
                    'error': str(webhook_error)
                })
        
        logger.info(f"PDF generation completed successfully", extra={
            'job_id': job_id,
            'google_drive_link': google_drive_webview_link
        })
        
        return {
            'success': True,
            'job_id': job_id,
            'google_drive_link': google_drive_webview_link,
            'pdf_filename': pdf_filename,
            'pdf_file_size': 0,  # File size not available since file is cleaned up after upload
            'google_drive_file_id': google_drive_file_id
        }
        
    except Exception as e:
        error_msg = f"Unexpected error in PDF generation worker: {str(e)}"
        error_details = {
            'traceback': traceback.format_exc(),
            'error_type': type(e).__name__
        }
        
        logger.error(error_msg, extra={
            'job_id': job_id,
            'error_details': error_details
        })
        
        # Mark job as failed
        if pdf_job_service:
            pdf_job_service.mark_job_failed(job_id, error_msg, error_details)
        
        # Send failure webhook if callback URL provided
        if callback_url:
            try:
                send_webhook_callback(
                    callback_url=callback_url,
                    job_id=job_id,
                    status='failed',
                    error=error_msg
                )
            except Exception as webhook_error:
                logger.warning(f"Failure webhook callback failed", extra={
                    'job_id': job_id,
                    'callback_url': callback_url,
                    'error': str(webhook_error)
                })
        
        return {
            'success': False,
            'error': error_msg,
            'job_id': job_id,
            'error_details': error_details
        }


def generate_pdf_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy wrapper for backward compatibility"""
    return generate_pdf_worker(
        code=job_data.get('code'),
        product_id=job_data.get('product_id'),
        user_email=job_data.get('user_email'),
        user_name=job_data.get('user_name'),
        callback_url=job_data.get('callback_url'),
        **job_data
    )


def send_webhook_callback(callback_url: str, 
                         job_id: str, 
                         status: str, 
                         result: Optional[Dict[str, Any]] = None,
                         error: Optional[str] = None):
    """Send webhook callback to notify about job completion"""
    
    import requests
    import json
    
    payload = {
        'job_id': job_id,
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if result:
        payload['result'] = result
    
    if error:
        payload['error'] = error
    
    try:
        response = requests.post(
            callback_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        response.raise_for_status()
        
        logger.info(f"Webhook callback sent successfully", extra={
            'job_id': job_id,
            'callback_url': callback_url,
            'status_code': response.status_code
        })
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook callback failed", extra={
            'job_id': job_id,
            'callback_url': callback_url,
            'error': str(e)
        })
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending webhook", extra={
            'job_id': job_id,
            'callback_url': callback_url,
            'error': str(e)
        })
        raise


def cleanup_worker():
    """Worker function to clean up old jobs"""
    
    logger.info("Starting job cleanup worker")
    
    try:
        pdf_job_service = get_pdf_job_service()
        if not pdf_job_service:
            logger.error("PDF job service not initialized")
            return {'success': False, 'error': 'Service not initialized'}
        
        # Clean up jobs older than 30 days
        deleted_count = pdf_job_service.cleanup_old_jobs(days_old=30)
        
        logger.info(f"Job cleanup completed", extra={'deleted_count': deleted_count})
        
        return {
            'success': True,
            'deleted_count': deleted_count
        }
        
    except Exception as e:
        error_msg = f"Error in cleanup worker: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'error': error_msg
        }

def test_worker_function(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple test function for worker verification
    
    Args:
        data: Test data
        
    Returns:
        Dict containing test result
    """
    current_job = get_current_job()
    job_id = current_job.id if current_job else 'test'
    
    logger.info(f"Running test worker function for job {job_id}")
    
    return {
        'job_id': job_id,
        'status': 'completed',
        'message': 'Test worker function executed successfully',
        'input_data': data,
        'timestamp': datetime.utcnow().isoformat()
    }