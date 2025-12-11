"""
Pydantic schemas for organization-related requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    
    organization_name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique organization name"
    )
    email: EmailStr = Field(
        ...,
        description="Admin email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Admin password"
    )

    @field_validator('organization_name')
    @classmethod
    def validate_organization_name(cls, v: str) -> str:
        """
        Validate organization name format.
        - Only alphanumeric and underscores
        - No spaces or special characters
        - Lowercase
        """
        # Remove leading/trailing whitespace
        v = v.strip()
        
        # Convert to lowercase
        v = v.lower()
        
        # Replace spaces with underscores
        v = v.replace(' ', '_')
        
        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError(
                'Organization name must contain only lowercase letters, numbers, and underscores'
            )
        
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_name": "acme_corp",
                "email": "admin@acmecorp.com",
                "password": "SecurePass123"
            }
        }
    }


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    
    organization_name: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="New organization name"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="New admin email"
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="New admin password"
    )

    @field_validator('organization_name')
    @classmethod
    def validate_organization_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate organization name format if provided."""
        if v is None:
            return v
        
        v = v.strip().lower().replace(' ', '_')
        
        if not re.match(r'^[a-z0-9_]+$', v):
            raise ValueError(
                'Organization name must contain only lowercase letters, numbers, and underscores'
            )
        
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "organization_name": "acme_corp_updated",
                "email": "newemail@acmecorp.com",
                "password": "NewSecurePass123"
            }
        }
    }


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    
    id: str = Field(..., description="Organization ID")
    organization_name: str = Field(..., description="Organization name")
    collection_name: str = Field(..., description="MongoDB collection name")
    admin_email: str = Field(..., description="Admin email address")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "organization_name": "acme_corp",
                "collection_name": "org_acme_corp",
                "admin_email": "admin@acmecorp.com",
                "created_at": "2025-12-12T10:30:00Z",
                "updated_at": "2025-12-12T10:30:00Z"
            }
        }
    }


class OrganizationCreateResponse(BaseModel):
    """Schema for organization creation response."""
    
    message: str = Field(..., description="Success message")
    organization: OrganizationResponse = Field(..., description="Organization details")
    admin_id: str = Field(..., description="Admin user ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Organization created successfully",
                "organization": {
                    "id": "507f1f77bcf86cd799439011",
                    "organization_name": "acme_corp",
                    "collection_name": "org_acme_corp",
                    "admin_email": "admin@acmecorp.com",
                    "created_at": "2025-12-12T10:30:00Z",
                    "updated_at": "2025-12-12T10:30:00Z"
                },
                "admin_id": "507f1f77bcf86cd799439012"
            }
        }
    }


class OrganizationUpdateResponse(BaseModel):
    """Schema for organization update response."""
    
    message: str = Field(..., description="Success message")
    organization: OrganizationResponse = Field(..., description="Updated organization details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Organization updated successfully",
                "organization": {
                    "id": "507f1f77bcf86cd799439011",
                    "organization_name": "acme_corp_updated",
                    "collection_name": "org_acme_corp_updated",
                    "admin_email": "newemail@acmecorp.com",
                    "created_at": "2025-12-12T10:30:00Z",
                    "updated_at": "2025-12-12T15:45:00Z"
                }
            }
        }
    }


class OrganizationDeleteResponse(BaseModel):
    """Schema for organization deletion response."""
    
    message: str = Field(..., description="Success message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Organization 'acme_corp' deleted successfully"
            }
        }
    }
