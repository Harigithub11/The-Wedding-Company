"""
Organization router for API endpoints.
Handles organization CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.services import OrganizationService, AdminService, CollectionService
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationCreateResponse,
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationUpdateResponse,
    OrganizationDeleteResponse
)
from app.schemas.admin import AdminLogin
from app.schemas.token import TokenResponse, TokenData
from app.core.security import JWTHandler, PasswordHasher
from app.core.config import settings
from app.middleware import get_current_user
from app.utils.validators import ValidationError, InputSanitizer, OrganizationNameValidator
from app.models import AdminModel, OrganizationModel
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/org", tags=["Organization"])


@router.post(
    "/create",
    response_model=OrganizationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
    description="Create a new organization with an admin user and dynamic collection"
)
async def create_organization(
    organization_data: OrganizationCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new organization.

    This endpoint:
    1. Validates and sanitizes organization name
    2. Checks for duplicate organization names
    3. Hashes admin password
    4. Creates organization document in Master DB
    5. Creates admin user document
    6. Creates dynamic collection for the organization

    Args:
        organization_data: Organization creation data (name, email, password)
        db: MongoDB database instance

    Returns:
        OrganizationCreateResponse with organization metadata and admin_id

    Raises:
        HTTPException 400: Organization already exists
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    organization_id = None
    collection_created = False
    
    try:
        # Initialize services
        org_service = OrganizationService(db)
        admin_service = AdminService(db)
        collection_service = CollectionService(db)
        org_model = OrganizationModel(db)

        # Sanitize inputs
        sanitized_org_name = InputSanitizer.sanitize_string(
            organization_data.organization_name,
            max_length=50
        )
        sanitized_email = InputSanitizer.sanitize_string(
            organization_data.email,
            max_length=100
        )

        # Check if organization already exists
        if await org_service.organization_exists(sanitized_org_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization '{sanitized_org_name}' already exists"
            )

        # Step 1: Create organization FIRST with admin_id=None
        # This prevents race condition where admin references non-existent org
        validated_name = OrganizationNameValidator.validate(sanitized_org_name)
        collection_name = OrganizationNameValidator.to_collection_name(validated_name)
        
        org_doc = await org_model.create(
            organization_name=validated_name,
            collection_name=collection_name,
            admin_id=None  # Will be updated after admin creation
        )
        organization_id = str(org_doc["_id"])
        logger.info(f"Created organization: {validated_name}")

        try:
            # Step 2: Create admin with correct organization_id
            admin_doc = await admin_service.create_admin(
                email=sanitized_email,
                password=organization_data.password,
                organization_id=organization_id
            )
            admin_id = str(admin_doc["_id"])
            logger.info(f"Created admin: {sanitized_email}")

            # Step 3: Update organization with admin_id
            await org_model.update(
                organization_id=organization_id,
                update_data={"admin_id": ObjectId(admin_id)}
            )
            logger.info(f"Updated organization with admin_id")

            # Step 4: Create dynamic collection for this organization
            await collection_service.create_collection(collection_name)
            collection_created = True
            logger.info(f"Created collection: {collection_name}")

            # Prepare response
            org_response = OrganizationResponse(
                id=organization_id,
                organization_name=validated_name,
                collection_name=collection_name,
                admin_email=sanitized_email,
                created_at=org_doc["created_at"],
                updated_at=org_doc.get("updated_at")
            )

            response = OrganizationCreateResponse(
                message="Organization created successfully",
                organization=org_response,
                admin_id=admin_id
            )

            logger.info(
                f"Successfully created organization: {validated_name} "
                f"with admin: {sanitized_email}"
            )

            return response

        except Exception as e:
            # Rollback: Delete organization if admin creation or update failed
            if organization_id:
                try:
                    await org_model.delete(organization_id)
                    logger.info(f"Rolled back: Deleted organization {organization_id}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for organization deletion: {rollback_error}")
            
            # Delete collection if it was created
            if collection_created:
                try:
                    await collection_service.delete_collection(collection_name)
                    logger.info(f"Rolled back: Deleted collection {collection_name}")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for collection deletion: {rollback_error}")
            
            logger.error(f"Rolled back organization creation due to error: {e}")
            raise

    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        logger.warning(f"Value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization. Please try again later."
        )


@router.get(
    "/get",
    response_model=OrganizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get organization by name",
    description="Retrieve organization metadata by organization name"
)
async def get_organization(
    organization_name: str = Query(
        ...,
        min_length=3,
        max_length=50,
        description="Organization name to retrieve"
    ),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get organization by name.

    This endpoint:
    1. Sanitizes organization name
    2. Fetches organization metadata from Master DB
    3. Returns organization details (excluding sensitive data)

    Args:
        organization_name: Organization name to search for
        db: MongoDB database instance

    Returns:
        OrganizationResponse with organization metadata

    Raises:
        HTTPException 404: Organization not found
        HTTPException 422: Validation error
        HTTPException 500: Database error
    """
    try:
        # Initialize service
        org_service = OrganizationService(db)

        # Sanitize organization name
        sanitized_name = InputSanitizer.sanitize_string(
            organization_name,
            max_length=50
        )

        # Get organization
        org_doc = await org_service.get_organization(sanitized_name)

        if not org_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{sanitized_name}' not found"
            )

        # Get admin email
        from app.models import AdminModel
        admin_model = AdminModel(db)
        try:
            admin_doc = await admin_model.get_by_id(str(org_doc["admin_id"]))
            admin_email = admin_doc["email"] if admin_doc else "unknown"
        except Exception as e:
            logger.warning(f"Failed to lookup admin email: {e}")
            admin_email = "unknown"

        # Prepare response (exclude sensitive data)
        response = OrganizationResponse(
            id=str(org_doc["_id"]),
            organization_name=org_doc["organization_name"],
            collection_name=org_doc["collection_name"],
            admin_email=admin_email,
            created_at=org_doc["created_at"],
            updated_at=org_doc.get("updated_at")
        )

        logger.info(f"Retrieved organization: {sanitized_name}")
        return response

    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization. Please try again later."
        )


@router.post(
    "/admin/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin login",
    description="Authenticate admin user and return JWT access token"
)
async def admin_login(
    login_data: AdminLogin,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Admin login endpoint.

    This endpoint:
    1. Validates login credentials (email and password)
    2. Looks up admin by email in Master DB
    3. Verifies password using bcrypt
    4. Generates JWT token with admin_id, organization_id, email, type, and jti

    Args:
        login_data: Admin login credentials (email, password)
        db: MongoDB database instance

    Returns:
        TokenResponse with access_token and token_type

    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 500: Database error
    """
    try:
        # Initialize services
        admin_service = AdminService(db)
        password_hasher = PasswordHasher()
        jwt_handler = JWTHandler()

        # Sanitize email input
        sanitized_email = InputSanitizer.sanitize_string(
            login_data.email,
            max_length=100
        )

        # Authenticate admin (updates last_login automatically)
        admin_doc = await admin_service.authenticate_admin(
            sanitized_email,
            login_data.password
        )

        if not admin_doc:
            logger.warning("Login attempt failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Generate JWT token
        admin_id = str(admin_doc["_id"])
        organization_id = str(admin_doc["organization_id"])
        email = admin_doc["email"]

        access_token = jwt_handler.create_token_for_admin(
            admin_id=admin_id,
            organization_id=organization_id,
            email=email
        )

        # Prepare response
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert minutes to seconds
        )

        logger.info(f"Admin login successful: {email}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process admin login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process login. Please try again later."
        )


@router.put(
    "/update",
    response_model=OrganizationUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update organization",
    description="Update organization name and/or admin credentials with atomic migration"
)
async def update_organization(
    update_data: OrganizationUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update organization with atomic migration.

    This endpoint performs an atomic update operation:
    1. Authenticates user and verifies organization access
    2. Validates new organization name (if provided)
    3. Creates new collection with updated name
    4. Migrates all documents from old collection to new collection
    5. Updates organization metadata in Master DB
    6. Updates admin credentials if provided
    7. Deletes old collection
    8. Rolls back on any failure

    Args:
        update_data: Organization update data (organization_name, email, password)
        db: MongoDB database instance
        current_user: Authenticated user from JWT token

    Returns:
        OrganizationUpdateResponse with updated organization metadata

    Raises:
        HTTPException 400: New organization name already exists
        HTTPException 403: User not authorized for this organization
        HTTPException 404: Organization not found
        HTTPException 409: Migration failure
        HTTPException 500: Database error
    """
    # Track resources for rollback
    new_collection_created = False
    new_collection_name = None
    old_org_data = None
    old_admin_data = None

    try:
        # Initialize services
        org_service = OrganizationService(db)
        admin_service = AdminService(db)
        collection_service = CollectionService(db)
        org_model = OrganizationModel(db)
        admin_model = AdminModel(db)

        # Get current organization
        org_doc = await org_model.get_by_id(current_user.organization_id)
        
        if not org_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Verify user belongs to this organization
        if str(org_doc["_id"]) != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this organization"
            )

        # Store old data for rollback
        old_org_data = org_doc.copy()
        old_collection_name = org_doc["collection_name"]

        # Get current admin data
        admin_doc = await admin_model.get_by_id(current_user.admin_id)
        if admin_doc:
            old_admin_data = admin_doc.copy()

        # Check if organization name is being updated
        if update_data.organization_name:
            # Sanitize and validate new organization name
            sanitized_new_name = InputSanitizer.sanitize_string(
                update_data.organization_name,
                max_length=50
            )
            validated_new_name = OrganizationNameValidator.validate(sanitized_new_name)

            # Check if new name is different from current
            if validated_new_name != org_doc["organization_name"]:
                # Generate new collection name
                new_collection_name = OrganizationNameValidator.to_collection_name(
                    validated_new_name
                )

                try:
                    # Step 1: Create new collection
                    await collection_service.create_collection(new_collection_name)
                    new_collection_created = True
                    logger.info(f"Created new collection: {new_collection_name}")

                    # Step 2: Migrate all documents from old to new collection
                    migrated_count = await collection_service.migrate_collection(
                        source_collection=old_collection_name,
                        target_collection=new_collection_name
                    )
                    logger.info(f"Migrated {migrated_count} documents to new collection")

                    # Step 3: Update organization metadata
                    update_fields = {
                        "organization_name": validated_new_name,
                        "collection_name": new_collection_name,
                        "updated_at": datetime.utcnow()
                    }
                    
                    try:
                        update_result = await org_model.update(
                            organization_id=current_user.organization_id,
                            update_data=update_fields
                        )
                        
                        # Step 4: Verify update succeeded before deleting old collection
                        if update_result:
                            logger.info(f"Updated organization metadata")
                            await collection_service.delete_collection(old_collection_name)
                            logger.info(f"Deleted old collection: {old_collection_name}")
                        else:
                            logger.error("Metadata update failed - keeping old collection")
                            raise Exception("Failed to update organization metadata")
                    
                    except Exception as dup_error:
                        # Handle duplicate key error specifically
                        if "duplicate key" in str(dup_error).lower():
                            logger.warning(f"Duplicate organization name: {validated_new_name}")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Organization name '{validated_new_name}' already exists"
                            )
                        raise

                except Exception as e:
                    # CRITICAL ROLLBACK: Ensure database is in consistent state
                    logger.error(f"Migration failed: {e}. Starting rollback...")
                    
                    # Step 1: Delete new collection if created
                    if new_collection_created and new_collection_name:
                        try:
                            await collection_service.delete_collection(new_collection_name)
                            logger.info(f"Rollback: Deleted new collection {new_collection_name}")
                        except Exception as rollback_error:
                            logger.error(f"Rollback failed: Could not delete new collection: {rollback_error}")

                    # Step 2: Restore old organization metadata
                    if old_org_data:
                        try:
                            await org_model.update(
                                organization_id=current_user.organization_id,
                                update_data={
                                    "organization_name": old_org_data["organization_name"],
                                    "collection_name": old_org_data["collection_name"],
                                    "updated_at": old_org_data.get("updated_at")
                                }
                            )
                            logger.info("Rollback: Restored old organization metadata")
                        except Exception as rollback_error:
                            logger.error(f"Rollback failed: Could not restore organization metadata: {rollback_error}")

                    # Step 3: Ensure old collection exists (recreate if missing)
                    try:
                        old_collection_exists = await collection_service.collection_exists(old_collection_name)
                        if not old_collection_exists:
                            # Recreate old collection if it was deleted
                            await collection_service.create_collection(old_collection_name)
                            logger.info(f"Rollback: Recreated old collection {old_collection_name}")
                        else:
                            logger.info(f"Rollback: Old collection {old_collection_name} still exists")
                    except Exception as rollback_error:
                        logger.error(f"Rollback failed: Could not ensure old collection exists: {rollback_error}")

                    # Log rollback completion
                    logger.error(f"Rollback completed. Migration failed with error: {e}")
                    
                    # Raise HTTP 409 Conflict
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Failed to migrate organization data: {str(e)}"
                    )

        # Update admin credentials if provided
        if update_data.email or update_data.password:
            try:
                new_email = None
                new_password_hash = None

                if update_data.email:
                    new_email = InputSanitizer.sanitize_string(
                        update_data.email,
                        max_length=100
                    )

                if update_data.password:
                    password_hasher = PasswordHasher()
                    new_password_hash = password_hasher.hash_password(update_data.password)

                # Update admin credentials
                await admin_model.update_credentials(
                    admin_id=current_user.admin_id,
                    email=new_email,
                    password_hash=new_password_hash
                )
                logger.info(f"Updated admin credentials for {current_user.admin_id}")

            except Exception as e:
                logger.critical(f"Failed to update admin credentials: {e}. Starting rollback...")
                
                # CRITICAL ROLLBACK: Restore organization state
                try:
                    # Restore old organization metadata
                    if old_org_data:
                        await org_model.update(
                            organization_id=current_user.organization_id,
                            update_data={
                                "organization_name": old_org_data["organization_name"],
                                "collection_name": old_org_data["collection_name"],
                                "updated_at": old_org_data.get("updated_at")
                            }
                        )
                        logger.info("Rollback: Restored old organization metadata")
                    
                    # Delete new collection if it exists
                    if new_collection_created and new_collection_name:
                        await collection_service.delete_collection(new_collection_name)
                        logger.info(f"Rollback: Deleted new collection {new_collection_name}")
                    
                    # Recreate old collection if missing
                    old_collection_exists = await collection_service.collection_exists(old_collection_name)
                    if not old_collection_exists:
                        await collection_service.create_collection(old_collection_name)
                        logger.info(f"Rollback: Recreated old collection {old_collection_name}")
                    
                    logger.critical("Rollback completed after credential update failure")
                
                except Exception as rollback_error:
                    logger.critical(f"Rollback failed after credential update: {rollback_error}")
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update admin credentials"
                )

        # Get updated organization data
        updated_org_doc = await org_model.get_by_id(current_user.organization_id)
        updated_admin_doc = await admin_model.get_by_id(current_user.admin_id)

        # Prepare response
        org_response = OrganizationResponse(
            id=str(updated_org_doc["_id"]),
            organization_name=updated_org_doc["organization_name"],
            collection_name=updated_org_doc["collection_name"],
            admin_email=updated_admin_doc["email"] if updated_admin_doc else old_admin_data.get("email", "unknown"),
            created_at=updated_org_doc["created_at"],
            updated_at=updated_org_doc.get("updated_at")
        )

        response = OrganizationUpdateResponse(
            message="Organization updated successfully",
            organization=org_response
        )

        logger.info(f"Organization update completed: {updated_org_doc['organization_name']}")
        return response

    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization. Please try again later."
        )


@router.delete(
    "/delete",
    response_model=OrganizationDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete organization",
    description="Delete organization and all associated data (cascade delete)"
)
async def delete_organization(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete organization with cascade deletion.

    This endpoint performs cascade deletion:
    1. Authenticates user and verifies organization access
    2. Deletes organization's dynamic collection
    3. Deletes all admin users associated with the organization
    4. Deletes organization document from Master DB
    5. Logs deletion for audit trail

    Args:
        db: MongoDB database instance
        current_user: Authenticated user from JWT token

    Returns:
        OrganizationDeleteResponse with success message

    Raises:
        HTTPException 403: User not authorized for this organization
        HTTPException 404: Organization not found
        HTTPException 500: Database error
    """
    try:
        # Initialize services
        collection_service = CollectionService(db)
        org_model = OrganizationModel(db)
        admin_model = AdminModel(db)

        # Get organization
        org_doc = await org_model.get_by_id(current_user.organization_id)
        
        if not org_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )

        # Verify user belongs to this organization
        if str(org_doc["_id"]) != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this organization"
            )

        organization_name = org_doc["organization_name"]
        collection_name = org_doc["collection_name"]

        # Step 1: Delete organization's dynamic collection
        try:
            await collection_service.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")
            # Continue with deletion even if collection doesn't exist

        # Step 2: Delete all admins associated with this organization
        try:
            deleted_admin_count = await admin_model.delete_by_organization_id(
                current_user.organization_id
            )
            logger.info(f"Deleted {deleted_admin_count} admin(s) for organization {organization_name}")
        except Exception as e:
            logger.error(f"Failed to delete admins: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete admin users"
            )

        # Step 3: Delete organization document
        try:
            deleted = await org_model.delete(current_user.organization_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            logger.info(f"Deleted organization: {organization_name}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete organization document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete organization"
            )

        # Prepare response
        response = OrganizationDeleteResponse(
            message=f"Organization '{organization_name}' deleted successfully"
        )

        logger.info(f"Organization deletion completed: {organization_name}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete organization. Please try again later."
        )
