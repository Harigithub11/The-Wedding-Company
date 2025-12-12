# Architecture Documentation

## System Overview

The Organization Management Service implements a **layered architecture pattern** with clear separation of concerns across four primary layers. The system is purpose-built for multi-tenancy, ensuring each organization operates in complete isolation with its dedicated MongoDB collection.

### Architectural Principles

- **🏛️ Layered Design** — Clean separation between routers, services, models, and database
- **🔒 Isolation First** — Each organization's data is completely isolated
- **⚡ Async by Default** — All I/O operations use async/await for maximum performance
- **🛡️ Security Built-in** — JWT authentication and authorization at every layer

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                              │
│                    (Browser/Mobile App)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Server                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Middleware Layer                        │  │
│  │  • CORS Handler                                      │  │
│  │  • Security Headers                                  │  │
│  │  • JWT Authentication (get_current_user)             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Router Layer                            │  │
│  │  • organization_router.py                            │  │
│  │    - POST /org/create                                │  │
│  │    - GET /org/get                                    │  │
│  │    - POST /org/admin/login                           │  │
│  │    - PUT /org/update                                 │  │
│  │    - DELETE /org/delete                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Service Layer                           │  │
│  │  • OrganizationService (business logic)              │  │
│  │  • AdminService (user management)                    │  │
│  │  • CollectionService (dynamic collections)           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Model Layer                             │  │
│  │  • OrganizationModel (DB operations)                 │  │
│  │  • AdminModel (DB operations)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ Motor (Async Driver)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MongoDB Database                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Master Database                         │  │
│  │  • organizations (collection)                        │  │
│  │  • admins (collection)                               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Dynamic Organization Collections             │  │
│  │  • org_acme_corp (collection)                        │  │
│  │  • org_tech_startup (collection)                     │  │
│  │  • org_... (one per organization)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow Diagrams

### 1. Unauthenticated Request Flow (Organization Creation)

**Endpoint:** `POST /org/create`

```
╭───────────────────────╮
│  Client HTTP Request   │
╰───────────┬──────────╯
           │
           ↓  JSON Body
╭───────────┴─────────────────────────────╮
│  FastAPI Router (organization_router.py)  │
╰──────────────────┬─────────────────────╯
                 │
                 ↓  Pydantic Validation
╭────────────────┴─────────────────────╮
│  Input Sanitization (XSS/SQL Prevention) │
╰────────────────┬─────────────────────╯
                 │
                 ↓  Business Logic
╭────────────────┴──────────────────────────────╮
│  Service Layer (OrganizationService, AdminService) │
╰────────────────┬──────────────────────────────╯
                 │
                 ↓  Database Operations
╭────────────────┴─────────────────────────╮
│  Model Layer (OrganizationModel, AdminModel) │
╰────────────────┬─────────────────────────╯
                 │
                 ↓  Motor Async Driver
╭────────────────┴────────────────╮
│  MongoDB Master Database         │
│  - organizations collection     │
│  - admins collection            │
╰────────────────┬────────────────╯
                 │
                 ↓  Collection Creation
╭────────────────┴──────────────────────╮
│  CollectionService                   │
│  Creates org_acme_corp collection    │
╰────────────────┬──────────────────────╯
                 │
                 ↓  HTTP 201 Created
╭────────────────┴─────────────────────╮
│  OrganizationCreateResponse          │
│  { organization, admin_id, message } │
╰────────────────┬─────────────────────╯
                 │
                 ↓
╭────────────────┴──────╮
│  Client Receives JSON  │
╰──────────────────────╯
```

### 2. Authenticated Request Flow (Organization Update)

**Endpoint:** `PUT /org/update`  
**Auth Required:** ✅ Yes (JWT Token)

```
╭──────────────────────────────────╮
│  Client Request + JWT Token    │
│  Authorization: Bearer <token>  │
╰───────────────┬───────────────────╯
               │
               ↓  JWT in Header
╭──────────────┴─────────────────────────╮
│  JWT Middleware (get_current_user)     │
│  ├─ Decode JWT token                 │
│  ├─ Verify signature (SECRET_KEY)     │
│  ├─ Check expiration (exp claim)      │
│  └─ Extract TokenData                 │
│     {admin_id, organization_id, email} │
╰──────────────┬─────────────────────────╯
               │
               ↓  TokenData Object
╭──────────────┴─────────────────────────╮
│  Authorization Check                  │
│  Verify admin owns organization       │
╰──────────────┬─────────────────────────╯
               │
               ↓  Authorized
╭──────────────┴─────────────────────────────╮
│  OrganizationService                    │
│  Atomic migration with rollback logic  │
╰──────────────┬─────────────────────────────╯
               │
               ↓  Multi-step Process
╭──────────────┴─────────────────────────────╮
│  1. Create new collection              │
│  2. Migrate all documents              │
│  3. Update organization metadata       │
│  4. Delete old collection              │
│  (Rollback on any failure)             │
╰──────────────┬─────────────────────────────╯
               │
               ↓  Success
╭──────────────┴────────────────╮
│  HTTP 200 OK Response          │
│  { message, organization }     │
╰───────────────────────────────╯
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Admin Login Flow                         │
└─────────────────────────────────────────────────────────────┘

1. Client sends credentials
   POST /org/admin/login
   { "email": "admin@acme.com", "password": "SecurePass123" }
        ↓
2. Router receives request
   organization_router.admin_login()
        ↓
3. AdminService.authenticate_admin()
   ├─ Lookup admin by email
   ├─ Verify password (bcrypt)
   └─ Update last_login timestamp
        ↓
4. JWTHandler.create_token_for_admin()
   ├─ Create payload:
   │  {
   │    "admin_id": "...",
   │    "organization_id": "...",
   │    "email": "...",
   │    "type": "admin",
   │    "jti": "unique-id",
   │    "exp": timestamp,
   │    "iat": timestamp
   │  }
   └─ Sign with SECRET_KEY
        ↓
5. Return JWT token
   {
     "access_token": "eyJhbGc...",
     "token_type": "bearer",
     "expires_in": 86400
   }
        ↓
6. Client stores token
        ↓
7. Client includes token in subsequent requests
   Authorization: Bearer eyJhbGc...
        ↓
8. get_current_user dependency validates token
   ├─ Decode JWT
   ├─ Verify signature
   ├─ Check expiration
   └─ Extract TokenData
        ↓
9. Protected endpoint executes
```

## Dynamic Collection Model

### Design Philosophy

Each organization gets its own MongoDB collection to ensure:
- **Data Isolation**: Organizations cannot access each other's data
- **Scalability**: Collections can be distributed across shards
- **Performance**: Smaller collections = faster queries
- **Flexibility**: Each org can have custom schemas in the future

### Collection Naming Convention

```
Master Database Collections:
- organizations
- admins

Dynamic Collections:
- org_{sanitized_organization_name}

Example:
Organization: "Acme Corp"
Collection: "org_acme_corp"
```

### Collection Lifecycle

```
CREATE:
  1. Validate organization name
  2. Sanitize name → collection_name
  3. Create organization document
  4. Create admin document
  5. Create dynamic collection
  6. Link admin to organization

UPDATE (with name change):
  1. Validate new name
  2. Create new collection
  3. Migrate all documents
  4. Update organization metadata
  5. Delete old collection
  6. Rollback on any failure

DELETE:
  1. Delete dynamic collection
  2. Delete all admins
  3. Delete organization document
```

## Atomic Migration Process (PUT /org/update)

### Migration Flow

```
┌─────────────────────────────────────────────────────────────┐
│              Atomic Migration with Rollback                 │
└─────────────────────────────────────────────────────────────┘

Phase 1: Preparation
├─ Authenticate user
├─ Validate new organization name
├─ Check for duplicates
└─ Store old state for rollback

Phase 2: Migration (Atomic)
├─ Step 1: Create new collection
│   └─ Track: new_collection_created = True
├─ Step 2: Migrate all documents
│   └─ Copy data from old → new
├─ Step 3: Update organization metadata
│   └─ Update name and collection_name
└─ Step 4: Delete old collection

Phase 3: Rollback (on any failure)
├─ Delete new collection (if created)
├─ Restore old organization metadata
├─ Ensure old collection exists (recreate if missing)
└─ Raise HTTP 409 Conflict

Phase 4: Success
└─ Return updated organization info
```

### Rollback Guarantees

The system ensures **database consistency** through:

1. **State Tracking**: Variables track what has been created
2. **Incremental Rollback**: Each step can be reversed
3. **Collection Recreation**: Old collection recreated if deleted
4. **Metadata Restoration**: Original data restored
5. **Error Logging**: All failures logged for debugging

## Cascade Deletion Flow

```
DELETE /org/delete
    ↓
1. Authenticate user
    ↓
2. Verify organization ownership
    ↓
3. Delete dynamic collection
   └─ db.drop_collection("org_acme_corp")
    ↓
4. Delete all admins for organization
   └─ AdminModel.delete_by_organization_id()
    ↓
5. Delete organization document
   └─ OrganizationModel.delete(org_id)
    ↓
6. Log deletion for audit
    ↓
7. Return success response
```

## Database Schema Design

### Master Database

#### Organizations Collection
```javascript
{
  _id: ObjectId("..."),
  organization_name: "acme_corp",        // Unique, indexed
  collection_name: "org_acme_corp",      // Unique, indexed
  admin_id: ObjectId("..."),             // Reference to admins
  created_at: ISODate("2025-12-12T00:00:00Z"),
  updated_at: ISODate("2025-12-12T00:00:00Z")
}

Indexes:
- organization_name (unique)
- collection_name (unique)
- admin_id
```

#### Admins Collection
```javascript
{
  _id: ObjectId("..."),
  email: "admin@acme.com",               // Unique, indexed
  password_hash: "$2b$13$...",           // Bcrypt hash
  organization_id: ObjectId("..."),      // Reference to organizations
  is_active: true,
  last_login: ISODate("2025-12-12T00:00:00Z"),
  created_at: ISODate("2025-12-12T00:00:00Z")
}

Indexes:
- email (unique)
- organization_id
```

### Dynamic Collections

Each organization's collection can store any documents:
```javascript
// Collection: org_acme_corp
{
  _id: ObjectId("..."),
  // Custom fields per organization
  // Future: can have different schemas per org
}
```

## Security Architecture

### Defense in Depth

```
Layer 1: Input Validation
├─ Pydantic schemas
├─ Custom validators (email, password, org name)
└─ Input sanitization

Layer 2: Authentication
├─ JWT token verification
├─ Token expiration checks
└─ Signature validation

Layer 3: Authorization
├─ Organization ownership verification
├─ Admin role checks
└─ Resource access control

Layer 4: Data Protection
├─ Password hashing (bcrypt)
├─ No sensitive data in responses
└─ Secure token storage

Layer 5: Network Security
├─ CORS configuration
├─ Security headers
└─ HTTPS (in production)
```

## Scalability Considerations

### Horizontal Scaling
- **Stateless API**: No session storage, uses JWT
- **Connection Pooling**: Motor manages MongoDB connections
- **Load Balancing**: Multiple FastAPI instances can run

### Database Scaling
- **Sharding**: Dynamic collections can be sharded by organization
- **Indexing**: Proper indexes on frequently queried fields
- **Replication**: MongoDB replica sets for high availability

### Performance Optimization
- **Async Operations**: All I/O is non-blocking
- **Batch Operations**: Bulk inserts/updates where possible
- **Caching**: Can add Redis for frequently accessed data

## Error Handling Strategy

```
Error Propagation:
Model Layer → Service Layer → Router Layer → Client

Error Types:
├─ Validation Errors (422)
│  └─ Caught at Pydantic schema level
├─ Business Logic Errors (400, 404, 409)
│  └─ Raised by service layer
├─ Authentication Errors (401)
│  └─ Raised by middleware
├─ Authorization Errors (403)
│  └─ Raised by endpoint logic
└─ System Errors (500)
   └─ Caught by global exception handler
```

## Monitoring & Logging

### Logging Levels
- **INFO**: Successful operations, state changes
- **WARNING**: Validation failures, auth failures
- **ERROR**: Rollback events, database errors
- **CRITICAL**: System failures, data inconsistencies

### Key Metrics to Monitor
- Request latency
- Database query time
- Authentication success/failure rate
- Rollback frequency
- Error rates by endpoint

## Future Enhancements

1. **Caching Layer**: Redis for frequently accessed organizations
2. **Event Sourcing**: Track all changes for audit
3. **Rate Limiting**: Per-organization API limits
4. **Webhooks**: Notify on organization events
5. **Multi-region**: Deploy across regions for low latency