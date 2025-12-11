"""
MongoDB database connection manager.
Implements singleton pattern for connection pooling.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton database connection manager.
    Manages MongoDB connection pool and provides database access.
    """

    _instance: Optional["DatabaseManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls) -> "DatabaseManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get MongoDB client instance."""
        if self._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._database

    async def connect(self) -> None:
        """
        Establish connection to MongoDB.
        Creates connection pool and verifies connectivity.
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")

            # Create MongoDB client with connection pooling
            self._client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                maxPoolSize=100,
                minPoolSize=10,
                maxIdleTimeMS=60000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
            )

            # Get database instance
            self._database = self._client[settings.DATABASE_NAME]

            # Verify connection
            await self._client.admin.command("ping")

            logger.info(
                f"Successfully connected to MongoDB database: {settings.DATABASE_NAME}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("Disconnected from MongoDB")

    async def get_collection(self, collection_name: str):
        """
        Get a collection from the database.

        Args:
            collection_name: Name of the collection

        Returns:
            AsyncIOMotorCollection instance
        """
        return self.database[collection_name]


# Create global database manager instance
db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency function to get database instance.
    Can be used with FastAPI Depends.

    Returns:
        AsyncIOMotorDatabase instance
    """
    return db_manager.database
