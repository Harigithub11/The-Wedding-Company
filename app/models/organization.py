"""
Organization database model for CRUD operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class OrganizationModel:
    """
    Organization model for database operations.
    Handles CRUD operations for the organizations collection.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize organization model.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.collection = database["organizations"]

    async def create(
        self,
        organization_name: str,
        collection_name: str,
        admin_id: str
    ) -> Dict[str, Any]:
        """
        Create a new organization.

        Args:
            organization_name: Unique organization name
            collection_name: MongoDB collection name for this org
            admin_id: ID of the admin user

        Returns:
            Created organization document

        Raises:
            Exception: If creation fails
        """
        try:
            organization_doc = {
                "organization_name": organization_name,
                "collection_name": collection_name,
                "admin_id": ObjectId(admin_id) if admin_id else None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "active"
            }

            result = await self.collection.insert_one(organization_doc)
            organization_doc["_id"] = result.inserted_id

            logger.info(f"Created organization: {organization_name}")
            return organization_doc

        except Exception as e:
            logger.error(f"Failed to create organization: {e}")
            raise

    async def get_by_name(self, organization_name: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by name.

        Args:
            organization_name: Organization name to search for

        Returns:
            Organization document if found, None otherwise
        """
        try:
            organization = await self.collection.find_one({
                "organization_name": organization_name
            })
            return organization

        except Exception as e:
            logger.error(f"Failed to get organization by name: {e}")
            raise

    async def get_by_id(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by ID.

        Args:
            organization_id: Organization ID

        Returns:
            Organization document if found, None otherwise
        """
        try:
            organization = await self.collection.find_one({
                "_id": ObjectId(organization_id)
            })
            return organization

        except Exception as e:
            logger.error(f"Failed to get organization by ID: {e}")
            raise

    async def get_by_admin_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization by admin ID.

        Args:
            admin_id: Admin user ID

        Returns:
            Organization document if found, None otherwise
        """
        try:
            organization = await self.collection.find_one({
                "admin_id": ObjectId(admin_id)
            })
            return organization

        except Exception as e:
            logger.error(f"Failed to get organization by admin ID: {e}")
            raise

    async def update(
        self,
        organization_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """
        Update organization.

        Args:
            organization_id: Organization ID
            update_data: Fields to update

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            result = await self.collection.update_one(
                {"_id": ObjectId(organization_id)},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Updated organization: {organization_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to update organization: {e}")
            raise

    async def delete(self, organization_id: str) -> bool:
        """
        Delete organization.

        Args:
            organization_id: Organization ID

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            result = await self.collection.delete_one({
                "_id": ObjectId(organization_id)
            })

            if result.deleted_count > 0:
                logger.info(f"Deleted organization: {organization_id}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to delete organization: {e}")
            raise

    async def exists(self, organization_name: str) -> bool:
        """
        Check if organization exists.

        Args:
            organization_name: Organization name to check

        Returns:
            True if exists, False otherwise
        """
        try:
            count = await self.collection.count_documents({
                "organization_name": organization_name
            })
            return count > 0

        except Exception as e:
            logger.error(f"Failed to check organization existence: {e}")
            raise

    async def create_indexes(self) -> None:
        """
        Create database indexes for performance.
        Should be called during application startup.
        """
        try:
            # Unique index on organization_name
            await self.collection.create_index(
                "organization_name",
                unique=True
            )

            # Index on admin_id for lookups
            await self.collection.create_index("admin_id")

            # Index on created_at for sorting
            await self.collection.create_index("created_at")

            logger.info("Created indexes for organizations collection")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
