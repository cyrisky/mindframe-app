"""PDF document model for database storage"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PDFDocument(BaseModel):
    """Model for PDF documents stored in the database"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Path to the stored PDF file")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(default="application/pdf")
    
    # Generation metadata
    template_name: Optional[str] = Field(default=None, description="Template used for generation")
    generation_method: str = Field(..., description="Method used: html, template, or url")
    source_content: Optional[str] = Field(default=None, description="Source HTML or URL")
    
    # User and session info
    user_id: Optional[str] = Field(default=None, description="User who generated the PDF")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None, description="When the PDF expires")
    
    # Status and metadata
    status: str = Field(default="completed", description="Status: pending, completed, failed")
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Download tracking
    download_count: int = Field(default=0, description="Number of times downloaded")
    last_downloaded: Optional[datetime] = Field(default=None, description="Last download timestamp")
    
    # Tags and categorization
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(default=None, description="Document category")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = self.dict(by_alias=True, exclude_none=True)
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PDFDocument":
        """Create instance from MongoDB document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
    
    def update_download_stats(self):
        """Update download statistics"""
        self.download_count += 1
        self.last_downloaded = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, error_message: str):
        """Mark document generation as failed"""
        self.status = "failed"
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self, file_path: str, file_size: int):
        """Mark document generation as completed"""
        self.status = "completed"
        self.file_path = file_path
        self.file_size = file_size
        self.updated_at = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if the document has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def add_tag(self, tag: str):
        """Add a tag to the document"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the document"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()