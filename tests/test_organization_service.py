"""
Tests for OrganizationService.
Tests business logic for organization CRUD operations.
"""

import pytest
from bson import ObjectId
from app.schemas.organization import OrganizationCreate
from app.models import OrganizationModel


class TestOrganizationService:
    """Test suite for OrganizationService."""
    
    @pytest.mark.asyncio
    async def test_create_organization(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test creating a new organization with correct document structure."""
        # Create admin first
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization data
        org_create = OrganizationCreate(**sample_organization_data)
        
        # Create organization
        org_doc = await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        
        # Assertions
        assert org_doc is not None
        assert "_id" in org_doc
        assert org_doc["organization_name"] == "test_company"
        assert org_doc["collection_name"] == "org_test_company"
        assert str(org_doc["admin_id"]) == admin_id
        assert "created_at" in org_doc
        assert org_doc.get("status") == "active"
    
    @pytest.mark.asyncio
    async def test_organization_exists(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test checking if organization exists returns correct booleans."""
        # Initially should not exist
        exists = await organization_service.organization_exists("test_company")
        assert exists is False
        
        # Create admin
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization
        org_create = OrganizationCreate(**sample_organization_data)
        await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        
        # Now should exist
        exists = await organization_service.organization_exists("test_company")
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_get_organization(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test retrieving an organization by name fetches correctly."""
        # Create admin
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization
        org_create = OrganizationCreate(**sample_organization_data)
        created_org = await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        
        # Get organization
        retrieved_org = await organization_service.get_organization("test_company")
        
        # Assertions
        assert retrieved_org is not None
        assert str(retrieved_org["_id"]) == str(created_org["_id"])
        assert retrieved_org["organization_name"] == "test_company"
        assert retrieved_org["collection_name"] == "org_test_company"
    
    @pytest.mark.asyncio
    async def test_update_organization(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test updating organization name and collection_name."""
        # Create admin
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization
        org_create = OrganizationCreate(**sample_organization_data)
        created_org = await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        org_id = str(created_org["_id"])
        
        # Update organization
        update_result = await organization_model.update(
            organization_id=org_id,
            update_data={
                "organization_name": "updated_company",
                "collection_name": "org_updated_company"
            }
        )
        
        # Assertions
        assert update_result is True
        
        # Verify update
        updated_org = await organization_model.get_by_id(org_id)
        assert updated_org["organization_name"] == "updated_company"
        assert updated_org["collection_name"] == "org_updated_company"
    
    @pytest.mark.asyncio
    async def test_delete_organization(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test deleting organization removes document."""
        # Create admin
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization
        org_create = OrganizationCreate(**sample_organization_data)
        created_org = await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        org_id = str(created_org["_id"])
        
        # Delete organization
        delete_result = await organization_model.delete(org_id)
        
        # Assertions
        assert delete_result is True
        
        # Verify deletion
        deleted_org = await organization_model.get_by_id(org_id)
        assert deleted_org is None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_organization_fails(
        self,
        organization_service,
        admin_service,
        organization_model,
        sample_organization_data
    ):
        """Test creating duplicate organization raises ValueError."""
        # Create admin
        admin_doc = await admin_service.create_admin(
            email=sample_organization_data["email"],
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439011"
        )
        admin_id = str(admin_doc["_id"])
        
        # Create organization
        org_create = OrganizationCreate(**sample_organization_data)
        await organization_service.create_organization(
            organization_data=org_create,
            admin_id=admin_id
        )
        
        # Create second admin with different email
        admin_doc2 = await admin_service.create_admin(
            email="admin2@testcompany.com",
            password=sample_organization_data["password"],
            organization_id="507f1f77bcf86cd799439012"
        )
        admin_id2 = str(admin_doc2["_id"])
        
        # Try to create duplicate organization - should raise ValueError
        with pytest.raises(ValueError, match="already exists"):
            await organization_service.create_organization(
                organization_data=org_create,
                admin_id=admin_id2
            )
