"""
Admin database model for CRUD operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class AdminModel:
    """
    Admin model for database operations.
    Handles CRUD operations for the admins collection.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize admin model.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.collection = database["admins"]

    async def create(
        self,
        email: str,
        password_hash: str,
        organization_id: str
    ) -> Dict[str, Any]:
        """
        Create a new admin user.

        Args:
            email: Admin email address
            password_hash: Bcrypt hashed password
            organization_id: Associated organization ID

        Returns:
            Created admin document

        Raises:
            Exception: If creation fails
        """
        try:
            admin_doc = {
                "email": email,
                "password_hash": password_hash,
                "organization_id": ObjectId(organization_id),
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True,
                "role": "admin"
            }

            result = await self.collection.insert_one(admin_doc)
            admin_doc["_id"] = result.inserted_id

            logger.info(f"Created admin user: {email}")
            return admin_doc

        except Exception as e:
            logger.error(f"Failed to create admin: {e}")
            raise

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get admin by email address.

        Args:
            email: Admin email address

        Returns:
            Admin document if found, None otherwise
        """
        try:
            admin = await self.collection.find_one({"email": email})
            return admin

        except Exception as e:
            logger.error(f"Failed to get admin by email: {e}")
            raise

    async def get_by_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get admin by ID.

        Args:
            admin_id: Admin user ID

        Returns:
            Admin document if found, None otherwise
        """
        try:
            admin = await self.collection.find_one({
                "_id": ObjectId(admin_id)
            })
            return admin

        except Exception as e:
            logger.error(f"Failed to get admin by ID: {e}")
            raise

    async def get_by_organization_id(
        self,
        organization_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get admin by organization ID.

        Args:
            organization_id: Organization ID

        Returns:
            Admin document if found, None otherwise
        """
        try:
            admin = await self.collection.find_one({
                "organization_id": ObjectId(organization_id)
            })
            return admin

        except Exception as e:
            logger.error(f"Failed to get admin by organization ID: {e}")
            raise

    async def update_credentials(
        self,
        admin_id: str,
        email: Optional[str] = None,
        password_hash: Optional[str] = None
    ) -> bool:
        """
        Update admin credentials.

        Args:
            admin_id: Admin user ID
            email: New email (optional)
            password_hash: New password hash (optional)

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            update_data = {}
            
            if email:
                update_data["email"] = email
            
            if password_hash:
                update_data["password_hash"] = password_hash

            if not update_data:
                return False

            result = await self.collection.update_one(
                {"_id": ObjectId(admin_id)},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Updated admin credentials: {admin_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to update admin credentials: {e}")
            raise

    async def update_last_login(self, admin_id: str) -> bool:
        """
        Update last login timestamp.

        Args:
            admin_id: Admin user ID

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(admin_id)},
                {"$set": {"last_login": datetime.utcnow()}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to update last login: {e}")
            raise

    async def delete(self, admin_id: str) -> bool:
        """
        Delete admin user.

        Args:
            admin_id: Admin user ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(admin_id)
            })

            if result.deleted_count > 0:
                logger.info(f"Deleted admin: {admin_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to delete admin: {e}")
            raise

    async def delete_by_organization_id(self, organization_id: str) -> int:
        """
        Delete all admins for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Number of admins deleted
        """
        try:
            result = await self.collection.delete_many({
                "organization_id": ObjectId(organization_id)
            })

            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(
                    f"Deleted {deleted_count} admin(s) for organization: {organization_id}"
                )
            
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete admins by organization ID: {e}")
            raise

    async def exists(self, email: str) -> bool:
        """
        Check if admin with email exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        try:
            count = await self.collection.count_documents({"email": email})
            return count > 0

        except Exception as e:
            logger.error(f"Failed to check admin existence: {e}")
            raise

    async def create_indexes(self) -> None:
        """
        Create database indexes for performance.
        Should be called during application startup.
        """
        try:
            # Unique index on email
            await self.collection.create_index("email", unique=True)

            # Index on organization_id for lookups
            await self.collection.create_index("organization_id")

            # Compound index for email + organization_id
            await self.collection.create_index([
                ("email", 1),
                ("organization_id", 1)
            ])

            logger.info("Created indexes for admins collection")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
