"""Pydantic models for API request validation"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator, model_validator
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    PSYCHOLOGIST = "psychologist"


class TemplateCategory(str, Enum):
    """Template category enumeration"""
    PERSONALITY = "personality"
    VALUES = "values"
    ASSESSMENT = "assessment"
    REPORT = "report"
    CUSTOM = "custom"


class FileType(str, Enum):
    """File type enumeration"""
    IMAGE = "image"
    DOCUMENT = "document"
    DATA = "data"


# Authentication Request Models
class UserRegistrationRequest(BaseModel):
    """User registration request model"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="User role")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one uppercase, lowercase, digit, and special character
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '@$!%*?&' for c in v)
        
        if not all([has_upper, has_lower, has_digit, has_special]):
            raise ValueError('Password must contain at least one uppercase letter, lowercase letter, digit, and special character')
        
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        
        # Allow only letters, spaces, hyphens, and apostrophes
        import re
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        return v.strip()


class UserLoginRequest(BaseModel):
    """User login request model"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    remember_me: Optional[bool] = Field(default=False, description="Remember login")


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation model"""
    
    token: str = Field(..., min_length=1, description="Reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        return UserRegistrationRequest.validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        return UserRegistrationRequest.validate_password_strength(v)


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    
    refresh_token: str = Field(..., min_length=1, description="Refresh token")


class EmailVerificationRequest(BaseModel):
    """Email verification request model"""
    
    token: str = Field(..., min_length=1, description="Verification token")


class TemplateDuplicateRequest(BaseModel):
    """Template duplicate request model"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Name for the duplicated template")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the duplicated template")
    
    @validator('name')
    def validate_template_name(cls, v):
        """Validate template name"""
        if not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()


class ForgotPasswordRequest(BaseModel):
    """Forgot password request model"""
    
    email: EmailStr = Field(..., description="User email address")


# Template Request Models
class TemplateVariableRequest(BaseModel):
    """Template variable request model"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Variable name")
    type: str = Field(..., description="Variable type")
    description: Optional[str] = Field(default=None, max_length=500, description="Variable description")
    required: bool = Field(default=True, description="Whether variable is required")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    
    @validator('name')
    def validate_variable_name(cls, v):
        """Validate variable name format"""
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Variable name must start with letter or underscore and contain only letters, numbers, and underscores')
        return v
    
    @validator('type')
    def validate_variable_type(cls, v):
        """Validate variable type"""
        allowed_types = ['string', 'number', 'boolean', 'date', 'list', 'object']
        if v not in allowed_types:
            raise ValueError(f'Variable type must be one of: {", ".join(allowed_types)}')
        return v


class TemplateCreateRequest(BaseModel):
    """Template creation request model"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(default="", max_length=1000, description="Template description")
    content: str = Field(..., min_length=1, description="Template content")
    category: TemplateCategory = Field(..., description="Template category")
    variables: List[TemplateVariableRequest] = Field(default_factory=list, description="Template variables")
    tags: List[str] = Field(default_factory=list, max_items=20, description="Template tags")
    is_public: bool = Field(default=False, description="Whether template is public")
    
    @validator('name')
    def validate_template_name(cls, v):
        """Validate template name"""
        if not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v:
            # Remove duplicates and empty tags
            v = list(set(tag.strip().lower() for tag in v if tag.strip()))
            
            # Validate tag format
            import re
            for tag in v:
                if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                    raise ValueError('Tags can only contain letters, numbers, hyphens, and underscores')
                if len(tag) > 50:
                    raise ValueError('Each tag must be 50 characters or less')
        
        return v


class TemplateUpdateRequest(BaseModel):
    """Template update request model"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    content: Optional[str] = Field(None, min_length=1, description="Template content")
    category: Optional[TemplateCategory] = Field(None, description="Template category")
    variables: Optional[List[TemplateVariableRequest]] = Field(None, description="Template variables")
    tags: Optional[List[str]] = Field(None, max_items=20, description="Template tags")
    is_public: Optional[bool] = Field(None, description="Whether template is public")
    
    @validator('name')
    def validate_template_name(cls, v):
        """Validate template name"""
        if v is not None and not v.strip():
            raise ValueError('Template name cannot be empty')
        return v.strip() if v else v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        return TemplateCreateRequest.validate_tags(v) if v is not None else v


class TemplateRenderRequest(BaseModel):
    """Template render request model"""
    
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    
    @validator('variables')
    def validate_variables(cls, v):
        """Validate template variables"""
        if not isinstance(v, dict):
            raise ValueError('Variables must be a dictionary')
        
        # Check for reasonable size limits
        if len(str(v)) > 10000:  # 10KB limit for variables
            raise ValueError('Variables data too large')
        
        return v


class TemplatePreviewRequest(BaseModel):
    """Template preview request model"""
    
    content: str = Field(..., min_length=1, description="Template content to preview")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    
    @validator('variables')
    def validate_variables(cls, v):
        """Validate template variables"""
        if not isinstance(v, dict):
            raise ValueError('Variables must be a dictionary')
        
        # Check for reasonable size limits
        if len(str(v)) > 10000:  # 10KB limit for variables
            raise ValueError('Variables data too large')
        
        return v


class TemplateValidationRequest(BaseModel):
    """Template validation request model"""
    
    data: Dict[str, Any] = Field(..., description="Data to validate against template")
    
    @validator('data')
    def validate_data(cls, v):
        """Validate template data"""
        if not isinstance(v, dict):
            raise ValueError('Data must be a dictionary')
        
        # Check for reasonable size limits
        if len(str(v)) > 50000:  # 50KB limit for validation data
            raise ValueError('Data too large for validation')
        
        return v


# PDF Generation Request Models
class PDFFromHtmlRequest(BaseModel):
    """PDF generation from HTML request model"""
    
    html_content: str = Field(..., min_length=1, description="HTML content to convert to PDF")
    css_content: Optional[str] = Field(None, description="CSS content for styling")
    options: Dict[str, Any] = Field(default_factory=dict, description="PDF generation options")
    
    @validator('html_content')
    def validate_html_content(cls, v):
        """Validate HTML content size"""
        max_size = 1024 * 1024  # 1MB
        if len(v.encode('utf-8')) > max_size:
            raise ValueError(f'HTML content too large. Maximum size: {max_size} bytes')
        return v
    
    @validator('css_content')
    def validate_css_content(cls, v):
        """Validate CSS content size"""
        if v is not None:
            max_size = 512 * 1024  # 512KB
            if len(v.encode('utf-8')) > max_size:
                raise ValueError(f'CSS content too large. Maximum size: {max_size} bytes')
        return v


class PDFFromTemplateRequest(BaseModel):
    """PDF generation from template request model"""
    
    template_name: str = Field(..., min_length=1, max_length=200, description="Template name")
    data: Dict[str, Any] = Field(..., description="Data for template rendering")
    options: Dict[str, Any] = Field(default_factory=dict, description="PDF generation options")
    
    @validator('data')
    def validate_data_size(cls, v):
        """Validate data size"""
        import json
        data_size = len(json.dumps(v))
        max_size = 1024 * 1024  # 1MB
        
        if data_size > max_size:
            raise ValueError(f'Data payload too large. Maximum size: {max_size} bytes')
        
        return v


class PsychologicalReportRequest(BaseModel):
    """Psychological report generation request model"""
    
    patient_info: Dict[str, Any] = Field(..., description="Patient information")
    test_results: List[Dict[str, Any]] = Field(..., description="Test results data")
    template_options: Dict[str, Any] = Field(default_factory=dict, description="Template options")
    
    @validator('patient_info')
    def validate_patient_info(cls, v):
        """Validate patient info structure"""
        required_fields = ['name', 'age', 'gender', 'test_date']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Patient info must include {field}')
        return v
    
    @validator('test_results')
    def validate_test_results(cls, v):
        """Validate test results structure"""
        if not v:
            raise ValueError('At least one test result is required')
        
        for result in v:
            required_fields = ['test_name', 'score']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f'Test result must include {field}')
        return v


class PDFGenerationRequest(BaseModel):
    """PDF generation request model (legacy)"""
    
    template_id: Optional[str] = Field(None, description="Template ID")
    template_content: Optional[str] = Field(None, description="Direct template content")
    data: Dict[str, Any] = Field(..., description="Data for template rendering")
    options: Dict[str, Any] = Field(default_factory=dict, description="PDF generation options")
    
    @model_validator(mode='before')
    @classmethod
    def validate_template_source(cls, values):
        """Validate that either template_id or template_content is provided"""
        template_id = values.get('template_id')
        template_content = values.get('template_content')
        
        if not template_id and not template_content:
            raise ValueError('Either template_id or template_content must be provided')
        
        if template_id and template_content:
            raise ValueError('Cannot provide both template_id and template_content')
        
        return values
    
    @validator('data')
    def validate_data_size(cls, v):
        """Validate data size"""
        import json
        data_size = len(json.dumps(v))
        max_size = 1024 * 1024  # 1MB
        
        if data_size > max_size:
            raise ValueError(f'Data payload too large. Maximum size: {max_size} bytes')
        
        return v


# Report Request Models
class ReportCreateRequest(BaseModel):
    """Report creation request model"""
    
    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    description: Optional[str] = Field(default="", max_length=1000, description="Report description")
    template_id: str = Field(..., description="Template ID")
    data: Dict[str, Any] = Field(..., description="Report data")
    tags: List[str] = Field(default_factory=list, max_items=20, description="Report tags")
    is_public: bool = Field(default=False, description="Whether report is public")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate report title"""
        if not v.strip():
            raise ValueError('Report title cannot be empty')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        return TemplateCreateRequest.validate_tags(v) if v else v


class ReportUpdateRequest(BaseModel):
    """Report update request model"""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Report title")
    description: Optional[str] = Field(None, max_length=1000, description="Report description")
    data: Optional[Dict[str, Any]] = Field(None, description="Report data")
    tags: Optional[List[str]] = Field(None, max_items=20, description="Report tags")
    is_public: Optional[bool] = Field(None, description="Whether report is public")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate report title"""
        if v is not None and not v.strip():
            raise ValueError('Report title cannot be empty')
        return v.strip() if v else v
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        return TemplateCreateRequest.validate_tags(v) if v else v


class ReportStatusUpdateRequest(BaseModel):
    """Report status update request model"""
    
    status: str = Field(..., description="Report status")
    notes: Optional[str] = Field(default="", max_length=1000, description="Status update notes")
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status value"""
        valid_statuses = ['draft', 'in_review', 'approved', 'published', 'archived']
        if v not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
        return v


class TestResultRequest(BaseModel):
    """Test result request model"""
    
    test_name: str = Field(..., min_length=1, max_length=200, description="Test name")
    test_type: str = Field(..., min_length=1, max_length=100, description="Test type")
    results: Dict[str, Any] = Field(..., description="Test results data")
    notes: Optional[str] = Field(default="", max_length=1000, description="Test notes")
    administered_date: Optional[str] = Field(None, description="Date test was administered")
    
    @validator('test_name')
    def validate_test_name(cls, v):
        """Validate test name"""
        if not v.strip():
            raise ValueError('Test name cannot be empty')
        return v.strip()
    
    @validator('test_type')
    def validate_test_type(cls, v):
        """Validate test type"""
        if not v.strip():
            raise ValueError('Test type cannot be empty')
        return v.strip()


# File Upload Request Models
class FileUploadRequest(BaseModel):
    """File upload request model"""
    
    file_type: FileType = Field(..., description="File type category")
    description: Optional[str] = Field(default="", max_length=500, description="File description")
    tags: List[str] = Field(default_factory=list, max_items=10, description="File tags")
    is_public: bool = Field(default=False, description="Whether file is public")
    
    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        return TemplateCreateRequest.validate_tags(v) if v else v


# Query Parameter Models
class PaginationParams(BaseModel):
    """Pagination parameters model"""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.limit


class SortParams(BaseModel):
    """Sort parameters model"""
    
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field"""
        # Define allowed sort fields
        allowed_fields = [
            'created_at', 'updated_at', 'name', 'title', 'email',
            'first_name', 'last_name', 'category', 'status'
        ]
        
        if v not in allowed_fields:
            raise ValueError(f'Invalid sort field. Allowed: {", ".join(allowed_fields)}')
        
        return v


class FilterParams(BaseModel):
    """Filter parameters model"""
    
    search: Optional[str] = Field(None, max_length=100, description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    status: Optional[str] = Field(None, description="Filter by status")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    
    @validator('search')
    def validate_search_query(cls, v):
        """Validate search query"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Search query must be at least 2 characters long')
        return v


class TemplateListParams(BaseModel):
    """Template list query parameters model"""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, max_length=100, description="Search query")
    category: Optional[TemplateCategory] = Field(None, description="Filter by category")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")
    
    @validator('search')
    def validate_search_query(cls, v):
        """Validate search query"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('Search query must be at least 2 characters long')
        return v
    
    @validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field"""
        allowed_fields = ['created_at', 'updated_at', 'name', 'category']
        if v not in allowed_fields:
            raise ValueError(f'Invalid sort field. Allowed: {", ".join(allowed_fields)}')
        return v
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.limit


# Assessment Request Models
class AssessmentSubmissionRequest(BaseModel):
    """Assessment submission request model"""
    
    assessment_type: str = Field(..., description="Type of assessment")
    responses: Dict[str, Any] = Field(..., description="Assessment responses")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('assessment_type')
    def validate_assessment_type(cls, v):
        """Validate assessment type"""
        allowed_types = ['personality', 'values', 'skills', 'custom']
        if v not in allowed_types:
            raise ValueError(f'Invalid assessment type. Allowed: {", ".join(allowed_types)}')
        return v
    
    @validator('responses')
    def validate_responses(cls, v):
        """Validate responses structure"""
        if not v:
            raise ValueError('Assessment responses cannot be empty')
        
        # Basic validation - responses should be a non-empty dict
        if not isinstance(v, dict):
            raise ValueError('Responses must be a dictionary')
        
        return v


# User Profile Request Models
class UserProfileUpdateRequest(BaseModel):
    """User profile update request model"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Last name")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Display name")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, pattern="^[a-z]{2}(-[A-Z]{2})?$", description="Language code")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        return UserRegistrationRequest.validate_names(v) if v is not None else v
    
    @validator('display_name')
    def validate_display_name(cls, v):
        """Validate display name"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Display name cannot be empty')
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone"""
        if v is not None:
            import pytz
            try:
                pytz.timezone(v)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError('Invalid timezone')
        return v


class AuthorizedViewerRequest(BaseModel):
    """Authorized viewer request model"""
    
    user_id: str = Field(..., min_length=1, description="User ID to add as viewer")
    permissions: List[str] = Field(default_factory=lambda: ['view'], description="Permissions to grant")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('User ID cannot be empty or whitespace only')
        return v.strip()
    
    @validator('permissions')
    def validate_permissions(cls, v):
        if not v:
            return ['view']  # Default permission
        
        valid_permissions = ['view', 'edit', 'delete', 'share']
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f'Invalid permission: {permission}. Valid permissions are: {valid_permissions}')
        
        # Ensure 'view' is always included
        if 'view' not in v:
            v.append('view')
        
        return list(set(v))  # Remove duplicates


class ReportDuplicateRequest(BaseModel):
    """Report duplicate request model"""
    
    title: str = Field(..., min_length=1, max_length=200, description="New report title")
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Report title cannot be empty or whitespace only')
        return v.strip()


class BatchReportItem(BaseModel):
    """Individual report item for batch generation"""
    
    patient_id: str = Field(..., min_length=1, description="Patient ID")
    template_id: str = Field(..., min_length=1, description="Template ID")
    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    description: Optional[str] = Field(default="", max_length=1000, description="Report description")
    data: Dict[str, Any] = Field(default_factory=dict, description="Report data")
    tags: List[str] = Field(default_factory=list, max_items=20, description="Report tags")
    is_public: bool = Field(default=False, description="Whether report is public")
    
    @validator('patient_id', 'template_id')
    def validate_ids(cls, v):
        if not v.strip():
            raise ValueError('ID cannot be empty or whitespace only')
        return v.strip()
    
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Report title cannot be empty or whitespace only')
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v):
        if v:
            for tag in v:
                if not isinstance(tag, str) or not tag.strip():
                    raise ValueError('All tags must be non-empty strings')
        return [tag.strip() for tag in v] if v else []


class BatchGenerateReportsRequest(BaseModel):
    """Batch generate reports request model"""
    
    reports: List[BatchReportItem] = Field(..., min_items=1, max_items=50, description="List of reports to generate")
    
    @validator('reports')
    def validate_reports_list(cls, v):
        if not v:
            raise ValueError('Reports list cannot be empty')
        if len(v) > 50:
            raise ValueError('Batch size cannot exceed 50 reports')
        return v


# Job Queue Request Models
class PDFJobSubmissionRequest(BaseModel):
    """PDF job submission request model"""
    
    code: str = Field(..., min_length=1, max_length=100, description="Test code identifier")
    product_id: str = Field(..., min_length=1, max_length=100, description="Product ID")
    user_email: Optional[EmailStr] = Field(None, description="User email address")
    user_name: Optional[str] = Field(None, min_length=1, max_length=200, description="User full name")
    callback_url: Optional[str] = Field(None, description="Webhook callback URL for job completion")
    
    @validator('code')
    def validate_code(cls, v):
        """Validate test code"""
        if not v.strip():
            raise ValueError('Test code cannot be empty or only whitespace')
        return v.strip()
    
    @validator('product_id')
    def validate_product_id(cls, v):
        """Validate product ID"""
        if not v.strip():
            raise ValueError('Product ID cannot be empty or only whitespace')
        return v.strip()
    
    @validator('user_name')
    def validate_user_name(cls, v):
        """Validate user name"""
        if v is not None and not v.strip():
            raise ValueError('User name cannot be empty or only whitespace')
        return v.strip() if v is not None else None
    
    @validator('callback_url')
    def validate_callback_url(cls, v):
        """Validate callback URL"""
        if v is not None and v.strip():
            import re
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
                r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                r'localhost|'
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                r'(?::\d+)?'
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v.strip()):
                raise ValueError('Invalid callback URL format')
            return v.strip()
        return v


class JobStatusRequest(BaseModel):
    """Job status request model"""
    
    job_id: str = Field(..., min_length=1, description="Job ID to check status for")
    
    @validator('job_id')
    def validate_job_id(cls, v):
        """Validate job ID"""
        if not v.strip():
            raise ValueError('Job ID cannot be empty or only whitespace')
        return v.strip()


# Export all models
__all__ = [
    'UserRole',
    'TemplateCategory',
    'FileType',
    'UserRegistrationRequest',
    'UserLoginRequest',
    'PasswordResetRequest',
    'PasswordResetConfirmRequest',
    'ChangePasswordRequest',
    'RefreshTokenRequest',
    'EmailVerificationRequest',
    'ForgotPasswordRequest',
    'TemplateDuplicateRequest',
    'TemplateVariableRequest',
    'TemplateCreateRequest',
    'TemplateUpdateRequest',
    'TemplateRenderRequest',
    'TemplatePreviewRequest',
    'TemplateValidationRequest',
    'PDFFromHtmlRequest',
    'PDFFromTemplateRequest',
    'PsychologicalReportRequest',
    'PDFGenerationRequest',
    'ReportCreateRequest',
    'ReportUpdateRequest',
    'ReportStatusUpdateRequest',
    'TestResultRequest',
    'AuthorizedViewerRequest',
    'ReportDuplicateRequest',
    'BatchReportItem',
    'BatchGenerateReportsRequest',
    'PDFJobSubmissionRequest',
    'JobStatusRequest',
    'FileUploadRequest',
    'PaginationParams',
    'SortParams',
    'FilterParams',
    'TemplateListParams',
    'AssessmentSubmissionRequest',
    'UserProfileUpdateRequest'
]