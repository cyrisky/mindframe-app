# Models Directory

This directory contains the data models for the Mindframe application, built using Pydantic for data validation and MongoDB integration.

## Overview

The models define the structure and validation rules for all data entities in the system. Each model includes:
- Field validation using Pydantic
- MongoDB integration with ObjectId handling
- Business logic methods for data manipulation
- Type hints for better code maintainability

## Available Models

### 1. User Model (`user_model.py`)

The `User` model handles authentication, user profiles, and account management.

#### Key Components:
- **UserPreferences**: UI theme, language, timezone, and application settings
- **UserQuota**: Usage limits and quota management for PDFs, storage, and templates
- **User**: Main user entity with authentication and profile data

#### Core Features:
- Password hashing with PBKDF2 and salt
- Session token management
- Role-based access control (RBAC)
- Account locking after failed login attempts
- API key generation
- Email verification and password reset tokens

#### Key Fields:
```python
# Authentication
username: str
email: EmailStr
password_hash: str
salt: str

# Profile
first_name: Optional[str]
last_name: Optional[str]
display_name: Optional[str]
avatar_url: Optional[str]

# Security
roles: List[str]
permissions: List[str]
failed_login_attempts: int
locked_until: Optional[datetime]

# Preferences and Quota
preferences: UserPreferences
quota: UserQuota
```

#### Usage Example:
```python
from models import User

# Create new user
user = User(
    username="john_doe",
    email="john@example.com",
    first_name="John",
    last_name="Doe"
)

# Set password
user.set_password("secure_password")

# Verify password
is_valid = user.verify_password("secure_password")

# Add role
user.add_role("admin")

# Check permissions
has_access = user.has_role("admin")
```

### 2. PDF Document Model (`pdf_model.py`)

The `PDFDocument` model manages generated PDF files and their metadata.

#### Core Features:
- File metadata tracking (size, path, content type)
- Generation method tracking (HTML, template, URL)
- Download statistics
- Expiration handling
- Tag-based categorization

#### Key Fields:
```python
# File Information
filename: str
file_path: str
file_size: int
content_type: str

# Generation Metadata
template_name: Optional[str]
generation_method: str  # html, template, url
source_content: Optional[str]

# User Context
user_id: Optional[str]
session_id: Optional[str]

# Status and Tracking
status: str  # pending, completed, failed
download_count: int
last_downloaded: Optional[datetime]
expires_at: Optional[datetime]

# Organization
tags: List[str]
category: Optional[str]
```

#### Usage Example:
```python
from models import PDFDocument

# Create PDF document record
pdf_doc = PDFDocument(
    filename="report.pdf",
    file_path="/storage/pdfs/report_123.pdf",
    file_size=1024000,
    generation_method="template",
    template_name="psychological_report",
    user_id="user_123"
)

# Mark as completed
pdf_doc.mark_as_completed("/storage/pdfs/report_123.pdf", 1024000)

# Update download stats
pdf_doc.update_download_stats()

# Add tags
pdf_doc.add_tag("psychological")
pdf_doc.add_tag("assessment")
```

### 3. Template Model (`template_model.py`)

The `Template` model manages HTML templates for PDF generation.

#### Key Components:
- **TemplateVariable**: Defines template variables with validation rules
- **Template**: Main template entity with content and metadata

#### Core Features:
- HTML, CSS, and JavaScript content storage
- Variable definition and validation
- Usage statistics tracking
- Version management
- Category and tag organization

#### Key Fields:
```python
# Template Identity
name: str
display_name: str
description: Optional[str]

# Content
html_content: str
css_content: Optional[str]
js_content: Optional[str]

# Variables
variables: List[TemplateVariable]

# Organization
category: str
subcategory: Optional[str]
tags: List[str]

# Version and Status
version: str
status: str  # active, inactive, deprecated

# Usage Tracking
usage_count: int
last_used: Optional[datetime]

# Page Settings
page_size: str  # A4, Letter, etc.
orientation: str  # portrait, landscape
margins: Dict[str, str]
```

#### Template Variables:
```python
class TemplateVariable(BaseModel):
    name: str
    type: str  # string, number, boolean, date, list, object
    description: Optional[str]
    required: bool
    default_value: Optional[Any]
    validation_rules: Dict[str, Any]
```

#### Usage Example:
```python
from models import Template, TemplateVariable

# Create template variable
var = TemplateVariable(
    name="client_name",
    type="string",
    description="Client's full name",
    required=True
)

# Create template
template = Template(
    name="basic_report",
    display_name="Basic Psychological Report",
    html_content="<h1>{{client_name}}</h1>",
    category="psychological",
    variables=[var]
)

# Validate data against template
data = {"client_name": "John Doe"}
errors = template.validate_data(data)

# Increment usage
template.increment_usage()
```

### 4. Psychological Report Model (`report_model.py`)

The `PsychologicalReport` model manages comprehensive psychological assessment reports.

#### Key Components:
- **ReportType**: Enum for different report types
- **ReportStatus**: Enum for report workflow states
- **TestResult**: Individual psychological test results
- **ClientInformation**: Client demographics and background
- **PsychologicalReport**: Main report entity

#### Core Features:
- Comprehensive client information management
- Multiple test result tracking
- Clinical impressions and diagnoses
- Treatment recommendations and goals
- Risk assessment and safety concerns
- Access control and confidentiality
- PDF generation tracking
- Quality assurance workflow

#### Report Types:
```python
class ReportType(str, Enum):
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
```

#### Report Status:
```python
class ReportStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    FINALIZED = "finalized"
    ARCHIVED = "archived"
```

#### Key Fields:
```python
# Report Metadata
report_number: str
report_type: ReportType
status: ReportStatus

# Client and Session
client_info: ClientInformation
session_date: date
report_date: date

# Professional Information
psychologist_name: str
psychologist_license: Optional[str]
psychologist_credentials: Optional[str]

# Clinical Content
reason_for_referral: str
background_information: Optional[str]
behavioral_observations: Optional[str]
tests_administered: List[TestResult]

# Clinical Findings
clinical_impressions: Optional[str]
diagnostic_impressions: List[str]
differential_diagnosis: List[str]

# Treatment and Recommendations
recommendations: List[str]
treatment_goals: List[str]
prognosis: Optional[str]

# Risk Assessment
risk_factors: List[str]
protective_factors: List[str]
safety_concerns: Optional[str]

# Access Control
created_by: str
authorized_viewers: List[str]
confidentiality_level: str

# PDF Generation
pdf_generated: bool
pdf_file_path: Optional[str]
pdf_generation_date: Optional[datetime]
```

#### Usage Example:
```python
from models import PsychologicalReport, ClientInformation, TestResult, ReportType

# Create client information
client = ClientInformation(
    client_id="client_123",
    first_name="Jane",
    last_name="Smith",
    date_of_birth=date(1990, 5, 15),
    gender="Female"
)

# Create test result
test = TestResult(
    test_name="MMPI-2",
    administration_date=date.today(),
    raw_scores={"depression": 65, "anxiety": 70},
    interpretation="Elevated scores suggest..."
)

# Create report
report = PsychologicalReport(
    report_number="RPT-2024-001",
    report_type=ReportType.ASSESSMENT,
    client_info=client,
    session_date=date.today(),
    psychologist_name="Dr. John Doe",
    reason_for_referral="Assessment for anxiety and depression",
    created_by="user_123"
)

# Add test result
report.add_test_result(test)

# Add diagnostic impression
report.add_diagnostic_impression("Major Depressive Disorder")

# Add recommendation
report.add_recommendation("Cognitive Behavioral Therapy")

# Update status
report.update_status(ReportStatus.FINALIZED, "user_123")
```

## Database Integration

All models include MongoDB integration methods:

### Common Methods:
- `to_dict()`: Convert model to MongoDB document
- `from_dict(data)`: Create model instance from MongoDB document
- ObjectId handling for `_id` fields
- Automatic timestamp management

### Example Usage:
```python
# Save to MongoDB
user_dict = user.to_dict()
collection.insert_one(user_dict)

# Load from MongoDB
user_data = collection.find_one({"username": "john_doe"})
user = User.from_dict(user_data)
```

## Validation and Type Safety

All models use Pydantic for:
- Automatic type validation
- Field constraints and validation rules
- JSON serialization/deserialization
- IDE support with type hints

### Custom Validation:
```python
# Email validation
email: EmailStr

# Field constraints
username: str = Field(..., min_length=3, max_length=50)

# Custom validators
@validator('password')
def validate_password(cls, v):
    if len(v) < 8:
        raise ValueError('Password must be at least 8 characters')
    return v
```

## Best Practices

1. **Always use model methods** for data manipulation instead of direct field access
2. **Validate data** before saving to database using model validation
3. **Use type hints** for better IDE support and code maintainability
4. **Handle ObjectId conversion** when working with MongoDB
5. **Update timestamps** when modifying model data
6. **Use enums** for predefined values to ensure data consistency
7. **Implement proper error handling** for validation failures

## Testing

Example test structure:
```python
import pytest
from models import User

def test_user_creation():
    user = User(
        username="test_user",
        email="test@example.com"
    )
    assert user.username == "test_user"
    assert user.is_active is True

def test_password_hashing():
    user = User(username="test", email="test@example.com")
    user.set_password("password123")
    assert user.verify_password("password123") is True
    assert user.verify_password("wrong_password") is False
```

## Migration and Schema Changes

When updating models:
1. Add new fields as optional with default values
2. Create migration scripts for existing data
3. Update validation rules carefully
4. Test with existing data before deployment
5. Document breaking changes

## Security Considerations

- **Never store plain text passwords** - always use hashed passwords
- **Validate all input data** using Pydantic validators
- **Implement proper access controls** for sensitive data
- **Use secure random tokens** for API keys and session tokens
- **Follow GDPR guidelines** for personal data handling
- **Implement data retention policies** for temporary data

## Performance Tips

- Use **projection** when querying MongoDB to limit returned fields
- Implement **indexing** on frequently queried fields
- Use **batch operations** for multiple document updates
- Consider **data denormalization** for read-heavy operations
- Implement **caching** for frequently accessed data

## Related Documentation

- [Authentication System](../AUTH_README.md)
- [Services Documentation](../services/README.md)
- [API Documentation](../api/README.md)
- [Database Schema](../../MONGODB_INTEGRATION_GUIDE.md)