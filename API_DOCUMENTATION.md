# Organization Management Service - API Documentation

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Security Features](#security-features)
6. [Data Models](#data-models)
7. [Atomicity & Rollback](#atomicity--rollback)
8. [Example Workflows](#example-workflows)
9. [Error Handling](#error-handling)

---

## Overview

The **Organization Management Service** is a multi-tenant FastAPI application that provides secure organization and admin user management with JWT-based authentication. Each organization gets its own isolated MongoDB collection for data storage, ensuring complete data separation between tenants.

### Key Features

- **Multi-tenant Architecture**: Each organization has a dedicated MongoDB collection
- **JWT Authentication**: Secure token-based authentication with bcrypt password hashing
- **Atomic Operations**: Organization updates with automatic rollback on failures
- **Input Validation**: Comprehensive input sanitization and validation
- **Cascade Deletion**: Safe deletion with cleanup of all related resources
- **Security Hardening**: Protection against algorithm confusion, timing attacks, and injection vulnerabilities

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Routers    │─────▶│   Services   │─────▶│  Models   │ │
│  │ (Endpoints)  │      │  (Business   │      │  (CRUD)   │ │
│  │              │      │   Logic)     │      │           │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│         ▼                      ▼                     ▼       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MongoDB Database Layer                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │  │
│  │  │organizations│  │   admins    │  │ org_<name>   │ │  │
│  │  │ (Master DB) │  │ (Master DB) │  │  (Dynamic)   │ │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Layers

1. **Routers**: HTTP endpoint definitions (`organization_router.py`)
2. **Services**: Business logic layer (`OrganizationService`, `AdminService`, `CollectionService`)
3. **Models**: Database CRUD operations (`OrganizationModel`, `AdminModel`)
4. **Schemas**: Request/response validation (`Pydantic` models)
5. **Middleware**: Authentication and security headers
6. **Utilities**: Validators and sanitizers

---

## Authentication

### JWT Token Structure

All authenticated endpoints require a JWT Bearer token in the `Authorization` header.

**Token Claims:**
```json
{
  "admin_id": "507f1f77bcf86cd799439012",
  "organization_id": "507f1f77bcf86cd799439011",
  "email": "admin@example.com",
  "type": "admin",
  "jti": "unique-token-id",
  "exp": 1702474800,
  "iat": 1702388400
}
```

**Security Features:**
- Algorithm: HS256 (hardcoded to prevent algorithm confusion attacks)
- Expiration: 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- JTI claim: Unique token ID for replay prevention
- IAT validation: 60-second clock skew tolerance

**Header Format:**
```
Authorization: Bearer <token>
```

---

## API Endpoints

### 1. Create Organization

**Endpoint:** `POST /org/create`  
**Authentication:** None (public endpoint)  
**Description:** Creates a new organization with an admin user and dedicated collection

#### Request Body

```json
{
  "organization_name": "acme_corp",
  "email": "admin@acmecorp.com",
  "password": "SecurePass123!"
}
```

**Schema:**
- `organization_name` (string, required): 3-50 characters, alphanumeric + underscores, lowercase
- `email` (string, required): Valid email address
- `password` (string, required): 8-100 characters

#### Response (201 Created)

```json
{
  "message": "Organization created successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "acme_corp",
    "collection_name": "org_acme_corp",
    "admin_email": "admin@acmecorp.com",
    "created_at": "2025-12-12T10:30:00.000Z",
    "updated_at": "2025-12-12T10:30:00.000Z"
  },
  "admin_id": "507f1f77bcf86cd799439012"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 201  | Organization created successfully |
| 400  | Organization already exists |
| 422  | Validation error (invalid input) |
| 500  | Internal server error |

#### Backend Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant OrgService
    participant AdminService
    participant CollectionService
    participant MongoDB

    Client->>Router: POST /org/create
    Router->>Router: Sanitize & Validate inputs
    Router->>OrgService: Check if org exists
    OrgService->>MongoDB: Query organizations
    MongoDB-->>OrgService: Not found
    Router->>MongoDB: Create organization (admin_id=null)
    MongoDB-->>Router: Organization created
    Router->>AdminService: Create admin user
    AdminService->>AdminService: Hash password (bcrypt)
    AdminService->>MongoDB: Insert admin document
    MongoDB-->>AdminService: Admin created
    Router->>MongoDB: Update org with admin_id
    MongoDB-->>Router: Updated
    Router->>CollectionService: Create dynamic collection
    CollectionService->>MongoDB: Create org_<name> collection
    MongoDB-->>CollectionService: Collection created
    Router-->>Client: 201 Created + Organization data
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/org/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corp",
    "email": "admin@acmecorp.com",
    "password": "SecurePass123!"
  }'
```

#### Rollback Behavior

If any step fails after organization creation:
1. Delete the organization document
2. Delete the dynamic collection (if created)
3. Return error to client

---

### 2. Get Organization

**Endpoint:** `GET /org/get`  
**Authentication:** None  
**Description:** Retrieve organization metadata by organization name

#### Query Parameters

- `organization_name` (string, required): Organization name to retrieve (3-50 characters)

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "organization_name": "acme_corp",
  "collection_name": "org_acme_corp",
  "admin_email": "admin@acmecorp.com",
  "created_at": "2025-12-12T10:30:00.000Z",
  "updated_at": "2025-12-12T10:35:00.000Z"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200  | Organization found |
| 404  | Organization not found |
| 422  | Validation error |
| 500  | Internal server error |

#### cURL Example

```bash
curl -X GET "http://localhost:8000/org/get?organization_name=acme_corp"
```

#### Error Handling

- If admin lookup fails, `admin_email` is set to `"unknown"` (does not throw 500)
- Logs warning but continues with response

---

### 3. Admin Login

**Endpoint:** `POST /org/admin/login`  
**Authentication:** None  
**Description:** Authenticate admin user and receive JWT access token

#### Request Body

```json
{
  "email": "admin@acmecorp.com",
  "password": "SecurePass123!"
}
```

**Schema:**
- `email` (string, required): Valid email address
- `password` (string, required): Admin password

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Fields:**
- `access_token`: JWT token string
- `token_type`: Always "bearer"
- `expires_in`: Token lifetime in seconds (86400 = 24 hours)

#### Status Codes

| Code | Description |
|------|-------------|
| 200  | Login successful |
| 401  | Invalid credentials |
| 500  | Internal server error |

#### Backend Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant AdminService
    participant PasswordHasher
    participant JWTHandler
    participant MongoDB

    Client->>Router: POST /org/admin/login
    Router->>AdminService: authenticate_admin(email, password)
    AdminService->>MongoDB: Find admin by email
    MongoDB-->>AdminService: Admin document
    AdminService->>PasswordHasher: verify_password()
    PasswordHasher-->>AdminService: Valid
    AdminService->>MongoDB: Update last_login timestamp
    MongoDB-->>AdminService: Updated
    AdminService-->>Router: Admin document
    Router->>JWTHandler: create_token_for_admin()
    JWTHandler-->>Router: JWT token
    Router-->>Client: 200 OK + Token
```

#### Security Features

- Generic error message: "Invalid credentials" (no email enumeration)
- Single log message: "Login attempt failed" (no leak of email/password validity)
- Automatic `last_login` timestamp update
- Constant-time password verification (timing attack prevention)

#### cURL Example

```bash
curl -X POST http://localhost:8000/org/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acmecorp.com",
    "password": "SecurePass123!"
  }'
```

---

### 4. Update Organization

**Endpoint:** `PUT /org/update`  
**Authentication:** Required (JWT Bearer Token)  
**Description:** Update organization name and/or admin credentials with atomic migration

#### Request Headers

```
Authorization: Bearer <token>
```

#### Request Body

```json
{
  "organization_name": "acme_corporation",
  "email": "new.admin@acmecorp.com",
  "password": "NewSecurePass456!"
}
```

**Schema:**
- `organization_name` (string, optional): New organization name (3-50 characters)
- `email` (string, optional): New admin email
- `password` (string, optional): New admin password (8-100 characters)

**Note:** At least one field must be provided.

#### Response (200 OK)

```json
{
  "message": "Organization updated successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "acme_corporation",
    "collection_name": "org_acme_corporation",
    "admin_email": "new.admin@acmecorp.com",
    "created_at": "2025-12-12T10:30:00.000Z",
    "updated_at": "2025-12-12T11:45:00.000Z"
  }
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200  | Update successful |
| 400  | Organization name already exists (duplicate) |
| 401  | Invalid or missing token |
| 403  | User not authorized for this organization |
| 404  | Organization not found |
| 409  | Migration conflict (rollback triggered) |
| 422  | Validation error |
| 500  | Internal server error |

#### Backend Flow (Name Change)

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Middleware
    participant CollectionService
    participant OrgModel
    participant MongoDB

    Client->>Router: PUT /org/update + Token
    Router->>Middleware: Validate JWT token
    Middleware-->>Router: TokenData (admin_id, org_id)
    Router->>MongoDB: Get current organization
    Router->>Router: Verify org access
    Router->>CollectionService: Create new collection
    CollectionService->>MongoDB: Create org_<new_name>
    MongoDB-->>CollectionService: Created
    Router->>CollectionService: Migrate documents
    CollectionService->>MongoDB: Copy all documents
    MongoDB-->>CollectionService: Migration complete
    Router->>OrgModel: Update metadata
    OrgModel->>MongoDB: Update org document
    MongoDB-->>OrgModel: Success (boolean true)
    Router->>Router: Verify update success
    Router->>CollectionService: Delete old collection
    CollectionService->>MongoDB: Drop org_<old_name>
    MongoDB-->>CollectionService: Deleted
    Router-->>Client: 200 OK + Updated org
```

#### Rollback Behavior

If migration or credential update fails:
1. Delete new collection (if created)
2. Restore old organization metadata
3. Recreate old collection (if accidentally deleted)
4. Log critical error
5. Return HTTP 409 or 500

#### cURL Example

```bash
# Update organization name only
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corporation"
  }'

# Update admin credentials only
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "new.admin@acmecorp.com",
    "password": "NewSecurePass456!"
  }'

# Update both
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corporation",
    "email": "new.admin@acmecorp.com",
    "password": "NewSecurePass456!"
  }'
```

---

### 5. Delete Organization

**Endpoint:** `DELETE /org/delete`  
**Authentication:** Required (JWT Bearer Token)  
**Description:** Delete organization and all associated data (cascade delete)

#### Request Headers

```
Authorization: Bearer <token>
```

#### Request Body

None

#### Response (200 OK)

```json
{
  "message": "Organization 'acme_corp' deleted successfully"
}
```

#### Status Codes

| Code | Description |
|------|-------------|
| 200  | Organization deleted successfully |
| 401  | Invalid or missing token |
| 403  | User not authorized for this organization |
| 404  | Organization not found |
| 500  | Internal server error |

#### Backend Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Middleware
    participant CollectionService
    participant OrgModel
    participant AdminModel
    participant MongoDB

    Client->>Router: DELETE /org/delete + Token
    Router->>Middleware: Validate JWT token
    Middleware-->>Router: TokenData
    Router->>MongoDB: Get organization
    Router->>Router: Verify org access
    Router->>CollectionService: Delete org collection
    CollectionService->>MongoDB: Drop org_<name>
    MongoDB-->>CollectionService: Deleted
    Router->>AdminModel: Delete all org admins
    AdminModel->>MongoDB: Delete by organization_id
    MongoDB-->>AdminModel: Deleted count
    Router->>OrgModel: Delete organization doc
    OrgModel->>MongoDB: Delete org document
    MongoDB-->>OrgModel: Deleted
    Router-->>Client: 200 OK + Success message
```

#### Cascade Deletion Order

1. **Dynamic collection**: Delete `org_<name>` collection (continues even if not found)
2. **Admin users**: Delete all admins associated with `organization_id`
3. **Organization document**: Delete organization from master DB

#### cURL Example

```bash
curl -X DELETE http://localhost:8000/org/delete \
  -H "Authorization: Bearer <token>"
```

---

## Security Features

### 1. Password Security

- **Algorithm**: bcrypt with 13 rounds (explicitly configured)
- **Hashing**: All passwords hashed before storage
- **Verification**: Constant-time comparison to prevent timing attacks
- **Minimum Length**: 8 characters
- **Maximum Length**: 100 characters

**Implementation:**
```python
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=13
)
```

### 2. JWT Security

**Protections Implemented:**

| Vulnerability | Protection |
|---------------|------------|
| Algorithm Confusion | Hardcoded "HS256", no `settings.ALGORITHM` |
| Token Replay | JTI (JWT ID) claim with UUID |
| Future-dated Tokens | IAT validation with 60s clock skew |
| Error Leakage | Generic "JWT decode failed" message |
| None Algorithm | Not in allowed algorithms list |

**Secret Key Requirements:**
- Minimum 32 characters (enforced via Pydantic validator)
- Application fails to start with weak keys

### 3. Input Validation & Sanitization

**Organization Name:**
- Strip whitespace
- Convert to lowercase
- Replace spaces with underscores
- Allow only: `[a-z0-9_]`
- Length: 3-50 characters

**Email:**
- EmailStr validation (Pydantic)
- RFC 5322 compliance
- Maximum 100 characters after sanitization

**Password:**
- Minimum 8 characters
- Maximum 100 characters
- No character restrictions (allows complexity)

**Implementation:**
```python
# Sanitization
sanitized = InputSanitizer.sanitize_string(input, max_length=50)

# Validation
validated_name = OrganizationNameValidator.validate(sanitized)
```

### 4. NoSQL Injection Protection

**Techniques:**
1. **Pydantic Validation**: All inputs validated before DB queries
2. **Type Enforcement**: MongoDB ObjectId conversion with validation
3. **Parameterized Queries**: No string concatenation in queries
4. **Input Sanitization**: Remove special characters before processing

**Example:**
```python
# Safe ObjectId conversion
organization_id = ObjectId(sanitized_id)  # Throws error if invalid

# Safe query
await collection.find_one({"_id": organization_id})
```

### 5. Security Headers

All responses include these headers (via `SecurityHeadersMiddleware`):

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### 6. Rate Limiting

- **Configuration**: 100 requests per 60 seconds (in-memory)
- **Recommendation**: Use Redis-backed rate limiting for production

### 7. CORS Configuration

- **Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Default**: `http://localhost:3000,http://localhost:8000`
- **Credentials**: Allowed
- **Methods**: All (`*`)
- **Headers**: All (`*`)

### 8. Logging & Privacy

**PII Protection:**
- Admin emails NOT logged in success paths
- Masked admin_id: `admin_id[:8]***`
- Generic error messages for authentication failures

**Log Levels:**
- `INFO`: Successful operations
- `WARNING`: Validation errors, failed lookups
- `ERROR`: Database errors
- `CRITICAL`: Rollback operations

---

## Data Models

### Organization Model

**Collection:** `organizations` (Master DB)

**Schema:**
```json
{
  "_id": "ObjectId",
  "organization_name": "string (unique, lowercase, alphanumeric+underscore)",
  "collection_name": "string (org_<name>)",
  "admin_id": "ObjectId (reference to admins._id, can be null)",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)",
  "status": "string (default: 'active')"
}
```

**Indexes:**
- `organization_name`: Unique index
- `admin_id`: Regular index

**CRUD Operations:**
- `create()`: Insert new organization
- `get_by_name()`: Find by organization name
- `get_by_id()`: Find by ObjectId
- `get_by_admin_id()`: Find by admin ID
- `update()`: Update fields and set `updated_at`
- `delete()`: Remove organization document
- `exists()`: Check if organization name exists
- `list_all()`: Get all organizations (paginated)
- `count()`: Count total organizations

---

### Admin Model

**Collection:** `admins` (Master DB)

**Schema:**
```json
{
  "_id": "ObjectId",
  "email": "string (unique, validated email)",
  "password_hash": "string (bcrypt hash)",
  "organization_id": "ObjectId (reference to organizations._id)",
  "is_active": "boolean (default: true)",
  "created_at": "datetime (UTC)",
  "updated_at": "datetime (UTC)",
  "last_login": "datetime (UTC, nullable)"
}
```

**Indexes:**
- `email`: Unique index
- `organization_id`: Regular index

**CRUD Operations:**
- `create()`: Insert new admin with hashed password
- `get_by_email()`: Find by email address
- `get_by_id()`: Find by ObjectId
- `get_by_organization_id()`: Find by organization ID
- `update()`: Update admin fields
- `update_credentials()`: Update email and/or password hash
- `update_last_login()`: Set last_login to current UTC time
- `delete()`: Remove admin document
- `delete_by_organization_id()`: Remove all admins for an organization
- `exists()`: Check if admin email exists

---

### Dynamic Collections

**Naming Convention:** `org_<organization_name>`

**Purpose:** Isolated data storage for each organization

**Schema:** Flexible (application-defined)

**Lifecycle:**
- **Created**: During organization creation (`POST /org/create`)
- **Renamed**: During organization update (`PUT /org/update`) via migration
- **Deleted**: During organization deletion (`DELETE /org/delete`)

**Management Operations:**
- `create_collection()`: Create new collection with indexes
- `delete_collection()`: Drop collection
- `migrate_collection()`: Copy all documents from source to target
- `collection_exists()`: Check if collection exists
- `count_documents()`: Count documents in collection

---

## Atomicity & Rollback

### Organization Creation Rollback

**Scenario:** Admin creation or collection creation fails after organization is created.

**Rollback Steps:**
1. Delete organization document from `organizations` collection
2. Delete dynamic collection `org_<name>` (if created)
3. Log rollback actions
4. Return error to client

**Code Flow:**
```python
try:
    org_doc = create_organization()
    admin_doc = create_admin()
    update_organization_with_admin_id()
    create_dynamic_collection()
except Exception as e:
    # Rollback
    delete_organization(org_id)
    delete_collection(collection_name)
    raise
```

---

### Organization Update Rollback

**Scenario:** Migration fails or credential update fails after collection changes.

**Rollback Steps:**

#### Migration Failure:
1. Delete new collection `org_<new_name>`
2. Restore old organization metadata (name, collection_name, updated_at)
3. Ensure old collection `org_<old_name>` exists (recreate if missing)
4. Log critical error
5. Return HTTP 409 Conflict

#### Credential Update Failure:
1. Restore old organization metadata
2. Delete new collection (if created)
3. Recreate old collection (if missing)
4. Log critical error
5. Return HTTP 500 Internal Server Error

**Code Flow:**
```python
try:
    create_new_collection()
    migrate_documents()
    update_metadata()
    if metadata_update_success:
        delete_old_collection()
    else:
        raise Exception("Metadata update failed")
except Exception as e:
    # Rollback
    delete_new_collection()
    restore_old_metadata()
    ensure_old_collection_exists()
    raise
```

**Metadata Update Verification:**
```python
update_result = await org_model.update(...)
if update_result:  # Boolean check
    delete_old_collection()
else:
    raise Exception("Metadata update failed")
```

---

### Cascade Deletion

**Scenario:** Organization deletion must clean up all related resources.

**Deletion Order:**
1. **Dynamic Collection**: Drop `org_<name>` (continues even if not found)
2. **Admin Users**: Delete all admins where `organization_id` matches
3. **Organization Document**: Delete from `organizations` collection

**Code Flow:**
```python
try:
    delete_collection(collection_name)  # Step 1
except Exception:
    log_warning("Collection may not exist")

delete_admins_by_org_id(org_id)  # Step 2 (must succeed)
delete_organization(org_id)      # Step 3 (must succeed)
```

**No Rollback:** Deletion is permanent and cannot be undone.

---

## Example Workflows

### Workflow 1: Create Organization

```bash
# Step 1: Create organization
curl -X POST http://localhost:8000/org/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "tech_startup",
    "email": "founder@techstartup.com",
    "password": "SecurePassword123!"
  }'

# Response:
# {
#   "message": "Organization created successfully",
#   "organization": {
#     "id": "507f1f77bcf86cd799439011",
#     "organization_name": "tech_startup",
#     "collection_name": "org_tech_startup",
#     "admin_email": "founder@techstartup.com",
#     "created_at": "2025-12-12T10:00:00Z",
#     "updated_at": "2025-12-12T10:00:00Z"
#   },
#   "admin_id": "507f1f77bcf86cd799439012"
# }

# What happened:
# 1. Organization "tech_startup" created in organizations collection
# 2. Admin user created with email "founder@techstartup.com"
# 3. Password hashed with bcrypt (13 rounds)
# 4. Dynamic collection "org_tech_startup" created
# 5. Organization document updated with admin_id
```

---

### Workflow 2: Login and Get Token

```bash
# Step 1: Login
curl -X POST http://localhost:8000/org/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "founder@techstartup.com",
    "password": "SecurePassword123!"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZG1pbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMiIsIm9yZ2FuaXphdGlvbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMSIsImVtYWlsIjoiZm91bmRlckB0ZWNoc3RhcnR1cC5jb20iLCJ0eXBlIjoiYWRtaW4iLCJqdGkiOiI4ZjFiNWZhNC05YzQ0LTRlZGItYjZhNi1jZWQwNGNhNmJlYTQiLCJleHAiOjE3MDI0NzQ4MDAsImlhdCI6MTcwMjM4ODQwMH0.signature",
#   "token_type": "bearer",
#   "expires_in": 86400
# }

# Save token for subsequent requests
TOKEN="<access_token_from_response>"

# Step 2: Use token in authenticated requests
curl -X GET "http://localhost:8000/org/get?organization_name=tech_startup" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Workflow 3: Update Organization Name (Migration)

```bash
# Prerequisites: Have valid JWT token

# Step 1: Update organization name
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "tech_startup_inc"
  }'

# Response:
# {
#   "message": "Organization updated successfully",
#   "organization": {
#     "id": "507f1f77bcf86cd799439011",
#     "organization_name": "tech_startup_inc",
#     "collection_name": "org_tech_startup_inc",
#     "admin_email": "founder@techstartup.com",
#     "created_at": "2025-12-12T10:00:00Z",
#     "updated_at": "2025-12-12T11:00:00Z"
#   }
# }

# What happened:
# 1. New collection "org_tech_startup_inc" created
# 2. All documents migrated from "org_tech_startup" to "org_tech_startup_inc"
# 3. Organization metadata updated (name, collection_name, updated_at)
# 4. Metadata update verified (boolean check)
# 5. Old collection "org_tech_startup" deleted
# 6. No downtime for data access

# If any step failed:
# - New collection deleted
# - Old metadata restored
# - Old collection recreated (if missing)
# - HTTP 409 returned with error message
```

---

### Workflow 4: Update Admin Credentials

```bash
# Prerequisites: Have valid JWT token

# Step 1: Update email and password
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@techstartup.com",
    "password": "NewSecurePass456!"
  }'

# Response:
# {
#   "message": "Organization updated successfully",
#   "organization": {
#     "id": "507f1f77bcf86cd799439011",
#     "organization_name": "tech_startup_inc",
#     "collection_name": "org_tech_startup_inc",
#     "admin_email": "ceo@techstartup.com",
#     "created_at": "2025-12-12T10:00:00Z",
#     "updated_at": "2025-12-12T11:30:00Z"
#   }
# }

# Important: Old token is still valid until expiration
# Re-login with new credentials to get fresh token

# Step 2: Login with new credentials
curl -X POST http://localhost:8000/org/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@techstartup.com",
    "password": "NewSecurePass456!"
  }'
```

---

### Workflow 5: Delete Organization

```bash
# Prerequisites: Have valid JWT token

# Step 1: Delete organization
curl -X DELETE http://localhost:8000/org/delete \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "message": "Organization 'tech_startup_inc' deleted successfully"
# }

# What happened (in order):
# 1. Dynamic collection "org_tech_startup_inc" dropped
# 2. All admin users with organization_id deleted from admins collection
# 3. Organization document deleted from organizations collection
# 4. All data permanently removed (no recovery)

# Step 2: Token is now invalid (organization no longer exists)
curl -X GET "http://localhost:8000/org/get?organization_name=tech_startup_inc"
# Returns: 404 Not Found
```

---

## Error Handling

### Error Response Format

All errors return consistent JSON structure:

```json
{
  "detail": "Error message description"
}
```

### Common Error Scenarios

#### 1. Authentication Errors

**Invalid Token:**
```json
HTTP 401 Unauthorized
{
  "detail": "Could not validate credentials"
}
```

**Missing Token:**
```json
HTTP 401 Unauthorized
{
  "detail": "Not authenticated"
}
```

**Expired Token:**
```json
HTTP 401 Unauthorized
{
  "detail": "Could not validate credentials"
}
```

#### 2. Authorization Errors

**Wrong Organization:**
```json
HTTP 403 Forbidden
{
  "detail": "You do not have access to this organization"
}
```

**Inactive Account:**
```json
HTTP 403 Forbidden
{
  "detail": "User account is inactive"
}
```

#### 3. Validation Errors

**Invalid Organization Name:**
```json
HTTP 422 Unprocessable Entity
{
  "detail": "Organization name must be 3-50 characters and contain only lowercase letters, numbers, and underscores"
}
```

**Invalid Email:**
```json
HTTP 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

**Password Too Short:**
```json
HTTP 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters"
    }
  ]
}
```

#### 4. Conflict Errors

**Duplicate Organization:**
```json
HTTP 400 Bad Request
{
  "detail": "Organization 'acme_corp' already exists"
}
```

**Duplicate Email:**
```json
HTTP 400 Bad Request
{
  "detail": "Admin with email 'admin@example.com' already exists"
}
```

**Migration Conflict:**
```json
HTTP 409 Conflict
{
  "detail": "Failed to migrate organization data: [error details]"
}
```

#### 5. Not Found Errors

**Organization Not Found:**
```json
HTTP 404 Not Found
{
  "detail": "Organization 'nonexistent' not found"
}
```

**Admin Not Found:**
```json
HTTP 403 Forbidden
{
  "detail": "User account not found"
}
```

#### 6. Server Errors

**Database Connection:**
```json
HTTP 500 Internal Server Error
{
  "detail": "Failed to create organization. Please try again later."
}
```

**Generic Error:**
```json
HTTP 500 Internal Server Error
{
  "detail": "Failed to process login. Please try again later."
}
```

### Error Logging

**Client-Facing Messages:**
- Generic and safe
- No sensitive information leaked
- No stack traces exposed

**Server-Side Logs:**
- Detailed error information
- Stack traces for debugging
- PII masked (admin_id, not email)
- Request context included

---

## Appendix: Configuration

### Environment Variables

Required variables (`.env` file):

```env
# Application
APP_NAME="Organization Management Service"
VERSION="1.0.0"
ENVIRONMENT="development"
DEBUG=True

# MongoDB
MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0"
DATABASE_NAME="org_management"

# JWT
SECRET_KEY="your-secret-key-at-least-32-characters-long"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Logging
LOG_LEVEL="DEBUG"
```

### Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pymongo==4.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
bcrypt==4.1.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
email-validator==2.1.0
```

### Running the Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Summary

This API provides a complete multi-tenant organization management solution with:

✅ **Secure Authentication**: JWT with bcrypt, hardened against common attacks  
✅ **Atomic Operations**: Rollback on failures, consistent database state  
✅ **Input Validation**: Comprehensive sanitization and validation  
✅ **Isolation**: Dedicated collections per organization  
✅ **Cascade Deletion**: Clean resource cleanup  
✅ **Production-Ready**: Security headers, CORS, rate limiting, logging  

**Support:** For issues or questions, refer to the codebase documentation or contact the development team.

---

**Document Version:** 1.0.0  
**Last Updated:** December 12, 2025  
**Generated From:** Actual implementation (Phase 4 complete)
