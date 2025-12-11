"""
Collection service for dynamic MongoDB collection management.
Handles creation, deletion, and migration of organization-specific collections.
"""

from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class CollectionService:
    """
    Service class for managing dynamic MongoDB collections.
    Handles organization-specific collection operations.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize collection service.

        Args:
            database: MongoDB database instance
        """
        self.database = database

    async def create_collection(self, collection_name: str) -> bool:
        """
        Create a new MongoDB collection.

        Args:
            collection_name: Name of the collection to create

        Returns:
            True if created successfully, False if already exists

        Raises:
            Exception: If creation fails
        """
        try:
            # Check if collection already exists
            existing_collections = await self.database.list_collection_names()
            
            if collection_name in existing_collections:
                logger.warning(f"Collection '{collection_name}' already exists")
                return False

            # Create collection
            await self.database.create_collection(collection_name)
            
            logger.info(f"Created collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a MongoDB collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if deleted successfully, False if doesn't exist

        Raises:
            Exception: If deletion fails
        """
        try:
            # Check if collection exists
            if not await self.collection_exists(collection_name):
                logger.warning(f"Collection '{collection_name}' does not exist")
                return False

            # Delete collection
            await self.database.drop_collection(collection_name)
            
            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            raise

    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if exists, False otherwise
        """
        try:
            existing_collections = await self.database.list_collection_names()
            return collection_name in existing_collections
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            raise

    async def migrate_collection(
        self,
        source_collection: str,
        target_collection: str
    ) -> int:
        """
        Migrate all data from source collection to target collection.

        Args:
            source_collection: Source collection name
            target_collection: Target collection name

        Returns:
            Number of documents migrated

        Raises:
            Exception: If migration fails
        """
        try:
            # Check if source exists
            if not await self.collection_exists(source_collection):
                raise ValueError(f"Source collection '{source_collection}' does not exist")

            # Get source collection
            source = self.database[source_collection]
            
            # Get all documents from source
            documents = await source.find().to_list(length=None)
            
            if not documents:
                logger.info(f"No documents to migrate from '{source_collection}'")
                return 0

            # Create target collection if it doesn't exist
            await self.create_collection(target_collection)
            
            # Get target collection
            target = self.database[target_collection]
            
            # Insert all documents into target
            result = await target.insert_many(documents)
            
            migrated_count = len(result.inserted_ids)
            logger.info(
                f"Migrated {migrated_count} documents from '{source_collection}' "
                f"to '{target_collection}'"
            )
            
            return migrated_count

        except Exception as e:
            logger.error(f"Failed to migrate collection: {e}")
            raise
