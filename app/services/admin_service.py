"""
Admin service for business logic.
Handles admin user operations and authentication.
"""

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import AdminModel
from app.core.security import PasswordHasher
from app.utils.validators import EmailValidator
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service class for admin business logic.
    Handles admin creation, authentication, and credential management.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize admin service.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.admin_model = AdminModel(database)
        self.password_hasher = PasswordHasher()

    async def create_admin(
        self,
        email: str,
        password: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Create a new admin user.

        Args:
            email: Admin email address
            password: Plain-text password
            organization_id: Associated organization ID

        Returns:
            Created admin document

        Raises:
            ValueError: If admin already exists
            Exception: If creation fails
        """
        try:
            # Validate email
            validated_email = EmailValidator.validate(email)

            # Check if admin already exists
            if await self.admin_model.exists(validated_email):
                raise ValueError(f"Admin with email '{validated_email}' already exists")

            # Hash password
            password_hash = self.password_hasher.hash_password(password)

            # Create admin document
            admin_doc = await self.admin_model.create(
                email=validated_email,
                password_hash=password_hash,
                organization_id=organization_id
            )

            logger.info(f"Admin created: {validated_email}")
            return admin_doc

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create admin: {e}")
            raise

    async def get_admin_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get admin by email address.

        Args:
            email: Admin email address

        Returns:
            Admin document if found, None otherwise
        """
        try:
            validated_email = EmailValidator.validate(email)
            return await self.admin_model.get_by_email(validated_email)
        except Exception as e:
            logger.error(f"Failed to get admin by email: {e}")
            raise

    async def authenticate_admin(
        self,
        email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate admin user.

        Args:
            email: Admin email address
            password: Plain-text password

        Returns:
            Admin document if authenticated, None otherwise
        """
        try:
            # Get admin by email
            admin = await self.get_admin_by_email(email)
            if not admin:
                return None

            # Verify password
            if not self.password_hasher.verify_password(
                password,
                admin["password_hash"]
            ):
                return None

            # Update last login
            await self.admin_model.update_last_login(str(admin["_id"]))

            return admin

        except Exception as e:
            logger.error(f"Failed to authenticate admin: {e}")
            raise
