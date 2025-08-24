"""PDF service for managing PDF generation operations"""

import os
import logging
import tempfile
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from ..core.pdf_generator import PDFGenerator, PDFGenerationError
from ..core.template_processor import TemplateProcessor
from ..core.layout_engine import LayoutEngine, LayoutConfig
from ..models.pdf_model import PDFDocument
from ..models.template_model import Template
from ..models.report_model import PsychologicalReport

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF generation and management"""
    
    def __init__(self):
        self.pdf_generator = None
        self.template_processor = None
        self.layout_engine = None
        self.db_service = None
        self.storage_service = None
        self.email_service = None
        self.google_drive_service = None
        self.executor = None
        self._initialized = False
    
    def initialize(self, db_service=None, storage_service=None, 
                   email_service=None, google_drive_service=None, max_workers: int = 4) -> bool:
        """Initialize PDF service"""
        try:
            # Initialize core components
            self.pdf_generator = PDFGenerator()
            self.template_processor = TemplateProcessor()
            self.layout_engine = LayoutEngine()
            
            # Store service references
            self.db_service = db_service
            # storage_service is deprecated - keeping for backward compatibility but not used
            self.storage_service = storage_service
            self.email_service = email_service
            self.google_drive_service = google_drive_service
            
            # Initialize thread pool for async operations
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            
            # Core components are initialized in their constructors
            # No additional initialization needed
            
            self._initialized = True
            logger.info("PDF service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PDF service: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform PDF service health check"""
        try:
            health_info = {
                "status": "healthy",
                "pdf_generator": False,
                "template_processor": False,
                "layout_engine": False,
                "database_available": False,
                "storage_available": False,
                "email_available": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check core components
            if self.pdf_generator:
                try:
                    # Test PDF generation with simple HTML
                    test_html = "<html><body><h1>Health Check</h1></body></html>"
                    test_pdf = self.pdf_generator.generate_from_html(test_html)
                    health_info["pdf_generator"] = len(test_pdf) > 0
                except Exception as e:
                    health_info["pdf_generator_error"] = str(e)
            
            if self.template_processor:
                try:
                    # Test template rendering
                    test_template = "Hello {{ name }}!"
                    result = self.template_processor.render_string(test_template, {"name": "World"})
                    health_info["template_processor"] = result == "Hello World!"
                except Exception as e:
                    health_info["template_processor_error"] = str(e)
            
            if self.layout_engine:
                try:
                    # Test layout generation
                    config = LayoutConfig()
                    css = self.layout_engine.generate_layout_css(config)
                    health_info["layout_engine"] = len(css) > 0
                except Exception as e:
                    health_info["layout_engine_error"] = str(e)
            
            # Check service dependencies
            if self.db_service:
                try:
                    db_health = self.db_service.health_check()
                    health_info["database_available"] = db_health.get("status") == "healthy"
                except Exception as e:
                    health_info["database_error"] = str(e)
            
            if self.storage_service:
                try:
                    storage_health = self.storage_service.health_check()
                    health_info["storage_available"] = storage_health.get("status") == "healthy"
                except Exception as e:
                    health_info["storage_error"] = str(e)
            
            if self.email_service:
                try:
                    email_health = self.email_service.health_check()
                    health_info["email_available"] = email_health.get("status") == "healthy"
                except Exception as e:
                    health_info["email_error"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"PDF service health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def generate_pdf_from_html(self, html_content: str, 
                              options: Dict[str, Any] = None,
                              user_id: str = None,
                              filename: str = None) -> Dict[str, Any]:
        """Generate PDF from HTML content and upload to Google Drive"""
        try:
            # Generate unique filename if not provided
            if not filename:
                filename = f"document_{uuid.uuid4().hex[:8]}.pdf"
            
            # Generate PDF
            pdf_content = self.pdf_generator.generate_from_html(html_content, options)
            
            # Create temporary file for Google Drive upload
            google_drive_result = None
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload to Google Drive
                google_drive_result = self.upload_to_google_drive(
                    file_path=temp_file_path,
                    file_name=filename
                )
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            # Create PDF document record with Google Drive info
            pdf_doc = PDFDocument(
                filename=filename,
                file_size=len(pdf_content),
                file_path=google_drive_result.get('web_view_link') if google_drive_result and google_drive_result.get('success') else None,
                content_type="application/pdf",
                user_id=user_id,
                generation_method="html",
                generation_options=options or {},
                status="completed"
            )
            
            # Save to database
            if self.db_service:
                try:
                    result = self.db_service.create_document(
                        "pdf_documents", pdf_doc.to_dict()
                    )
                    pdf_doc.id = str(result.inserted_id)
                except Exception as e:
                    logger.warning(f"Failed to save PDF document to database: {e}")
            
            logger.info(f"Generated PDF: {filename} ({len(pdf_content)} bytes)")
            
            return {
                "success": True,
                "pdf_document": pdf_doc.to_dict(),
                "google_drive_result": google_drive_result,
                "size": len(pdf_content)
            }
            
        except PDFGenerationError as e:
            logger.error(f"PDF generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "pdf_generation"
            }
        except Exception as e:
            logger.error(f"Unexpected error generating PDF: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected"
            }
    
    def generate_pdf_from_template(self, template_name: str, 
                                  variables: Dict[str, Any],
                                  options: Dict[str, Any] = None,
                                  user_id: str = None,
                                  filename: str = None) -> Dict[str, Any]:
        """Generate PDF from template"""
        try:
            # Render template
            html_content = self.template_processor.render_template(
                template_name, variables
            )
            
            # Generate filename if not provided
            if not filename:
                filename = f"{template_name}_{uuid.uuid4().hex[:8]}.pdf"
            
            # Generate PDF
            result = self.generate_pdf_from_html(
                html_content, options, user_id, filename
            )
            
            if result["success"]:
                # Update generation method
                result["pdf_document"]["generation_method"] = "template"
                result["pdf_document"]["template_name"] = template_name
                result["pdf_document"]["template_variables"] = variables
                
                # Update database record if available
                if self.db_service and result["pdf_document"].get("id"):
                    try:
                        self.db_service.update_document(
                            "pdf_documents",
                            {"_id": result["pdf_document"]["id"]},
                            {
                                "$set": {
                                    "generation_method": "template",
                                    "template_name": template_name,
                                    "template_variables": variables
                                }
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update PDF document in database: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating PDF from template: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "template_processing"
            }
    
    def generate_psychological_report(self, report_data: Dict[str, Any],
                                    template_name: str = "psychological_report",
                                    user_id: str = None,
                                    send_email: bool = False) -> Dict[str, Any]:
        """Generate psychological report PDF"""
        try:
            # Create psychological report object
            report = PsychologicalReport(**report_data)
            
            # Prepare template variables
            template_vars = {
                "report": report.to_dict(),
                "client": report.client_information.to_dict() if report.client_information else {},
                "professional": report.professional_information,
                "test_results": [result.to_dict() for result in report.test_results],
                "generated_date": datetime.now().strftime("%B %d, %Y"),
                "generated_time": datetime.now().strftime("%I:%M %p")
            }
            
            # Generate filename
            client_name = report.client_information.full_name if report.client_information else "Unknown"
            safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"psychological_report_{safe_client_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            # Generate PDF
            result = self.generate_pdf_from_template(
                template_name, template_vars, user_id=user_id, filename=filename
            )
            
            if result["success"]:
                # Update generation method
                result["pdf_document"]["generation_method"] = "psychological_report"
                result["pdf_document"]["report_id"] = report.id
                result["pdf_document"]["client_name"] = client_name
                
                # Save report to database
                if self.db_service:
                    try:
                        report.pdf_generation_status = "completed"
                        report.pdf_file_path = result["pdf_document"].get("file_path")
                        report.pdf_generated_at = datetime.utcnow()
                        
                        self.db_service.create_document(
                            "psychological_reports", report.to_dict()
                        )
                    except Exception as e:
                        logger.warning(f"Failed to save psychological report to database: {e}")
                
                # Send email notification if requested
                if send_email and self.email_service and user_id:
                    try:
                        # Get user info (this would need to be implemented)
                        # user_info = self.get_user_info(user_id)
                        # if user_info:
                        #     self.email_service.send_report_notification(
                        #         user_info['email'], user_info['name'],
                        #         client_name, report.id,
                        #         f"/download/{result['pdf_document']['id']}"
                        #     )
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to send email notification: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating psychological report: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "report_generation"
            }
    
    def generate_pdf_async(self, generation_func, *args, **kwargs) -> str:
        """Generate PDF asynchronously and return task ID"""
        task_id = str(uuid.uuid4())
        
        def async_generation():
            try:
                result = generation_func(*args, **kwargs)
                # Store result in cache/database with task_id
                if self.db_service:
                    self.db_service.create_document(
                        "async_tasks",
                        {
                            "task_id": task_id,
                            "status": "completed" if result["success"] else "failed",
                            "result": result,
                            "created_at": datetime.utcnow(),
                            "completed_at": datetime.utcnow()
                        }
                    )
            except Exception as e:
                logger.error(f"Async PDF generation failed: {e}")
                if self.db_service:
                    self.db_service.create_document(
                        "async_tasks",
                        {
                            "task_id": task_id,
                            "status": "failed",
                            "error": str(e),
                            "created_at": datetime.utcnow(),
                            "completed_at": datetime.utcnow()
                        }
                    )
        
        # Submit task to thread pool
        self.executor.submit(async_generation)
        
        # Store initial task status
        if self.db_service:
            try:
                self.db_service.create_document(
                    "async_tasks",
                    {
                        "task_id": task_id,
                        "status": "pending",
                        "created_at": datetime.utcnow()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to store async task status: {e}")
        
        return task_id
    
    def get_async_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of async PDF generation task"""
        if not self.db_service:
            return {"error": "Database service not available"}
        
        try:
            task = self.db_service.find_one(
                "async_tasks", {"task_id": task_id}
            )
            
            if not task:
                return {"error": "Task not found"}
            
            return {
                "task_id": task_id,
                "status": task.get("status"),
                "result": task.get("result"),
                "error": task.get("error"),
                "created_at": task.get("created_at"),
                "completed_at": task.get("completed_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting async task status: {e}")
            return {"error": str(e)}
    
    def get_pdf_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get PDF document by ID"""
        if not self.db_service:
            return None
        
        try:
            doc = self.db_service.find_one(
                "pdf_documents", {"_id": document_id}
            )
            return doc
        except Exception as e:
            logger.error(f"Error getting PDF document: {e}")
            return None
    
    def list_pdf_documents(self, user_id: str = None, 
                          limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """List PDF documents"""
        if not self.db_service:
            return []
        
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            
            docs = self.db_service.find(
                "pdf_documents", query, limit=limit, skip=skip,
                sort=[("created_at", -1)]
            )
            return list(docs)
        except Exception as e:
            logger.error(f"Error listing PDF documents: {e}")
            return []
    
    def delete_pdf_document(self, document_id: str, user_id: str = None) -> bool:
        """Delete PDF document"""
        try:
            # Get document info
            doc = self.get_pdf_document(document_id)
            if not doc:
                return False
            
            # Check user permission
            if user_id and doc.get("user_id") != user_id:
                logger.warning(f"User {user_id} attempted to delete document {document_id} owned by {doc.get('user_id')}")
                return False
            
            # Delete file from storage
            if self.storage_service and doc.get("file_path"):
                self.storage_service.delete_file(doc["file_path"])
            
            # Delete from database
            if self.db_service:
                result = self.db_service.delete_document(
                    "pdf_documents", {"_id": document_id}
                )
                return result.deleted_count > 0
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting PDF document: {e}")
            return False
    
    def get_pdf_content(self, document_id: str, user_id: str = None) -> Optional[bytes]:
        """Get PDF file content"""
        try:
            # Get document info
            doc = self.get_pdf_document(document_id)
            if not doc:
                return None
            
            # Check user permission
            if user_id and doc.get("user_id") != user_id:
                logger.warning(f"User {user_id} attempted to access document {document_id} owned by {doc.get('user_id')}")
                return None
            
            # Get file content from storage
            if self.storage_service and doc.get("file_path"):
                content = self.storage_service.get_file(doc["file_path"])
                
                # Update download statistics
                if content and self.db_service:
                    try:
                        self.db_service.update_document(
                            "pdf_documents",
                            {"_id": document_id},
                            {
                                "$inc": {"download_count": 1},
                                "$set": {"last_downloaded_at": datetime.utcnow()}
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update download statistics: {e}")
                
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting PDF content: {e}")
            return None
    
    def get_generation_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """Get PDF generation statistics"""
        if not self.db_service:
            return {}
        
        try:
            pipeline = []
            
            # Filter by user if specified
            if user_id:
                pipeline.append({"$match": {"user_id": user_id}})
            
            # Group and count
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_documents": {"$sum": 1},
                        "total_size": {"$sum": "$file_size"},
                        "total_downloads": {"$sum": "$download_count"},
                        "by_method": {
                            "$push": {
                                "method": "$generation_method",
                                "size": "$file_size"
                            }
                        },
                        "by_status": {
                            "$push": "$status"
                        }
                    }
                }
            ])
            
            result = list(self.db_service.aggregate("pdf_documents", pipeline))
            
            if result:
                stats = result[0]
                
                # Process method statistics
                method_stats = {}
                for item in stats.get("by_method", []):
                    method = item.get("method", "unknown")
                    if method not in method_stats:
                        method_stats[method] = {"count": 0, "total_size": 0}
                    method_stats[method]["count"] += 1
                    method_stats[method]["total_size"] += item.get("size", 0)
                
                # Process status statistics
                status_stats = {}
                for status in stats.get("by_status", []):
                    status_stats[status] = status_stats.get(status, 0) + 1
                
                return {
                    "total_documents": stats.get("total_documents", 0),
                    "total_size_mb": round(stats.get("total_size", 0) / 1024 / 1024, 2),
                    "total_downloads": stats.get("total_downloads", 0),
                    "by_method": method_stats,
                    "by_status": status_stats
                }
            
            return {
                "total_documents": 0,
                "total_size_mb": 0,
                "total_downloads": 0,
                "by_method": {},
                "by_status": {}
            }
            
        except Exception as e:
            logger.error(f"Error getting generation statistics: {e}")
            return {}
    
    def cleanup_old_documents(self, days_old: int = 30) -> int:
        """Clean up old PDF documents"""
        if not self.db_service:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old documents
            old_docs = self.db_service.find(
                "pdf_documents",
                {"created_at": {"$lt": cutoff_date}}
            )
            
            deleted_count = 0
            for doc in old_docs:
                if self.delete_pdf_document(str(doc["_id"])):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old PDF documents")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old documents: {e}")
            return 0
    
    def upload_to_google_drive(self, file_path: str, file_name: str = None) -> Dict[str, Any]:
        """Upload a PDF file to Google Drive
        
        Args:
            file_path (str): Local path to the PDF file
            file_name (str, optional): Name for the file in Drive
            
        Returns:
            Dict[str, Any]: Upload result containing file ID and web view link
        """
        try:
            if not self.google_drive_service:
                return {
                    'success': False,
                    'error': 'Google Drive service not initialized',
                    'message': 'Google Drive service not available'
                }
            
            # Upload to Google Drive
            result = self.google_drive_service.upload_file(
                file_path=file_path,
                file_name=file_name,
                mime_type='application/pdf'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to upload to Google Drive'
            }
    
    def shutdown(self):
        """Shutdown PDF service"""
        if self.executor:
            self.executor.shutdown(wait=True)
        logger.info("PDF service shutdown complete")


# Global PDF service instance
pdf_service = PDFService()