"""
Tests for AdminService.
Tests admin user management and authentication.
"""

import pytest
from app.models import AdminModel


class TestAdminService:
    """Test suite for AdminService."""
    
    @pytest.mark.asyncio
    async def test_create_admin_stores_hashed_password(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test creating admin stores hashed password, not plain text."""
        admin_doc = await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        
        # Assertions
        assert admin_doc is not None
        assert "_id" in admin_doc
        assert admin_doc["email"] == "admin@example.com"
        assert str(admin_doc["organization_id"]) == sample_admin_data["organization_id"]
        assert "password_hash" in admin_doc
        assert admin_doc["password_hash"] != sample_admin_data["password"]  # Hashed
        assert admin_doc["password_hash"].startswith("$2b$")  # bcrypt hash format
        assert admin_doc["is_active"] is True
        assert "created_at" in admin_doc
    
    @pytest.mark.asyncio
    async def test_get_admin_by_email(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test retrieving admin by email returns correct admin."""
        # Create admin
        created_admin = await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        
        # Get admin by email
        retrieved_admin = await admin_service.get_admin_by_email(sample_admin_data["email"])
        
        # Assertions
        assert retrieved_admin is not None
        assert str(retrieved_admin["_id"]) == str(created_admin["_id"])
        assert retrieved_admin["email"] == sample_admin_data["email"]
        assert retrieved_admin["password_hash"] == created_admin["password_hash"]
    
    @pytest.mark.asyncio
    async def test_authenticate_admin_valid_credentials(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test authenticating admin with valid credentials returns admin."""
        # Create admin
        await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        
        # Authenticate with correct credentials
        authenticated_admin = await admin_service.authenticate_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"]
        )

        # Assertions
        assert authenticated_admin is not None
        assert authenticated_admin["email"] == sample_admin_data["email"]
        # Fetch from DB to verify last_login was updated
        admin_from_db = await admin_model.get_by_email(sample_admin_data["email"])
        assert "last_login" in admin_from_db
        assert admin_from_db["last_login"] is not None

    @pytest.mark.asyncio
    async def test_authenticate_admin_invalid_password(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test authenticating admin with invalid password returns None."""
        # Create admin
        await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        
        # Try to authenticate with wrong password
        authenticated_admin = await admin_service.authenticate_admin(
            email=sample_admin_data["email"],
            password="WrongPassword123!"
        )
        
        # Assertions
        assert authenticated_admin is None
    
    @pytest.mark.asyncio
    async def test_authenticate_admin_nonexistent_email(
        self,
        admin_service,
        admin_model
    ):
        """Test authenticating admin with non-existent email returns None."""
        authenticated_admin = await admin_service.authenticate_admin(
            email="nonexistent@example.com",
            password="SomePassword123!"
        )
        
        # Assertions
        assert authenticated_admin is None
    
    @pytest.mark.asyncio
    async def test_update_credentials(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test updating admin email and password_hash."""
        # Create admin
        created_admin = await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        admin_id = str(created_admin["_id"])
        old_password_hash = created_admin["password_hash"]
        
        # Hash new password
        from app.core.security import PasswordHasher
        password_hasher = PasswordHasher()
        new_password_hash = password_hasher.hash_password("NewPassword456!")
        
        # Update credentials
        await admin_model.update_credentials(
            admin_id=admin_id,
            email="newemail@example.com",
            password_hash=new_password_hash
        )
        
        # Verify update
        updated_admin = await admin_model.get_by_id(admin_id)
        assert updated_admin["email"] == "newemail@example.com"
        assert updated_admin["password_hash"] == new_password_hash
        assert updated_admin["password_hash"] != old_password_hash
    
    @pytest.mark.asyncio
    async def test_delete_by_organization_id(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test deleting all admins by organization_id removes all admins."""
        org_id = "507f1f77bcf86cd799439011"
        
        # Create multiple admins for same organization
        admin1 = await admin_service.create_admin(
            email="admin1@example.com",
            password="Password123!",
            organization_id=org_id
        )
        admin2 = await admin_service.create_admin(
            email="admin2@example.com",
            password="Password123!",
            organization_id=org_id
        )
        admin3 = await admin_service.create_admin(
            email="admin3@example.com",
            password="Password123!",
            organization_id="507f1f77bcf86cd799439013"
        )
        
        # Delete all admins for test_org_123
        deleted_count = await admin_model.delete_by_organization_id(org_id)
        
        # Assertions
        assert deleted_count == 2
        
        # Verify admins deleted
        deleted_admin1 = await admin_model.get_by_id(str(admin1["_id"]))
        deleted_admin2 = await admin_model.get_by_id(str(admin2["_id"]))
        assert deleted_admin1 is None
        assert deleted_admin2 is None
        
        # Verify admin from different org still exists
        remaining_admin = await admin_model.get_by_id(str(admin3["_id"]))
        assert remaining_admin is not None
    
    @pytest.mark.asyncio
    async def test_create_duplicate_admin_fails(
        self,
        admin_service,
        admin_model,
        sample_admin_data
    ):
        """Test creating duplicate admin raises ValueError."""
        # Create first admin
        await admin_service.create_admin(
            email=sample_admin_data["email"],
            password=sample_admin_data["password"],
            organization_id=sample_admin_data["organization_id"]
        )
        
        # Try to create duplicate - should raise ValueError
        with pytest.raises(ValueError, match="already exists"):
            await admin_service.create_admin(
                email=sample_admin_data["email"],
                password="DifferentPassword123!",
                organization_id="different_org_id"
            )
