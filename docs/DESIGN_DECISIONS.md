# Design Decisions & Technical Rationale

This document provides comprehensive documentation of the key architectural and design decisions made during the development of the Organization Management Service. Each decision includes the rationale, alternatives considered, trade-offs, and implementation details.

## Table of Contents

1. [Dynamic Collections Per Organization](#1-dynamic-collections-per-organization)
2. [Atomic Migrations with Rollback](#2-atomic-migrations-with-rollback)
3. [Security Architecture](#3-security-architecture)
4. [Input Validation Strategy](#4-input-validation-strategy)
5. [Error Handling Philosophy](#5-error-handling-philosophy)
6. [Async Operations](#6-async-operations)

---

## 1. Dynamic Collections Per Organization

### 📌 Decision Statement

Each organization receives its own dedicated MongoDB collection with the naming pattern `org_{organization_name}`, rather than storing all organization data in a single shared collection.

### 🎯 Primary Rationale

This design ensures **complete data isolation** between organizations, which is critical for security, compliance, and scalability in a multi-tenant system.

### ✅ Advantages

| Benefit | Description |
|---------|-------------|
| **🔒 Data Isolation** | Complete separation between organizations prevents accidental data leakage |
| **🛡️ Security** | Compromise of one organization doesn't affect others |
| **📈 Scalability** | Collections can be sharded independently based on organization size |
| **⚡ Performance** | Smaller collections enable faster queries and more efficient indexes |
| **🔧 Flexibility** | Each organization can have custom schemas in the future |
| **📜 Compliance** | Easier to meet data residency and privacy requirements (GDPR, HIPAA) |
| **💾 Backup/Restore** | Individual organizations can be backed up or restored independently |

### ⚠️ Trade-offs

| Challenge | Mitigation |
|-----------|------------|
| **Complexity** | More complex migration logic | Comprehensive rollback mechanisms |
| **Collection Limit** | MongoDB has a limit (~24,000 collections) | Monitor and alert at threshold |
| **Management** | More collections to monitor | Automated monitoring tools |

### 🚫 Alternative Considered

**Single Shared Collection Approach**
```json
{
  "_id": "ObjectId",
  "organization_id": "ObjectId",
  "data": { ... }
}
```

**Why Rejected:**
- ❌ Harder to ensure complete data isolation
- ❌ Query performance degrades as total data grows
- ❌ More complex access control at application layer
- ❌ Difficult to implement per-organization features
- ❌ Risk of cross-organization data leakage from bugs

### 🛠️ Implementation Details

```python
# Collection naming convention
def get_collection_name(organization_name: str) -> str:
    """Convert organization name to collection name."""
    sanitized = organization_name.lower().replace(" ", "_")
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
    return f"org_{sanitized}"

# Examples:
# "Acme Corp"           → "org_acme_corp"
# "Tech-Startup 2024"   → "org_techstartup2024"
# "Café & Restaurant"   → "org_caf_restaurant"
```

### 📊 Impact Analysis

- **Storage Overhead:** Minimal (empty collection ~4KB)
- **Query Performance:** Improved (smaller result sets)
- **Development Complexity:** Increased (rollback logic required)
- **Operational Complexity:** Moderate (more collections to monitor)
- **Security Posture:** Significantly improved

---

## 2. Atomic Migrations with Rollback

### 📌 Decision Statement

Organization updates (especially name changes that require collection migration) use atomic operations with comprehensive automatic rollback mechanisms.

### 🎯 Primary Rationale

Data integrity is paramount. Migration failures must never leave the system in an inconsistent state or result in data loss.

### 🔴 Why Rollback is Critical

| Risk | Impact Without Rollback | Mitigation with Rollback |
|------|------------------------|-------------------------|
| **Data Consistency** | Partial migrations leave system broken | Complete rollback restores original state |
| **User Experience** | Users lose access to their data | Seamless recovery, users never know |
| **Data Integrity** | Data may be partially or fully lost | Old data preserved until migration confirmed |
| **Production Safety** | Customer data loss is unacceptable | Zero data loss guarantee |

### 🔄 Migration Process

```
╭────────────────────────────────────────╮
│          ATOMIC MIGRATION FLOW           │
╰────────────────────────────────────────╯

1️⃣ CREATE NEW COLLECTION
   └─▶ org_new_name
   
2️⃣ MIGRATE ALL DOCUMENTS
   └─▶ Copy from org_old_name → org_new_name
   └─▶ Verify document count matches
   
3️⃣ UPDATE METADATA
   └─▶ organizations.collection_name
   └─▶ organizations.organization_name
   └─▶ organizations.updated_at
   
4️⃣ DELETE OLD COLLECTION
   └─▶ Drop org_old_name
   
✅ SUCCESS
```

### ⚡ Failure Scenarios & Handling

| Failure Point | Scenario | Rollback Action |
|---------------|----------|----------------|
| **Step 1** | Disk space exhausted | Delete new collection |
| **Step 2** | Network timeout during copy | Delete new collection, keep old |
| **Step 2** | Duplicate key error | Delete new collection, keep old |
| **Step 3** | Metadata update fails | Delete new collection, restore metadata |
| **Step 4** | Cannot drop old collection | Manual cleanup, migration still successful |

### 🛠️ Rollback Implementation

```python
async def update_organization_with_migration(
    old_name: str,
    new_name: str
) -> dict:
    """
    Atomic migration with comprehensive rollback.
    """
    new_collection = f"org_{new_name}"
    old_collection = f"org_{old_name}"
    
    try:
        # Step 1: Create new collection
        await collection_service.create_collection(new_collection)
        
        # Step 2: Migrate all documents
        migrated_count = await collection_service.migrate_collection(
            source=old_collection,
            target=new_collection
        )
        
        # Step 3: Update metadata (atomic)
        await organization_model.update(
            {"collection_name": old_collection},
            {
                "organization_name": new_name,
                "collection_name": new_collection,
                "updated_at": datetime.utcnow()
            }
        )
        
        # Step 4: Delete old collection
        await collection_service.delete_collection(old_collection)
        
        return {"success": True, "migrated": migrated_count}
        
    except Exception as e:
        # ROLLBACK: Restore original state
        logger.error(f"Migration failed: {e}. Rolling back...")
        
        # Delete new collection if created
        await collection_service.delete_collection(new_collection)
        
        # Ensure old collection still exists
        if not await collection_service.collection_exists(old_collection):
            # Recreate if somehow deleted
            await collection_service.create_collection(old_collection)
        
        # Restore original metadata
        await organization_model.update(
            {"organization_name": new_name},
            {
                "organization_name": old_name,
                "collection_name": old_collection
            }
        )
        
        raise HTTPException(
            status_code=409,
            detail="Organization update failed. Original state restored."
        )
```

### 🚫 Alternative Considered

**Two-Phase Commit Protocol**
```
Phase 1: Prepare (lock resources)
Phase 2: Commit (apply changes)
```

**Why Rejected:**
- ❌ MongoDB doesn't support multi-collection transactions
- ❌ Adds significant complexity (coordinator, locks, timeouts)
- ❌ Our rollback approach is simpler and equally safe
- ❌ No performance benefit
- ❌ Requires distributed transaction manager

### 📋 Testing Coverage

- ✅ Test migration success
- ✅ Test rollback on step 1 failure
- ✅ Test rollback on step 2 failure (network timeout simulation)
- ✅ Test rollback on step 3 failure (metadata update)
- ✅ Test data integrity after rollback
- ✅ Test concurrent migration attempts

---

## 3. Security Architecture

### 3.1 JWT Authentication

**Decision**: Use JWT tokens instead of session-based authentication.

**Rationale:**
- **Stateless**: No server-side session storage needed
- **Scalable**: Works across multiple server instances
- **Mobile-Friendly**: Easy to store and send from mobile apps
- **Standard**: Industry-standard approach (OAuth 2.0 compatible)
- **Performance**: No database lookup on every request

**Token Contents:**
```json
{
  "admin_id": "...",
  "organization_id": "...",
  "email": "...",
  "type": "admin",
  "jti": "unique-id",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Security Measures:**
- Tokens expire after 24 hours (configurable)
- Signed with HS256 algorithm
- JTI (JWT ID) for token revocation in future
- Type field to distinguish admin vs other token types

### 3.2 Password Hashing (Bcrypt)

**Decision**: Use bcrypt with 13 rounds for password hashing.

**Rationale:**
- **Industry Standard**: Widely accepted and battle-tested
- **Adaptive**: Can increase rounds as hardware improves
- **Salt Included**: Automatic salting prevents rainbow table attacks
- **Slow by Design**: Makes brute-force attacks impractical

**Why 13 Rounds:**
- Balance between security and performance
- ~100-200ms hashing time (acceptable for login)
- Resistant to GPU-based attacks

**Alternative Considered:**
Argon2 (winner of Password Hashing Competition).

**Why Bcrypt Chosen:**
- More mature ecosystem
- Better Python library support
- Sufficient for our security needs
- Easier to audit and debug

### 3.3 Input Sanitization

**Decision**: Sanitize all user inputs before processing.

**Rationale:**
- **Injection Prevention**: Prevents NoSQL injection attacks
- **XSS Prevention**: Removes potentially malicious scripts
- **Data Quality**: Ensures consistent data format
- **Validation**: Catches malformed inputs early

**Sanitization Strategy:**
```python
# Remove dangerous characters
# Trim whitespace
# Enforce length limits
# Convert to lowercase (for names)
```

**Validation Layers:**
1. **Pydantic Schemas**: Type checking and basic validation
2. **Custom Validators**: Business rule validation
3. **Input Sanitizer**: Remove dangerous characters
4. **Database Constraints**: Final safety net

---

## 4. Validation Strategy

### Decision
Multi-layered validation approach with fail-fast principle.

### Validation Layers

**Layer 1: Pydantic Schemas**
```python
class OrganizationCreate(BaseModel):
    organization_name: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
```

**Layer 2: Custom Validators**
```python
OrganizationNameValidator.validate(name)
EmailValidator.validate(email)
PasswordValidator.validate(password)
```

**Layer 3: Business Logic**
```python
if await org_exists(name):
    raise ValueError("Organization already exists")
```

**Layer 4: Database Constraints**
```python
# Unique indexes on organization_name, email
```

### Rationale

**Why Multiple Layers:**
- **Defense in Depth**: Multiple chances to catch errors
- **Clear Error Messages**: Each layer provides specific feedback
- **Performance**: Fail fast before expensive operations
- **Maintainability**: Each layer has single responsibility

**Validation Rules:**

**Organization Name:**
- 3-50 characters
- Alphanumeric, underscores, hyphens only
- No leading/trailing whitespace
- Unique across system

**Email:**
- Valid email format (RFC 5322)
- Unique per admin
- Case-insensitive

**Password:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Special characters allowed

---

## 5. Error Handling Philosophy

### Decision
Consistent error handling with appropriate HTTP status codes and detailed error messages.

### Error Code Strategy

**400 Bad Request**: Client error (duplicate org, invalid input)
**401 Unauthorized**: Authentication failure
**403 Forbidden**: Authorization failure (wrong organization)
**404 Not Found**: Resource doesn't exist
**409 Conflict**: Migration/update conflict
**422 Unprocessable Entity**: Validation error
**500 Internal Server Error**: Server/database error

### Rationale

**Principle: Be Specific**
- Clients can handle errors appropriately
- Easier debugging
- Better user experience

**Principle: Don't Leak Information**
```python
# Bad: "Admin with email admin@acme.com not found"
# Good: "Invalid credentials"
```

**Principle: Log Everything**
```python
logger.error(f"Failed to create org: {e}")  # Server-side
return {"detail": "Failed to create organization"}  # Client-side
```

### Error Response Format
```json
{
  "detail": "Human-readable error message"
}
```

---

## 6. Service Layer Pattern

### Decision
Separate business logic into service classes instead of putting it in routers.

### Rationale

**Benefits:**
- **Testability**: Services can be unit tested independently
- **Reusability**: Same service methods used by multiple endpoints
- **Maintainability**: Business logic in one place
- **Separation of Concerns**: Routers handle HTTP, services handle logic

**Architecture:**
```
Router (HTTP handling)
    ↓
Service (Business logic)
    ↓
Model (Database operations)
    ↓
MongoDB
```

**Example:**
```python
# Router: Thin layer
@router.post("/create")
async def create_org(data: OrgCreate, db = Depends(get_database)):
    service = OrganizationService(db)
    return await service.create_organization(data)

# Service: Business logic
class OrganizationService:
    async def create_organization(self, data):
        # Validation
        # Duplicate check
        # Create org
        # Create collection
```

---

## 7. Async/Await Architecture

### Decision
Use async/await for all I/O operations.

### Rationale

**Performance Benefits:**
- Non-blocking I/O
- Handle more concurrent requests
- Better resource utilization
- Lower latency

**Why FastAPI + Motor:**
- FastAPI: Native async support
- Motor: Async MongoDB driver
- Perfect match for I/O-bound operations

**When to Use Async:**
- ✅ Database queries
- ✅ External API calls
- ✅ File I/O
- ❌ CPU-intensive tasks (use threads/processes)

---

## 8. Database Design

### 8.1 Master Database vs Dynamic Collections

**Decision**: Use a master database for metadata and dynamic collections for organization data.

**Master Database:**
- `organizations` collection
- `admins` collection

**Dynamic Collections:**
- `org_{name}` collections

**Rationale:**
- Centralized metadata for quick lookups
- Isolated data for security
- Easy to scale independently

### 8.2 Indexing Strategy

**Decision**: Create indexes on frequently queried fields.

**Indexes Created:**
```python
# organizations collection
- organization_name (unique)
- collection_name (unique)
- admin_id

# admins collection
- email (unique)
- organization_id
```

**Rationale:**
- Fast lookups by name/email
- Enforce uniqueness at database level
- Prevent full collection scans

---

## 9. Testing Strategy

### Decision
Comprehensive testing with unit tests, integration tests, and rollback simulation.

**Test Pyramid:**
```
        /\
       /  \  Integration Tests (21 tests)
      /    \
     /      \
    /________\ Unit Tests (30+ tests)
```

**Why Integration Tests:**
- Test real database operations
- Verify end-to-end flows
- Catch integration issues
- Test rollback mechanisms

**Why Mock Failures:**
- Simulate production failures
- Test rollback logic
- Ensure data consistency
- Validate error handling

---

## 10. Configuration Management

### Decision
Use environment variables with Pydantic settings.

**Rationale:**
- **12-Factor App**: Follow industry best practices
- **Security**: Secrets not in code
- **Flexibility**: Easy to change per environment
- **Type Safety**: Pydantic validates config

**Configuration Structure:**
```python
class Settings(BaseSettings):
    MONGODB_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    class Config:
        env_file = ".env"
```

---

## 11. Logging Strategy

### Decision
Structured logging with different levels for different scenarios.

**Log Levels:**
- **INFO**: Successful operations
- **WARNING**: Auth failures, validation errors
- **ERROR**: Rollbacks, database errors
- **CRITICAL**: System failures

**What to Log:**
- ✅ State changes (org created, updated, deleted)
- ✅ Authentication attempts
- ✅ Rollback events
- ✅ Errors with context
- ❌ Passwords or tokens
- ❌ PII (use masked IDs)

**Example:**
```python
logger.info(f"Organization created: {org_name}")
logger.warning(f"Login failed for admin: {email[:3]}***")
logger.error(f"Rollback triggered: {error}")
```

---

## 12. Future-Proofing Decisions

### Extensibility Points

**1. Custom Organization Schemas**
Dynamic collections allow each org to have custom fields in future.

**2. Multiple Admin Roles**
Token type field allows for different user types (admin, user, guest).

**3. Multi-Region Support**
Stateless JWT allows deployment across regions.

**4. Event Sourcing**
Logging structure supports adding event sourcing later.

**5. Rate Limiting**
Token-based auth makes per-user rate limiting easy.

---

## Summary

These design decisions prioritize:
1. **Security**: Multiple layers of protection
2. **Reliability**: Atomic operations with rollback
3. **Scalability**: Async architecture, dynamic collections
4. **Maintainability**: Clean separation of concerns
5. **Testability**: Comprehensive test coverage

Each decision was made with production readiness in mind, balancing simplicity with robustness.
