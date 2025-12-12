"""
Pytest configuration and fixtures for testing.
Provides database connections and service instances for tests.
"""

import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services import OrganizationService, AdminService, CollectionService
from app.models import OrganizationModel, AdminModel


# Test database name (unique to avoid conflicts)
TEST_DB_NAME = "org_management_test"


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.
    Required for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_client():
    """
    Create a MongoDB client for testing.
    Connects to the same MongoDB instance but uses a separate test database.
    """
    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000
    )
    
    # Verify connection
    await client.admin.command("ping")
    
    yield client
    
    # Cleanup: Drop test database and close connection
    await client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture(scope="function")
async def db(db_client):
    """
    Provide a clean test database for each test function.
    Drops all collections after each test to ensure isolation.
    """
    database = db_client[TEST_DB_NAME]
    
    yield database
    
    # Cleanup: Drop all collections after each test
    collections = await database.list_collection_names()
    for collection_name in collections:
        await database.drop_collection(collection_name)


@pytest.fixture(scope="function")
async def organization_service(db):
    """
    Provide an OrganizationService instance for testing.
    Uses the test database.
    """
    service = OrganizationService(db)
    return service


@pytest.fixture(scope="function")
async def admin_service(db):
    """
    Provide an AdminService instance for testing.
    Uses the test database.
    """
    service = AdminService(db)
    return service


@pytest.fixture(scope="function")
async def collection_service(db):
    """
    Provide a CollectionService instance for testing.
    Uses the test database.
    """
    service = CollectionService(db)
    return service


@pytest.fixture(scope="function")
async def organization_model(db):
    """
    Provide an OrganizationModel instance for testing.
    Uses the test database.
    """
    model = OrganizationModel(db)
    await model.create_indexes()
    return model


@pytest.fixture(scope="function")
async def admin_model(db):
    """
    Provide an AdminModel instance for testing.
    Uses the test database.
    """
    model = AdminModel(db)
    await model.create_indexes()
    return model


@pytest.fixture
def sample_organization_data():
    """
    Provide sample organization data for testing.
    """
    return {
        "organization_name": "test_company",
        "email": "admin@testcompany.com",
        "password": "SecurePass123!"
    }


@pytest.fixture
def sample_admin_data():
    """
    Provide sample admin data for testing.
    """
    return {
        "email": "admin@example.com",
        "password": "SecurePassword123!",
        "organization_id": "000000000000000000000001"
    }
