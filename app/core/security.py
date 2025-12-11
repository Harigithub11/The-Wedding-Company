"""
Security utilities for authentication and password hashing.
Implements JWT token generation/validation and bcrypt password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)

# Password hashing context with bcrypt
# Explicitly set 13 rounds for defense against future hardware improvements
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=13
)


class PasswordHasher:
    """
    Password hashing utility using bcrypt.
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain-text password using bcrypt.

        Args:
            password: Plain-text password

        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a hashed password.
        
        Implements constant-time failure to prevent timing attacks.

        Args:
            plain_password: Plain-text password to verify
            hashed_password: Hashed password to check against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Constant-time failure for invalid hash format
            # Burn equal time to prevent timing attacks
            pwd_context.hash("dummy")
            return False


class JWTHandler:
    """
    JWT token generation and validation utility.
    """

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Payload data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow().timestamp()  # Use timestamp for consistency
        })

        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Implements protection against algorithm confusion attacks and
        validates issued-at timestamp.

        Args:
            token: JWT token string to decode

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Prevent algorithm confusion attack - validate JWT header format
            if not token.startswith('eyJ'):
                logger.warning("Invalid JWT header format")
                return None
            
            # Hardcode algorithm to prevent algorithm confusion
            # Explicitly verify signature
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            
            # Validate issued-at timestamp to prevent future-dated tokens
            # Allow 60 second clock skew tolerance for distributed systems
            iat = payload.get("iat")
            if iat:
                current_timestamp = datetime.utcnow().timestamp()
                if iat > current_timestamp + 60:  # 60 second tolerance
                    logger.warning("Token with future iat rejected")
                    return None
            
            return payload

        except JWTError:
            # Don't leak error details that could reveal signature algorithm
            logger.warning("JWT decode failed")
            return None

    @staticmethod
    def create_token_for_admin(
        admin_id: str,
        organization_id: str,
        email: str
    ) -> str:
        """
        Create a JWT token specifically for admin authentication.
        
        Includes JTI (JWT ID) claim for token replay prevention.

        Args:
            admin_id: Admin user ID
            organization_id: Organization ID
            email: Admin email

        Returns:
            JWT token string
        """
        payload = {
            "admin_id": admin_id,
            "organization_id": organization_id,
            "email": email,
            "type": "admin",
            "jti": str(uuid.uuid4())  # JWT ID for token replay prevention
        }

        return JWTHandler.create_access_token(payload)


# Export instances for easy import
password_hasher = PasswordHasher()
jwt_handler = JWTHandler()
