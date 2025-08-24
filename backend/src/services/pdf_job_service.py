"""PDF Job Service for managing PDF generation jobs and results"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ..models.pdf_job_model import PDFJobResult, JobStatus, PDFJobResultService
from .database_service import DatabaseService
from ..utils.logging_utils import LoggingUtils

logger = LoggingUtils.get_logger(__name__)


class PDFJobService:
    """Service for managing PDF generation jobs and results"""
    
    def __init__(self, database_service: DatabaseService):
        self.db_service = database_service
        self.job_result_service = PDFJobResultService(database_service)
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure required indexes exist on pdf_job_results collection"""
        try:
            collection = self.job_result_service.get_collection()
            
            # Create indexes for optimal query performance
            indexes = [
                # Unique index on job_id
                {"keys": [("job_id", 1)], "options": {"unique": True}},
                
                # Compound index for code and product_id queries
                {"keys": [("code", 1), ("product_id", 1)]},
                
                # Status index for job status queries
                {"keys": [("status", 1)]},
                
                # Created_at index for time-based queries
                {"keys": [("created_at", 1)]},
                
                # User email index for user-specific queries
                {"keys": [("user_email", 1)]},
                
                # Compound index for status and created_at
                {"keys": [("status", 1), ("created_at", 1)]},
                
                # Compound index for code, product_id, and status
                {"keys": [("code", 1), ("product_id", 1), ("status", 1)]},
                
                # TTL index for automatic cleanup of old completed jobs (30 days)
                {"keys": [("completed_at", 1)], "options": {"expireAfterSeconds": 30 * 24 * 60 * 60, "partialFilterExpression": {"status": {"$in": ["completed", "failed"]}}}}
            ]
            
            for index_spec in indexes:
                try:
                    collection.create_index(
                        index_spec["keys"], 
                        **index_spec.get("options", {})
                    )
                except Exception as e:
                    # Index might already exist, log but don't fail
                    logger.debug(f"Index creation skipped (might already exist): {e}")
            
            logger.info("PDF job results collection indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
    
    def create_job(self, 
                   job_id: str,
                   code: str,
                   product_id: str,
                   user_email: Optional[str] = None,
                   user_name: Optional[str] = None,
                   callback_url: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new PDF job result record"""
        
        logger.info(f"Creating PDF job record", extra={
            'job_id': job_id,
            'code': code,
            'product_id': product_id,
            'user_email': user_email
        })
        
        try:
            job_result = PDFJobResult(
                job_id=job_id,
                code=code,
                product_id=product_id,
                user_email=user_email,
                user_name=user_name,
                callback_url=callback_url,
                metadata=metadata or {}
            )
            
            record_id = self.job_result_service.create_job_result(job_result)
            
            logger.info(f"PDF job record created successfully", extra={
                'job_id': job_id,
                'record_id': record_id
            })
            
            return record_id
            
        except Exception as e:
            logger.error(f"Error creating PDF job record: {e}", extra={
                'job_id': job_id,
                'code': code,
                'product_id': product_id
            })
            raise
    
    def get_job_by_id(self, job_id: str) -> Optional[PDFJobResult]:
        """Get job result by job ID"""
        try:
            return self.job_result_service.get_job_result_by_job_id(job_id)
        except Exception as e:
            logger.error(f"Error getting job by ID: {e}", extra={'job_id': job_id})
            return None
    
    def get_job_by_code_and_product(self, code: str, product_id: str) -> Optional[PDFJobResult]:
        """Get latest job result by code and product ID"""
        try:
            return self.job_result_service.get_job_result_by_code_and_product(code, product_id)
        except Exception as e:
            logger.error(f"Error getting job by code and product: {e}", extra={
                'code': code,
                'product_id': product_id
            })
            return None
    
    def mark_job_started(self, job_id: str) -> bool:
        """Mark job as started"""
        logger.info(f"Marking job as started", extra={'job_id': job_id})
        
        try:
            success = self.job_result_service.mark_job_as_started(job_id)
            
            if success:
                logger.info(f"Job marked as started successfully", extra={'job_id': job_id})
            else:
                logger.warning(f"Failed to mark job as started", extra={'job_id': job_id})
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking job as started: {e}", extra={'job_id': job_id})
            return False
    
    def mark_job_completed(self, 
                          job_id: str,
                          pdf_filename: str,
                          pdf_file_size: int,
                          google_drive_file_id: str) -> bool:
        """Mark job as completed with results"""
        
        logger.info(f"Marking job as completed", extra={
            'job_id': job_id,
            'pdf_filename': pdf_filename,
            'pdf_file_size': pdf_file_size,
            'google_drive_file_id': google_drive_file_id
        })
        
        try:
            success = self.job_result_service.mark_job_as_completed(
                job_id=job_id,
                pdf_filename=pdf_filename,
                pdf_file_size=pdf_file_size,
                google_drive_file_id=google_drive_file_id
            )
            
            if success:
                logger.info(f"Job marked as completed successfully", extra={'job_id': job_id})
                
                # Also update the workflow.psikotes_v2 collection for permanent storage
                self._update_workflow_collection(job_id, google_drive_file_id)
            else:
                logger.warning(f"Failed to mark job as completed", extra={'job_id': job_id})
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking job as completed: {e}", extra={'job_id': job_id})
            return False
    
    def mark_job_failed(self, 
                       job_id: str, 
                       error_message: str, 
                       error_details: Optional[Dict[str, Any]] = None) -> bool:
        """Mark job as failed with error information"""
        
        logger.error(f"Marking job as failed", extra={
            'job_id': job_id,
            'error_message': error_message,
            'error_details': error_details
        })
        
        try:
            success = self.job_result_service.mark_job_as_failed(
                job_id=job_id,
                error_message=error_message,
                error_details=error_details
            )
            
            if success:
                logger.info(f"Job marked as failed successfully", extra={'job_id': job_id})
                
                # Also update the workflow.psikotes_v2 collection for permanent storage
                self._update_workflow_collection_failed(job_id, error_message)
            else:
                logger.warning(f"Failed to mark job as failed", extra={'job_id': job_id})
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking job as failed: {e}", extra={'job_id': job_id})
            return False
    
    def _update_workflow_collection(self, job_id: str, google_drive_file_id: str):
        """Update workflow.psikotes_v2 collection with PDF generation results"""
        try:
            # Get job details
            job_result = self.get_job_by_id(job_id)
            if not job_result:
                logger.warning(f"Job result not found for workflow update", extra={'job_id': job_id})
                return
            
            # Get workflow database (assuming it's configured)
            # This would need to be configured based on your database setup
            workflow_db = self.db_service.client.get_database('workflow')  # Adjust database name as needed
            workflow_collection = workflow_db.get_collection('psikotes_v2')
            
            # Update the workflow collection
            update_result = workflow_collection.update_one(
                {"code": job_result.code},
                {"$set": {
                    f"pdf_generation.product_configs.{job_result.product_id}": {
                        "status": "completed",
                        "job_id": job_id,
                        "google_drive_file_id": google_drive_file_id,
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    "pdf_generation.status": "completed",
                    "pdf_generation.job_id": job_id,
                    "pdf_generation.google_drive_file_id": google_drive_file_id,
                    "pdf_generation.completed_at": datetime.utcnow().isoformat()
                }}
            )
            
            if update_result.modified_count > 0:
                logger.info(f"Workflow collection updated successfully", extra={
                    'job_id': job_id,
                    'code': job_result.code
                })
            else:
                logger.warning(f"No workflow document updated", extra={
                    'job_id': job_id,
                    'code': job_result.code
                })
                
        except Exception as e:
            logger.error(f"Error updating workflow collection: {e}", extra={'job_id': job_id})
    
    def _update_workflow_collection_failed(self, job_id: str, error_message: str):
        """Update workflow.psikotes_v2 collection with PDF generation failure"""
        try:
            # Get job details
            job_result = self.get_job_by_id(job_id)
            if not job_result:
                logger.warning(f"Job result not found for workflow update", extra={'job_id': job_id})
                return
            
            # Get workflow database
            workflow_db = self.db_service.client.get_database('workflow')
            workflow_collection = workflow_db.get_collection('psikotes_v2')
            
            # Update the workflow collection
            update_result = workflow_collection.update_one(
                {"code": job_result.code},
                {"$set": {
                    f"pdf_generation.product_configs.{job_result.product_id}": {
                        "status": "failed",
                        "job_id": job_id,
                        "error_message": error_message,
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    "pdf_generation.status": "failed",
                    "pdf_generation.job_id": job_id,
                    "pdf_generation.error_message": error_message,
                    "pdf_generation.completed_at": datetime.utcnow().isoformat()
                }}
            )
            
            if update_result.modified_count > 0:
                logger.info(f"Workflow collection updated with failure", extra={
                    'job_id': job_id,
                    'code': job_result.code
                })
            else:
                logger.warning(f"No workflow document updated for failure", extra={
                    'job_id': job_id,
                    'code': job_result.code
                })
                
        except Exception as e:
            logger.error(f"Error updating workflow collection with failure: {e}", extra={'job_id': job_id})
    
    def get_pending_jobs(self, limit: int = 100) -> List[PDFJobResult]:
        """Get pending jobs"""
        try:
            return self.job_result_service.get_jobs_by_status(JobStatus.PENDING, limit)
        except Exception as e:
            logger.error(f"Error getting pending jobs: {e}")
            return []
    
    def get_in_progress_jobs(self, limit: int = 100) -> List[PDFJobResult]:
        """Get in-progress jobs"""
        try:
            return self.job_result_service.get_jobs_by_status(JobStatus.IN_PROGRESS, limit)
        except Exception as e:
            logger.error(f"Error getting in-progress jobs: {e}")
            return []
    
    def get_failed_jobs(self, limit: int = 100) -> List[PDFJobResult]:
        """Get failed jobs"""
        try:
            return self.job_result_service.get_jobs_by_status(JobStatus.FAILED, limit)
        except Exception as e:
            logger.error(f"Error getting failed jobs: {e}")
            return []
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed/failed jobs"""
        logger.info(f"Starting cleanup of jobs older than {days_old} days")
        
        try:
            deleted_count = self.job_result_service.cleanup_old_jobs(days_old)
            
            logger.info(f"Cleanup completed", extra={
                'deleted_count': deleted_count,
                'days_old': days_old
            })
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during job cleanup: {e}")
            return 0
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            collection = self.job_result_service.get_collection()
            
            # Get counts by status
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = {}
            for result in collection.aggregate(pipeline):
                status_counts[result["_id"]] = result["count"]
            
            # Get total count
            total_count = collection.count_documents({})
            
            # Get average processing time for completed jobs
            avg_pipeline = [
                {"$match": {"status": "completed", "processing_duration": {"$exists": True}}},
                {"$group": {
                    "_id": None,
                    "avg_duration": {"$avg": "$processing_duration"}
                }}
            ]
            
            avg_duration = 0
            avg_result = list(collection.aggregate(avg_pipeline))
            if avg_result:
                avg_duration = avg_result[0]["avg_duration"]
            
            return {
                "total_jobs": total_count,
                "status_counts": status_counts,
                "average_processing_duration": avg_duration
            }
            
        except Exception as e:
            logger.error(f"Error getting job statistics: {e}")
            return {
                "total_jobs": 0,
                "status_counts": {},
                "average_processing_duration": 0
            }