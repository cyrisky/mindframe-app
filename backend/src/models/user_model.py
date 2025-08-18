"""User model for authentication and user management"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
import hashlib
import secrets


class UserPreferences(BaseModel):
    """User preferences model"""
    
    theme: str = Field(default="light", description="UI theme preference")
    language: str = Field(default="en", description="Language preference")
    timezone: str = Field(default="UTC", description="Timezone preference")
    notifications_enabled: bool = Field(default=True, description="Email notifications enabled")
    default_page_size: str = Field(default="A4", description="Default PDF page size")
    default_orientation: str = Field(default="portrait", description="Default PDF orientation")
    auto_save_templates: bool = Field(default=True, description="Auto-save template changes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserQuota(BaseModel):
    """User quota and usage limits"""
    
    max_pdfs_per_month: int = Field(default=100, description="Maximum PDFs per month")
    max_storage_mb: int = Field(default=1000, description="Maximum storage in MB")
    max_template_count: int = Field(default=50, description="Maximum number of templates")
    
    current_pdfs_this_month: int = Field(default=0, description="Current PDFs generated this month")
    current_storage_mb: float = Field(default=0.0, description="Current storage usage in MB")
    current_template_count: int = Field(default=0, description="Current number of templates")
    
    quota_reset_date: datetime = Field(default_factory=datetime.utcnow, description="When quota resets")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def is_pdf_quota_exceeded(self) -> bool:
        """Check if PDF generation quota is exceeded"""
        return self.current_pdfs_this_month >= self.max_pdfs_per_month
    
    def is_storage_quota_exceeded(self) -> bool:
        """Check if storage quota is exceeded"""
        return self.current_storage_mb >= self.max_storage_mb
    
    def is_template_quota_exceeded(self) -> bool:
        """Check if template quota is exceeded"""
        return self.current_template_count >= self.max_template_count
    
    def reset_monthly_quota(self):
        """Reset monthly quotas"""
        self.current_pdfs_this_month = 0
        self.quota_reset_date = datetime.utcnow()


class User(BaseModel):
    """User model for authentication and profile management"""
    
    id: Optional[str] = Field(default=None, alias="_id")
    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    
    # Authentication
    password_hash: str = Field(..., description="Hashed password")
    salt: str = Field(..., description="Password salt")
    
    # Profile information
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    display_name: Optional[str] = Field(default=None, description="Display name")
    avatar_url: Optional[str] = Field(default=None, description="Avatar image URL")
    bio: Optional[str] = Field(default=None, description="User biography")
    
    # Account status
    is_active: bool = Field(default=True, description="Account is active")
    is_verified: bool = Field(default=False, description="Email is verified")
    is_admin: bool = Field(default=False, description="User has admin privileges")
    
    # Roles and permissions
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    
    # User preferences and settings
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    quota: UserQuota = Field(default_factory=UserQuota)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")
    last_activity: Optional[datetime] = Field(default=None, description="Last activity timestamp")
    
    # Security
    failed_login_attempts: int = Field(default=0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(default=None, description="Account locked until")
    password_changed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # API and session management
    api_key: Optional[str] = Field(default=None, description="API key for external access")
    session_tokens: List[str] = Field(default_factory=list, description="Active session tokens")
    
    # Organization and team
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    team_ids: List[str] = Field(default_factory=list, description="Team IDs")
    
    # Verification and recovery
    email_verification_token: Optional[str] = Field(default=None, description="Email verification token")
    password_reset_token: Optional[str] = Field(default=None, description="Password reset token")
    password_reset_expires: Optional[datetime] = Field(default=None, description="Password reset expiry")
    
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
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create instance from MongoDB document"""
        if "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Hash a password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash.hex(), salt
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash"""
        password_hash, _ = self.hash_password(password, self.salt)
        return password_hash == self.password_hash
    
    def set_password(self, password: str):
        """Set a new password"""
        self.password_hash, self.salt = self.hash_password(password)
        self.password_changed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        self.api_key = secrets.token_urlsafe(32)
        self.updated_at = datetime.utcnow()
        return self.api_key
    
    def add_session_token(self, token: str):
        """Add a session token"""
        if token not in self.session_tokens:
            self.session_tokens.append(token)
            self.updated_at = datetime.utcnow()
    
    def remove_session_token(self, token: str):
        """Remove a session token"""
        if token in self.session_tokens:
            self.session_tokens.remove(token)
            self.updated_at = datetime.utcnow()
    
    def clear_all_sessions(self):
        """Clear all session tokens"""
        self.session_tokens = []
        self.updated_at = datetime.utcnow()
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.failed_login_attempts = 0
        self.updated_at = datetime.utcnow()
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        self.updated_at = datetime.utcnow()
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow().replace(minute=datetime.utcnow().minute + 30)
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def unlock_account(self):
        """Unlock the account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.updated_at = datetime.utcnow()
    
    def add_role(self, role: str):
        """Add a role to the user"""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.utcnow()
    
    def remove_role(self, role: str):
        """Remove a role from the user"""
        if role in self.roles:
            self.roles.remove(role)
            self.updated_at = datetime.utcnow()
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles or self.is_admin
    
    def add_permission(self, permission: str):
        """Add a permission to the user"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: str):
        """Remove a permission from the user"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        return permission in self.permissions or self.is_admin
    
    def get_full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        else:
            return self.username
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for public API (excluding sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "roles": self.roles,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "preferences": self.preferences.dict()
        }