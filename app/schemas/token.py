"""
Pydantic schemas for JWT token responses.
"""

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZG1pbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMiIsIm9yZ2FuaXphdGlvbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMSIsImVtYWlsIjoiYWRtaW5AYWNtZWNvcnAuY29tIiwidHlwZSI6ImFkbWluIiwiZXhwIjoxNzAyNDc0ODAwLCJpYXQiOjE3MDIzODg0MDB9.signature",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }
    }


class TokenData(BaseModel):
    """Schema for decoded token data (internal use)."""
    
    admin_id: str = Field(..., description="Admin user ID")
    organization_id: str = Field(..., description="Organization ID")
    email: str = Field(..., description="Admin email")
    type: str = Field(default="admin", description="Token type")
