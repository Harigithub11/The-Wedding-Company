"""
Organization service for business logic.
Handles organization CRUD operations and orchestrates between models.
"""

from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models import OrganizationModel, AdminModel
from app.utils.validators import OrganizationNameValidator, InputSanitizer
from app.schemas.organization import OrganizationCreate, OrganizationResponse
import logging

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Service class for organization business logic.
    Coordinates between models and handles validation.
    """

    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize organization service.

        Args:
            database: MongoDB database instance
        """
        self.database = database
        self.org_model = OrganizationModel(database)
        self.admin_model = AdminModel(database)

    async def create_organization(
        self,
        organization_data: OrganizationCreate,
        admin_id: str
    ) -> Dict[str, Any]:
        """
        Create a new organization.

        Args:
            organization_data: Organization creation data
            admin_id: ID of the created admin user

        Returns:
            Organization document

        Raises:
            ValueError: If organization already exists
            Exception: If creation fails
        """
        try:
            # Validate and sanitize organization name
            sanitized_name = OrganizationNameValidator.validate(
                organization_data.organization_name
            )

            # Check if organization already exists
            if await self.org_model.exists(sanitized_name):
                raise ValueError(
                    f"Organization '{sanitized_name}' already exists"
                )

            # Generate collection name
            collection_name = OrganizationNameValidator.to_collection_name(
                sanitized_name
            )

            # Create organization document
            org_doc = await self.org_model.create(
                organization_name=sanitized_name,
                collection_name=collection_name,
                admin_id=admin_id
            )

            logger.info(f"Organization created: {sanitized_name}")
            return org_doc

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to create organization: {e}")
            raise

    async def get_organization(
        self,
        organization_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get organization by name.

        Args:
            organization_name: Organization name to search for

        Returns:
            Organization document if found, None otherwise
        """
        try:
            # Sanitize organization name
            sanitized_name = OrganizationNameValidator.validate(
                organization_name
            )

            # Get organization
            org_doc = await self.org_model.get_by_name(sanitized_name)
            return org_doc

        except Exception as e:
            logger.error(f"Failed to get organization: {e}")
            raise

    async def organization_exists(self, organization_name: str) -> bool:
        """
        Check if organization exists.

        Args:
            organization_name: Organization name to check

        Returns:
            True if exists, False otherwise
        """
        try:
            sanitized_name = OrganizationNameValidator.validate(
                organization_name
            )
            return await self.org_model.exists(sanitized_name)
        except Exception as e:
            logger.error(f"Failed to check organization existence: {e}")
            raise
