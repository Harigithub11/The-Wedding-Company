"""
Pydantic schemas for admin-related requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr


class AdminLogin(BaseModel):
    """Schema for admin login request."""
    
    email: EmailStr = Field(
        ...,
        description="Admin email address"
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Admin password"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@acmecorp.com",
                "password": "SecurePass123"
            }
        }
    }


class AdminCreate(BaseModel):
    """Schema for creating admin user (internal use)."""
    
    email: EmailStr = Field(
        ...,
        description="Admin email address"
    )
    password_hash: str = Field(
        ...,
        description="Hashed password"
    )
    organization_id: str = Field(
        ...,
        description="Associated organization ID"
    )


class AdminResponse(BaseModel):
    """Schema for admin user response."""
    
    id: str = Field(..., description="Admin user ID")
    email: str = Field(..., description="Admin email address")
    organization_id: str = Field(..., description="Organization ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "email": "admin@acmecorp.com",
                "organization_id": "507f1f77bcf86cd799439011"
            }
        }
    }
