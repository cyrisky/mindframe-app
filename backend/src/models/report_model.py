"""Psychological report model for specialized report generation"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum


class ReportType(str, Enum):
    """Types of psychological reports"""
    ASSESSMENT = "assessment"
    THERAPY_SESSION = "therapy_session"
    PROGRESS_REPORT = "progress_report"
    DIAGNOSTIC = "diagnostic"
    TREATMENT_PLAN = "treatment_plan"
    DISCHARGE_SUMMARY = "discharge_summary"
    PSYCHOLOGICAL_EVALUATION = "psychological_evaluation"
    NEUROPSYCHOLOGICAL = "neuropsychological"
    FORENSIC = "forensic"
    EDUCATIONAL = "educational"


class ReportStatus(str, Enum):
    """Report status options"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    FINALIZED = "finalized"
    ARCHIVED = "archived"


class TestResult(BaseModel):
    """Individual test result within a report"""
    
    test_name: str = Field(..., description="Name of the psychological test")
    test_code: Optional[str] = Field(default=None, description="Test code or identifier")
    administration_date: date = Field(..., description="Date test was administered")
    
    # Raw scores and results
    raw_scores: Dict[str, Any] = Field(default_factory=dict, description="Raw test scores")
    scaled_scores: Dict[str, Any] = Field(default_factory=dict, description="Scaled/standardized scores")
    percentiles: Dict[str, Any] = Field(default_factory=dict, description="Percentile rankings")
    
    # Interpretations
    interpretation: Optional[str] = Field(default=None, description="Test interpretation")
    clinical_significance: Optional[str] = Field(default=None, description="Clinical significance")
    recommendations: List[str] = Field(default_factory=list, description="Test-specific recommendations")
    
    # Validity and reliability
    validity_indicators: Dict[str, Any] = Field(default_factory=dict, description="Test validity indicators")
    confidence_level: Optional[str] = Field(default=None, description="Confidence level of results")
    
    # Additional metadata
    administrator: Optional[str] = Field(default=None, description="Person who administered the test")
    duration_minutes: Optional[int] = Field(default=None, description="Test duration in minutes")
    notes: Optional[str] = Field(default=None, description="Additional notes about the test")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class ClientInformation(BaseModel):
    """Client information for psychological reports"""
    
    # Basic demographics
    client_id: str = Field(..., description="Unique client identifier")
    first_name: str = Field(..., description="Client first name")
    last_name: str = Field(..., description="Client last name")
    date_of_birth: date = Field(..., description="Client date of birth")
    age: Optional[int] = Field(default=None, description="Client age at time of report")
    gender: Optional[str] = Field(default=None, description="Client gender")
    
    # Contact information
    address: Optional[str] = Field(default=None, description="Client address")
    phone: Optional[str] = Field(default=None, description="Client phone number")
    email: Optional[str] = Field(default=None, description="Client email")
    emergency_contact: Optional[str] = Field(default=None, description="Emergency contact information")
    
    # Background information
    occupation: Optional[str] = Field(default=None, description="Client occupation")
    education_level: Optional[str] = Field(default=None, description="Client education level")
    marital_status: Optional[str] = Field(default=None, description="Client marital status")
    primary_language: Optional[str] = Field(default="English", description="Client primary language")
    
    # Clinical information
    referring_physician: Optional[str] = Field(default=None, description="Referring physician")
    referral_reason: Optional[str] = Field(default=None, description="Reason for referral")
    presenting_concerns: List[str] = Field(default_factory=list, description="Presenting concerns")
    medical_history: Optional[str] = Field(default=None, description="Relevant medical history")
    psychiatric_history: Optional[str] = Field(default=None, description="Psychiatric history")
    current_medications: List[str] = Field(default_factory=list, description="Current medications")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }


class PsychologicalReport(BaseModel):
    """Comprehensive psychological report model"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    
    # Report metadata
    report_number: str = Field(..., description="Unique report number")
    report_type: ReportType = Field(..., description="Type of psychological report")
    status: ReportStatus = Field(default=ReportStatus.DRAFT, description="Report status")
    
    # Client and session information
    client_info: ClientInformation = Field(..., description="Client information")
    session_date: date = Field(..., description="Date of assessment/session")
    report_date: date = Field(default_factory=date.today, description="Date report was generated")
    
    # Professional information
    psychologist_name: str = Field(..., description="Name of the psychologist")
    psychologist_license: Optional[str] = Field(default=None, description="Psychologist license number")
    psychologist_credentials: Optional[str] = Field(default=None, description="Psychologist credentials")
    supervisor_name: Optional[str] = Field(default=None, description="Supervisor name if applicable")
    
    # Report content sections
    reason_for_referral: str = Field(..., description="Reason for referral")
    background_information: Optional[str] = Field(default=None, description="Background and history")
    behavioral_observations: Optional[str] = Field(default=None, description="Behavioral observations")
    
    # Test results and assessments
    tests_administered: List[TestResult] = Field(default_factory=list, description="Test results")
    
    # Clinical findings
    clinical_impressions: Optional[str] = Field(default=None, description="Clinical impressions")
    diagnostic_impressions: List[str] = Field(default_factory=list, description="Diagnostic impressions")
    differential_diagnosis: List[str] = Field(default_factory=list, description="Differential diagnoses")
    
    # Recommendations and treatment
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    treatment_goals: List[str] = Field(default_factory=list, description="Treatment goals")
    prognosis: Optional[str] = Field(default=None, description="Prognosis")
    
    # Risk assessment
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    protective_factors: List[str] = Field(default_factory=list, description="Protective factors")
    safety_concerns: Optional[str] = Field(default=None, description="Safety concerns")
    
    # Follow-up and monitoring
    follow_up_recommendations: List[str] = Field(default_factory=list, description="Follow-up recommendations")
    next_review_date: Optional[date] = Field(default=None, description="Next review date")
    
    # Document management
    template_used: Optional[str] = Field(default=None, description="Template used for generation")
    version: str = Field(default="1.0", description="Report version")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    finalized_at: Optional[datetime] = Field(default=None, description="When report was finalized")
    
    # Access and permissions
    created_by: str = Field(..., description="User who created the report")
    authorized_viewers: List[str] = Field(default_factory=list, description="Authorized viewers")
    confidentiality_level: str = Field(default="high", description="Confidentiality level")
    
    # PDF generation
    pdf_generated: bool = Field(default=False, description="Whether PDF has been generated")
    pdf_file_path: Optional[str] = Field(default=None, description="Path to generated PDF")
    pdf_generation_date: Optional[datetime] = Field(default=None, description="PDF generation timestamp")
    
    # Quality assurance
    reviewed_by: Optional[str] = Field(default=None, description="Reviewer name")
    review_date: Optional[date] = Field(default=None, description="Review date")
    review_comments: Optional[str] = Field(default=None, description="Review comments")
    
    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Report tags")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = self.dict(by_alias=True, exclude_none=True)
        if self.id:
            data["_id"] = ObjectId(self.id)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PsychologicalReport":
        """Create instance from MongoDB document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
    
    def add_test_result(self, test_result: TestResult):
        """Add a test result to the report"""
        self.tests_administered.append(test_result)
        self.updated_at = datetime.utcnow()
    
    def remove_test_result(self, test_name: str):
        """Remove a test result by test name"""
        self.tests_administered = [
            test for test in self.tests_administered 
            if test.test_name != test_name
        ]
        self.updated_at = datetime.utcnow()
    
    def get_test_result(self, test_name: str) -> Optional[TestResult]:
        """Get a test result by test name"""
        for test in self.tests_administered:
            if test.test_name == test_name:
                return test
        return None
    
    def add_diagnostic_impression(self, diagnosis: str):
        """Add a diagnostic impression"""
        if diagnosis not in self.diagnostic_impressions:
            self.diagnostic_impressions.append(diagnosis)
            self.updated_at = datetime.utcnow()
    
    def add_recommendation(self, recommendation: str):
        """Add a recommendation"""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
            self.updated_at = datetime.utcnow()
    
    def add_treatment_goal(self, goal: str):
        """Add a treatment goal"""
        if goal not in self.treatment_goals:
            self.treatment_goals.append(goal)
            self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: ReportStatus, updated_by: str):
        """Update report status"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == ReportStatus.FINALIZED:
            self.finalized_at = datetime.utcnow()
    
    def mark_pdf_generated(self, file_path: str):
        """Mark that PDF has been generated"""
        self.pdf_generated = True
        self.pdf_file_path = file_path
        self.pdf_generation_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_authorized_viewer(self, user_id: str):
        """Add an authorized viewer"""
        if user_id not in self.authorized_viewers:
            self.authorized_viewers.append(user_id)
            self.updated_at = datetime.utcnow()
    
    def remove_authorized_viewer(self, user_id: str):
        """Remove an authorized viewer"""
        if user_id in self.authorized_viewers:
            self.authorized_viewers.remove(user_id)
            self.updated_at = datetime.utcnow()
    
    def can_view(self, user_id: str) -> bool:
        """Check if user can view this report"""
        return (
            user_id == self.created_by or 
            user_id in self.authorized_viewers or
            user_id == self.reviewed_by
        )
    
    def add_tag(self, tag: str):
        """Add a tag to the report"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the report"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def calculate_client_age(self) -> int:
        """Calculate client age based on date of birth and session date"""
        age = self.session_date.year - self.client_info.date_of_birth.year
        if (self.session_date.month, self.session_date.day) < (self.client_info.date_of_birth.month, self.client_info.date_of_birth.day):
            age -= 1
        return age
    
    def get_summary_data(self) -> Dict[str, Any]:
        """Get summary data for report listing"""
        return {
            "id": self.id,
            "report_number": self.report_number,
            "report_type": self.report_type.value,
            "status": self.status.value,
            "client_name": f"{self.client_info.first_name} {self.client_info.last_name}",
            "session_date": self.session_date.isoformat(),
            "psychologist_name": self.psychologist_name,
            "created_at": self.created_at.isoformat(),
            "pdf_generated": self.pdf_generated
        }