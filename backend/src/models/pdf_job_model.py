"""PDF Job Result model for MongoDB operations"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PDFJobResult(BaseModel):
    """PDF Job Result model for MongoDB storage"""
    
    # MongoDB ObjectId (optional for new documents)
    id: Optional[str] = Field(default=None, alias="_id")
    
    # Job identification
    job_id: str = Field(..., description="Unique job identifier from RQ")
    code: str = Field(..., description="Test code from workflow.psikotes_v2")
    product_id: str = Field(..., description="Product configuration ID")
    
    # Job status and timing
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion timestamp")
    
    # User information
    user_email: Optional[str] = Field(default=None, description="User email for Google Drive sharing")
    user_name: Optional[str] = Field(default=None, description="User name for PDF personalization")
    
    # PDF generation details
    pdf_filename: Optional[str] = Field(default=None, description="Generated PDF filename")
    pdf_file_size: Optional[int] = Field(default=None, description="PDF file size in bytes")
    
    # Google Drive integration
    google_drive_file_id: Optional[str] = Field(default=None, description="Google Drive file ID")
    google_drive_folder_id: Optional[str] = Field(default=None, description="Google Drive folder ID")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if job failed")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    # Processing metadata
    processing_duration: Optional[float] = Field(default=None, description="Processing duration in seconds")
    template_used: Optional[str] = Field(default=None, description="Template used for PDF generation")
    
    # Webhook callback
    callback_url: Optional[str] = Field(default=None, description="n8n webhook callback URL")
    callback_sent: bool = Field(default=False, description="Whether callback was sent successfully")
    callback_sent_at: Optional[datetime] = Field(default=None, description="Callback sent timestamp")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional job metadata")
    
    class Config:
        """Pydantic configuration"""
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    
    def mark_as_started(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
    
    def mark_as_completed(self, 
                         pdf_filename: str,
                         pdf_file_size: int,
                         google_drive_file_id: str) -> None:
        """Mark job as completed with results"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.pdf_filename = pdf_filename
        self.pdf_file_size = pdf_file_size
        self.google_drive_file_id = google_drive_file_id
        
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
    
    def mark_as_failed(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark job as failed with error information"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details or {}
        
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
    
    def mark_callback_sent(self) -> None:
        """Mark callback as sent"""
        self.callback_sent = True
        self.callback_sent_at = datetime.utcnow()
    
    def increment_retry_count(self) -> None:
        """Increment retry count"""
        self.retry_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = self.dict(by_alias=True, exclude_none=True)
        
        # Convert datetime objects to ISO format
        for field in ['created_at', 'started_at', 'completed_at', 'callback_sent_at']:
            if field in data and data[field]:
                data[field] = data[field].isoformat() if isinstance(data[field], datetime) else data[field]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFJobResult':
        """Create instance from dictionary"""
        # Convert ISO datetime strings back to datetime objects
        for field in ['created_at', 'started_at', 'completed_at', 'callback_sent_at']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
        
        return cls(**data)


class PDFJobResultService:
    """Service for managing PDF job results in MongoDB"""
    
    def __init__(self, database_service):
        self.db_service = database_service
        self.collection_name = "pdf_job_results"
    
    def get_collection(self):
        """Get the pdf_job_results collection"""
        return self.db_service.get_collection(self.collection_name)
    
    def create_job_result(self, job_result: PDFJobResult) -> str:
        """Create a new job result record"""
        collection = self.get_collection()
        result = collection.insert_one(job_result.to_dict())
        return str(result.inserted_id)
    
    def get_job_result_by_job_id(self, job_id: str) -> Optional[PDFJobResult]:
        """Get job result by job ID"""
        collection = self.get_collection()
        data = collection.find_one({"job_id": job_id})
        
        if data:
            data["_id"] = str(data["_id"])
            return PDFJobResult.from_dict(data)
        return None
    
    def get_job_result_by_code_and_product(self, code: str, product_id: str) -> Optional[PDFJobResult]:
        """Get job result by code and product ID"""
        collection = self.get_collection()
        data = collection.find_one({
            "code": code,
            "product_id": product_id,
            "status": {"$in": [JobStatus.COMPLETED.value, JobStatus.IN_PROGRESS.value, JobStatus.PENDING.value]}
        }, sort=[("created_at", -1)])
        
        if data:
            data["_id"] = str(data["_id"])
            return PDFJobResult.from_dict(data)
        return None
    
    def update_job_result(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job result"""
        collection = self.get_collection()
        result = collection.update_one(
            {"job_id": job_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    def mark_job_as_started(self, job_id: str) -> bool:
        """Mark job as started"""
        return self.update_job_result(job_id, {
            "status": JobStatus.IN_PROGRESS.value,
            "started_at": datetime.utcnow().isoformat()
        })
    
    def mark_job_as_completed(self, job_id: str, 
                             pdf_filename: str,
                             pdf_file_size: int,
                             google_drive_file_id: str) -> bool:
        """Mark job as completed"""
        completed_at = datetime.utcnow()
        return self.update_job_result(job_id, {
            "status": JobStatus.COMPLETED.value,
            "completed_at": completed_at.isoformat(),
            "pdf_filename": pdf_filename,
            "pdf_file_size": pdf_file_size,
            "google_drive_file_id": google_drive_file_id
        })
    
    def mark_job_as_failed(self, job_id: str, error_message: str, 
                          error_details: Optional[Dict[str, Any]] = None) -> bool:
        """Mark job as failed"""
        return self.update_job_result(job_id, {
            "status": JobStatus.FAILED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": error_message,
            "error_details": error_details or {}
        })
    
    def get_jobs_by_status(self, status: JobStatus, limit: int = 100) -> List[PDFJobResult]:
        """Get jobs by status"""
        collection = self.get_collection()
        cursor = collection.find({"status": status.value}).limit(limit)
        
        results = []
        for data in cursor:
            data["_id"] = str(data["_id"])
            results.append(PDFJobResult.from_dict(data))
        
        return results
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed/failed jobs"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        collection = self.get_collection()
        
        result = collection.delete_many({
            "status": {"$in": [JobStatus.COMPLETED.value, JobStatus.FAILED.value]},
            "created_at": {"$lt": cutoff_date.isoformat()}
        })
        
        return result.deleted_count