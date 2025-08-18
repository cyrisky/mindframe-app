"""Template model for managing HTML templates"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId


class TemplateVariable(BaseModel):
    """Model for template variables"""
    
    name: str = Field(..., description="Variable name")
    type: str = Field(..., description="Variable type: string, number, boolean, date, list, object")
    description: Optional[str] = Field(default=None, description="Variable description")
    required: bool = Field(default=True, description="Whether the variable is required")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Template(BaseModel):
    """Model for HTML templates"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = Field(..., description="Template name")
    display_name: str = Field(..., description="Human-readable template name")
    description: Optional[str] = Field(default=None, description="Template description")
    
    # Template content
    html_content: str = Field(..., description="HTML template content")
    css_content: Optional[str] = Field(default=None, description="CSS styles")
    js_content: Optional[str] = Field(default=None, description="JavaScript content")
    
    # Template metadata
    category: str = Field(..., description="Template category")
    subcategory: Optional[str] = Field(default=None, description="Template subcategory")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    # Template variables
    variables: List[TemplateVariable] = Field(default_factory=list, description="Template variables")
    
    # Version and status
    version: str = Field(default="1.0.0", description="Template version")
    status: str = Field(default="active", description="Status: active, inactive, deprecated")
    
    # File information
    file_path: Optional[str] = Field(default=None, description="Path to template file")
    file_size: Optional[int] = Field(default=None, description="Template file size")
    
    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times used")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    
    # Author and ownership
    author: Optional[str] = Field(default=None, description="Template author")
    created_by: Optional[str] = Field(default=None, description="User who created the template")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Template settings
    page_size: str = Field(default="A4", description="Default page size")
    orientation: str = Field(default="portrait", description="Page orientation")
    margins: Dict[str, str] = Field(
        default_factory=lambda: {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"},
        description="Page margins"
    )
    
    # Preview and thumbnail
    preview_url: Optional[str] = Field(default=None, description="Preview image URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail image URL")
    
    # Validation and requirements
    min_data_version: Optional[str] = Field(default=None, description="Minimum data version required")
    dependencies: List[str] = Field(default_factory=list, description="Template dependencies")
    
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
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        """Create instance from MongoDB document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
    
    def increment_usage(self):
        """Increment usage statistics"""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_variable(self, variable: TemplateVariable):
        """Add a variable to the template"""
        # Check if variable already exists
        for i, existing_var in enumerate(self.variables):
            if existing_var.name == variable.name:
                self.variables[i] = variable
                self.updated_at = datetime.utcnow()
                return
        
        self.variables.append(variable)
        self.updated_at = datetime.utcnow()
    
    def remove_variable(self, variable_name: str):
        """Remove a variable from the template"""
        self.variables = [var for var in self.variables if var.name != variable_name]
        self.updated_at = datetime.utcnow()
    
    def get_variable(self, name: str) -> Optional[TemplateVariable]:
        """Get a variable by name"""
        for variable in self.variables:
            if variable.name == name:
                return variable
        return None
    
    def get_required_variables(self) -> List[TemplateVariable]:
        """Get all required variables"""
        return [var for var in self.variables if var.required]
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate data against template variables"""
        errors = []
        
        # Check required variables
        for variable in self.get_required_variables():
            if variable.name not in data:
                errors.append(f"Required variable '{variable.name}' is missing")
        
        # Validate variable types and rules
        for variable in self.variables:
            if variable.name in data:
                value = data[variable.name]
                
                # Type validation
                if variable.type == "string" and not isinstance(value, str):
                    errors.append(f"Variable '{variable.name}' must be a string")
                elif variable.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Variable '{variable.name}' must be a number")
                elif variable.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Variable '{variable.name}' must be a boolean")
                elif variable.type == "list" and not isinstance(value, list):
                    errors.append(f"Variable '{variable.name}' must be a list")
                elif variable.type == "object" and not isinstance(value, dict):
                    errors.append(f"Variable '{variable.name}' must be an object")
        
        return errors
    
    def add_tag(self, tag: str):
        """Add a tag to the template"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the template"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def is_active(self) -> bool:
        """Check if template is active"""
        return self.status == "active"
    
    def deactivate(self):
        """Deactivate the template"""
        self.status = "inactive"
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate the template"""
        self.status = "active"
        self.updated_at = datetime.utcnow()
    
    def deprecate(self):
        """Mark template as deprecated"""
        self.status = "deprecated"
        self.updated_at = datetime.utcnow()