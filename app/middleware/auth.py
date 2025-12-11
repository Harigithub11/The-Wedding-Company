"""
Authentication middleware and dependencies.
Implements JWT token validation and user authentication for protected routes.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import jwt_handler
from app.core.database import db_manager
from app.models import AdminModel
from app.schemas import TokenData
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Validates the JWT token and returns the user data.
    This dependency should be used on all protected routes.
    
    Args:
        token: JWT token extracted from Authorization header
        
    Returns:
        TokenData containing admin_id, organization_id, email
        
    Raises:
        HTTPException 401: If token is invalid, expired, or missing required fields
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate token
        payload = jwt_handler.decode_token(token)
        
        if payload is None:
            logger.warning("Token validation failed: Invalid token")
            raise credentials_exception
        
        # Extract required fields
        admin_id: Optional[str] = payload.get("admin_id")
        organization_id: Optional[str] = payload.get("organization_id")
        email: Optional[str] = payload.get("email")
        token_type: Optional[str] = payload.get("type")
        
        # Validate required fields
        if admin_id is None or organization_id is None or email is None:
            logger.warning("Token validation failed: Missing required fields")
            raise credentials_exception
        
        # Validate token type
        if token_type != "admin":
            logger.warning(f"Token validation failed: Invalid token type '{token_type}'")
            raise credentials_exception
        
        # Create and return token data
        token_data = TokenData(
            admin_id=admin_id,
            organization_id=organization_id,
            email=email,
            type=token_type
        )
        
        # Don't log PII - use masked admin_id instead
        logger.info(f"Authentication successful for admin_id: {admin_id[:8]}***")
        return token_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get current user and verify they are active.
    
    This checks that the admin user exists in the database and is active.
    Use this for routes that require an active admin user.
    
    Args:
        current_user: TokenData from get_current_user dependency
        
    Returns:
        TokenData if user is active
        
    Raises:
        HTTPException 403: If user account is inactive or not found
    """
    try:
        # Get database instance
        database = db_manager.database
        admin_model = AdminModel(database)
        
        # Check if admin exists and is active
        admin = await admin_model.get_by_id(current_user.admin_id)
        
        if admin is None:
            logger.warning(f"Admin not found: {current_user.admin_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account not found"
            )
        
        if not admin.get("is_active", False):
            logger.warning(f"Inactive admin attempted access: {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify user status"
        )


async def verify_organization_access(
    organization_id: str,
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to verify user has access to a specific organization.
    
    Ensures the authenticated user belongs to the requested organization.
    
    Args:
        organization_id: Organization ID to verify access to
        current_user: TokenData from get_current_user dependency
        
    Returns:
        TokenData if user has access to organization
        
    Raises:
        HTTPException 403: If user doesn't have access to organization
    """
    if current_user.organization_id != organization_id:
        logger.warning(
            f"Access denied: User {current_user.email} attempted to access "
            f"organization {organization_id} but belongs to {current_user.organization_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization"
        )
    
    return current_user


# Optional: Rate limiting decorator (bonus feature)
class RateLimiter:
    """
    Simple rate limiter for API endpoints.
    Can be expanded with Redis for production use.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # In production, use Redis for distributed rate limiting
        self.requests = {}
    
    async def __call__(self, token: str = Depends(oauth2_scheme)) -> None:
        """
        Check rate limit for current user.
        
        Args:
            token: JWT token
            
        Raises:
            HTTPException 429: If rate limit exceeded
        """
        # Decode token to get user identifier
        payload = jwt_handler.decode_token(token)
        if payload:
            user_id = payload.get("admin_id", "unknown")
            
            # Simple in-memory rate limiting (use Redis in production)
            from datetime import datetime
            now = datetime.utcnow().timestamp()
            
            if user_id not in self.requests:
                self.requests[user_id] = []
            
            # Remove old requests outside window
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if now - req_time < self.window_seconds
            ]
            
            # Check if limit exceeded
            if len(self.requests[user_id]) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
                )
            
            # Add current request
            self.requests[user_id].append(now)


# Export rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
