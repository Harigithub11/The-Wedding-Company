"""
Tests for CollectionService.
Tests dynamic MongoDB collection management.
"""

import pytest


class TestCollectionService:
    """Test suite for CollectionService."""
    
    @pytest.mark.asyncio
    async def test_create_collection(
        self,
        collection_service,
        db
    ):
        """Test creating a new collection successfully."""
        collection_name = "org_test_collection"
        
        # Create collection
        result = await collection_service.create_collection(collection_name)
        
        # Assertions
        assert result is True
        
        # Verify collection exists in database
        collections = await db.list_collection_names()
        assert collection_name in collections
    
    @pytest.mark.asyncio
    async def test_collection_exists(
        self,
        collection_service,
        db
    ):
        """Test checking if collection exists returns correct value."""
        collection_name = "org_exists_test"
        
        # Initially should not exist
        exists = await collection_service.collection_exists(collection_name)
        assert exists is False
        
        # Create collection
        await collection_service.create_collection(collection_name)
        
        # Now should exist
        exists = await collection_service.collection_exists(collection_name)
        assert exists is True
    
    @pytest.mark.asyncio
    async def test_delete_collection(
        self,
        collection_service,
        db
    ):
        """Test deleting a collection removes it."""
        collection_name = "org_delete_test"
        
        # Create collection
        await collection_service.create_collection(collection_name)
        
        # Verify it exists
        exists_before = await collection_service.collection_exists(collection_name)
        assert exists_before is True
        
        # Delete collection
        result = await collection_service.delete_collection(collection_name)
        
        # Assertions
        assert result is True
        
        # Verify collection no longer exists
        exists_after = await collection_service.collection_exists(collection_name)
        assert exists_after is False
    
    @pytest.mark.asyncio
    async def test_migrate_collection(
        self,
        collection_service,
        db
    ):
        """Test migrating data between collections moves documents correctly."""
        source_collection = "org_source"
        target_collection = "org_target"
        
        # Create source collection
        await collection_service.create_collection(source_collection)
        
        # Insert test documents into source
        source = db[source_collection]
        test_documents = [
            {"name": "Document 1", "value": 100},
            {"name": "Document 2", "value": 200},
            {"name": "Document 3", "value": 300}
        ]
        await source.insert_many(test_documents)
        
        # Migrate collection
        migrated_count = await collection_service.migrate_collection(
            source_collection=source_collection,
            target_collection=target_collection
        )
        
        # Assertions
        assert migrated_count == 3
        
        # Verify target collection exists
        target_exists = await collection_service.collection_exists(target_collection)
        assert target_exists is True
        
        # Verify target collection has the documents
        target = db[target_collection]
        target_docs = await target.find().to_list(length=None)
        assert len(target_docs) == 3
        
        # Verify document content (excluding _id which may differ)
        target_names = sorted([doc["name"] for doc in target_docs])
        expected_names = sorted([doc["name"] for doc in test_documents])
        assert target_names == expected_names
        
        target_values = sorted([doc["value"] for doc in target_docs])
        expected_values = sorted([doc["value"] for doc in test_documents])
        assert target_values == expected_values
    
    @pytest.mark.asyncio
    async def test_migrate_to_existing_collection_succeeds(
        self,
        collection_service,
        db
    ):
        """Test migration to existing collection appends documents."""
        source_collection = "org_source_exist"
        target_collection = "org_target_exist"
        
        # Create source collection with documents
        await collection_service.create_collection(source_collection)
        source = db[source_collection]
        await source.insert_many([{"data": "source1"}, {"data": "source2"}])
        
        # Create target collection with existing documents
        await collection_service.create_collection(target_collection)
        target = db[target_collection]
        await target.insert_many([{"data": "existing1"}])
        
        # Migrate - should append to target
        migrated_count = await collection_service.migrate_collection(
            source_collection=source_collection,
            target_collection=target_collection
        )
        
        # Assertions
        assert migrated_count == 2
        
        # Verify target has all documents (1 existing + 2 migrated)
        target_docs = await target.find().to_list(length=None)
        assert len(target_docs) == 3
    
    @pytest.mark.asyncio
    async def test_migrate_nonexistent_source_fails(
        self,
        collection_service,
        db
    ):
        """Test migration from non-existent source raises ValueError."""
        source_collection = "org_nonexistent_source"
        target_collection = "org_target"
        
        # Try to migrate from non-existent source - should raise ValueError
        with pytest.raises(ValueError, match="does not exist"):
            await collection_service.migrate_collection(
                source_collection=source_collection,
                target_collection=target_collection
            )
    
    @pytest.mark.asyncio
    async def test_migration_failure_preserves_original(
        self,
        collection_service,
        db
    ):
        """Test that migration failure does not delete original data."""
        source_collection = "org_source_safe"
        
        # Create source collection with documents
        await collection_service.create_collection(source_collection)
        source = db[source_collection]
        test_documents = [
            {"important": "data1"},
            {"important": "data2"}
        ]
        await source.insert_many(test_documents)
        
        # Attempt migration with bad target (will fail during create/insert)
        # We simulate failure by trying to migrate to empty string (invalid name)
        try:
            await collection_service.migrate_collection(
                source_collection=source_collection,
                target_collection=""  # Invalid collection name
            )
        except Exception:
            pass  # Expected to fail
        
        # Verify original data still exists in source
        source_docs = await source.find().to_list(length=None)
        assert len(source_docs) == 2
        assert source_docs[0]["important"] in ["data1", "data2"]
        assert source_docs[1]["important"] in ["data1", "data2"]
    
    @pytest.mark.asyncio
    async def test_create_duplicate_collection_returns_false(
        self,
        collection_service,
        db
    ):
        """Test creating duplicate collection returns False."""
        collection_name = "org_duplicate_test"
        
        # Create collection first time
        result1 = await collection_service.create_collection(collection_name)
        assert result1 is True
        
        # Try to create again - should return False
        result2 = await collection_service.create_collection(collection_name)
        assert result2 is False
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection_returns_false(
        self,
        collection_service,
        db
    ):
        """Test deleting non-existent collection returns False."""
        collection_name = "org_nonexistent"
        
        # Try to delete non-existent collection
        result = await collection_service.delete_collection(collection_name)
        
        # Assertions
        assert result is False
    
    @pytest.mark.asyncio
    async def test_migrate_empty_collection(
        self,
        collection_service,
        db
    ):
        """Test migrating empty collection returns 0."""
        source_collection = "org_empty_source"
        target_collection = "org_empty_target"
        
        # Create empty source collection
        await collection_service.create_collection(source_collection)
        
        # Migrate
        migrated_count = await collection_service.migrate_collection(
            source_collection=source_collection,
            target_collection=target_collection
        )
        
        # Assertions
        assert migrated_count == 0
