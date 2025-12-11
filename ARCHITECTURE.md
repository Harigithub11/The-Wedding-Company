# Architecture Document
## Organization Management Service - Multi-Tenant Backend System

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Patterns](#architecture-patterns)
4. [Component Design](#component-design)
5. [Database Architecture](#database-architecture)
6. [API Design](#api-design)
7. [Security Architecture](#security-architecture)
8. [Data Flow Diagrams](#data-flow-diagrams)
9. [Scalability Analysis](#scalability-analysis)
10. [Trade-offs & Alternatives](#trade-offs--alternatives)
11. [Technology Stack](#technology-stack)
12. [Deployment Architecture](#deployment-architecture)

---

## Executive Summary

This document describes the architecture of a **multi-tenant organization management service** built using FastAPI and MongoDB. The system implements a **collection-per-tenant** approach where each organization gets its own MongoDB collection for data isolation, while a Master Database maintains global metadata and user authentication information.

### Key Architectural Decisions:
- **Framework**: FastAPI (Python) for high performance and automatic API documentation
- **Database**: MongoDB for flexible schema and dynamic collection creation
- **Multi-Tenancy**: Collection-per-tenant approach for data isolation
- **Authentication**: JWT-based stateless authentication
- **Security**: Bcrypt password hashing, role-based access control
- **Design Pattern**: Service-oriented architecture with clean separation of concerns

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│                  (Postman, Web App, Mobile)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│                      (FastAPI Router)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /org/create  │  /org/get  │  /org/update  │  /org/delete│  │
│  │                    /admin/login                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Middleware Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │ Auth Guard   │  │  Validation  │  │  Error Handling    │   │
│  │  (JWT)       │  │  (Pydantic)  │  │                    │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Organization   │  │    Admin     │  │   Collection    │   │
│  │    Service      │  │   Service    │  │    Service      │   │
│  └─────────────────┘  └──────────────┘  └─────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Access Layer                            │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Organization   │  │    Admin     │  │   Collection    │   │
│  │     Model       │  │    Model     │  │    Manager      │   │
│  └─────────────────┘  └──────────────┘  └─────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Layer (MongoDB)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Master Database                            │  │
│  │  ┌────────────────────┐  ┌────────────────────────┐     │  │
│  │  │  organizations     │  │      admins            │     │  │
│  │  │  Collection        │  │      Collection        │     │  │
│  │  └────────────────────┘  └────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Dynamic Organization Collections              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │org_company1│  │org_company2│  │org_company3│  ...    │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Patterns

### 1. Layered Architecture

The application follows a **4-layer architecture**:

```
┌─────────────────────────────────────┐
│     Presentation Layer (Router)     │  ← API Endpoints, Request/Response
├─────────────────────────────────────┤
│     Business Logic (Service)        │  ← Core business rules
├─────────────────────────────────────┤
│     Data Access Layer (Model)       │  ← Database operations
├─────────────────────────────────────┤
│     Database Layer (MongoDB)        │  ← Data persistence
└─────────────────────────────────────┘
```

**Benefits:**
- Clear separation of concerns
- Easy to test each layer independently
- Flexible to change database without affecting business logic
- Maintainable and scalable

---

### 2. Service-Oriented Architecture (SOA)

Each business domain has its own service:

```
OrganizationService ──┐
                      ├──► Database Layer
AdminService ─────────┤
                      │
CollectionService ────┘
```

**Benefits:**
- Single Responsibility Principle
- Reusable services across different endpoints
- Easy to extend with new services

---

### 3. Dependency Injection

FastAPI's dependency injection for authentication:

```python
@router.delete("/org/delete")
async def delete_org(
    current_user: dict = Depends(get_current_user)  # ← Injected
):
    # Only authenticated users can access
```

**Benefits:**
- Decoupled authentication logic
- Easy to test with mock dependencies
- Centralized authentication handling

---

## Component Design

### 1. Project Structure

```
organization-management-service/
│
├── app/
│   ├── __init__.py
│   │
│   ├── main.py                      # FastAPI application entry point
│   │
│   ├── core/                        # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                # Environment configuration
│   │   ├── security.py              # JWT & password hashing
│   │   └── database.py              # MongoDB connection manager
│   │
│   ├── models/                      # Database models
│   │   ├── __init__.py
│   │   ├── organization.py          # Organization model
│   │   └── admin.py                 # Admin user model
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── organization.py          # Org request/response schemas
│   │   ├── admin.py                 # Admin schemas
│   │   └── token.py                 # JWT token schemas
│   │
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── organization_service.py  # Organization operations
│   │   ├── admin_service.py         # Admin operations
│   │   └── collection_service.py    # Dynamic collection management
│   │
│   ├── routers/                     # API routes
│   │   ├── __init__.py
│   │   ├── organization.py          # Organization endpoints
│   │   └── admin.py                 # Admin endpoints
│   │
│   ├── middleware/                  # Custom middleware
│   │   ├── __init__.py
│   │   └── error_handler.py         # Global error handling
│   │
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       └── validators.py            # Custom validators
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── test_organization.py
│   ├── test_admin.py
│   └── test_auth.py
│
├── docs/                            # Documentation
│   ├── architecture_diagram.png
│   └── api_examples.md
│
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
├── ARCHITECTURE.md                  # This file
└── Dockerfile                       # Docker configuration (optional)
```

---

### 2. Component Responsibilities

#### A. Router Layer (`routers/`)
```python
# Responsibilities:
- Accept HTTP requests
- Validate request data using Pydantic
- Call appropriate service methods
- Return HTTP responses
- Handle HTTP-specific concerns (status codes, headers)

# Does NOT:
- Contain business logic
- Directly access database
- Perform complex validations
```

#### B. Service Layer (`services/`)
```python
# Responsibilities:
- Implement business logic
- Orchestrate operations across multiple models
- Transaction management
- Business rule validation
- Error handling for business logic

# Does NOT:
- Know about HTTP requests/responses
- Directly create database connections
```

#### C. Model Layer (`models/`)
```python
# Responsibilities:
- Database CRUD operations
- Data validation at database level
- Query construction
- Schema definition

# Does NOT:
- Contain business logic
- Know about HTTP layer
```

#### D. Core Layer (`core/`)
```python
# Responsibilities:
- Configuration management
- Database connection pooling
- Security utilities (JWT, hashing)
- Shared infrastructure

# Does NOT:
- Contain business logic
- Define routes
```

---

## Database Architecture

### 1. Master Database Design

The Master Database contains two primary collections:

#### Collection: `organizations`
```javascript
{
  "_id": ObjectId("..."),                    // MongoDB generated ID
  "organization_name": "company1",           // Unique organization name
  "collection_name": "org_company1",         // Dynamic collection name
  "created_at": ISODate("2025-12-11T..."),   // Creation timestamp
  "updated_at": ISODate("2025-12-11T..."),   // Last update timestamp
  "admin_id": ObjectId("..."),               // Reference to admin user
  "status": "active",                        // Organization status
  "metadata": {                              // Optional metadata
    "industry": "technology",
    "size": "small"
  }
}

// Indexes:
db.organizations.createIndex({ "organization_name": 1 }, { unique: true })
db.organizations.createIndex({ "admin_id": 1 })
db.organizations.createIndex({ "created_at": -1 })
```

#### Collection: `admins`
```javascript
{
  "_id": ObjectId("..."),                    // MongoDB generated ID
  "email": "admin@company1.com",             // Unique email
  "password_hash": "$2b$12$...",             // Bcrypt hashed password
  "organization_id": ObjectId("..."),        // Reference to organization
  "created_at": ISODate("2025-12-11T..."),   // Creation timestamp
  "last_login": ISODate("2025-12-11T..."),   // Last login timestamp
  "is_active": true,                         // Account status
  "role": "admin"                            // User role
}

// Indexes:
db.admins.createIndex({ "email": 1 }, { unique: true })
db.admins.createIndex({ "organization_id": 1 })
db.admins.createIndex({ "email": 1, "organization_id": 1 })
```

---

### 2. Dynamic Organization Collections

Each organization gets its own collection following the naming pattern: `org_<organization_name>`

#### Example: `org_company1`
```javascript
// This collection can store organization-specific data
// Schema is flexible and can be defined per organization needs

// Example document structure (optional initialization):
{
  "_id": ObjectId("..."),
  "data_type": "sample",
  "created_at": ISODate("2025-12-11T..."),
  "content": {
    // Organization-specific data
  }
}

// The collection starts empty and can be populated as needed
// This provides maximum flexibility for different org needs
```

---

### 3. Database Connection Architecture

```
┌─────────────────────────────────────────────┐
│         FastAPI Application                 │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │   Database Connection Singleton       │ │
│  │                                       │ │
│  │   ┌───────────────────────────────┐  │ │
│  │   │   Connection Pool (10-100)    │  │ │
│  │   │                               │  │ │
│  │   │  ┌─────┐ ┌─────┐ ┌─────┐    │  │ │
│  │   │  │Conn1│ │Conn2│ │Conn3│ ...│  │ │
│  │   │  └─────┘ └─────┘ └─────┘    │  │ │
│  │   └───────────────────────────────┘  │ │
│  └───────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
                   │
                   │ MongoDB Wire Protocol
                   ▼
┌─────────────────────────────────────────────┐
│           MongoDB Server/Cluster            │
│                                             │
│  ┌────────────────┐  ┌──────────────────┐  │
│  │ Master Database│  │ Org Collections  │  │
│  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────┘
```

**Connection Management:**
- Singleton pattern ensures one connection pool per application
- Connection pooling for efficient resource usage
- Automatic reconnection on connection loss
- Graceful shutdown handling

---

## API Design

### 1. RESTful API Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/org/create` | No | Create new organization |
| GET | `/org/get` | No | Get organization details |
| PUT | `/org/update` | Yes (JWT) | Update organization |
| DELETE | `/org/delete` | Yes (JWT) | Delete organization |
| POST | `/admin/login` | No | Admin authentication |

---

### 2. Request/Response Schemas

#### POST `/org/create`

**Request:**
```json
{
  "organization_name": "company1",
  "email": "admin@company1.com",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "message": "Organization created successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "company1",
    "collection_name": "org_company1",
    "created_at": "2025-12-11T10:30:00Z"
  },
  "admin": {
    "id": "507f1f77bcf86cd799439012",
    "email": "admin@company1.com"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Organization name 'company1' already exists"
}
```

---

#### GET `/org/get?organization_name=company1`

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "organization_name": "company1",
  "collection_name": "org_company1",
  "created_at": "2025-12-11T10:30:00Z",
  "admin_email": "admin@company1.com"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Organization 'company1' not found"
}
```

---

#### POST `/admin/login`

**Request:**
```json
{
  "email": "admin@company1.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

---

#### PUT `/org/update`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request:**
```json
{
  "organization_name": "company1_renamed",
  "email": "newemail@company1.com",
  "password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Organization updated successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "company1_renamed",
    "collection_name": "org_company1_renamed",
    "updated_at": "2025-12-11T11:00:00Z"
  }
}
```

---

#### DELETE `/org/delete?organization_name=company1`

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "message": "Organization 'company1' deleted successfully"
}
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "You don't have permission to delete this organization"
}
```

---

## Security Architecture

### 1. Authentication Flow

```
┌──────────┐                                    ┌──────────┐
│  Client  │                                    │  Server  │
└────┬─────┘                                    └────┬─────┘
     │                                                │
     │  1. POST /admin/login                         │
     │    { email, password }                        │
     ├──────────────────────────────────────────────►│
     │                                                │
     │                                          2. Query admin
     │                                          by email
     │                                                │
     │                                          3. Verify password
     │                                          using bcrypt
     │                                                │
     │  4. Return JWT token                          │
     │◄──────────────────────────────────────────────┤
     │    { access_token: "..." }                    │
     │                                                │
     │  5. Protected endpoint request                │
     │    Authorization: Bearer <token>              │
     ├──────────────────────────────────────────────►│
     │                                                │
     │                                          6. Verify JWT
     │                                          signature
     │                                                │
     │                                          7. Decode token
     │                                          payload
     │                                                │
     │                                          8. Extract user info
     │                                          (admin_id, org_id)
     │                                                │
     │  9. Return protected resource                 │
     │◄──────────────────────────────────────────────┤
     │                                                │
```

---

### 2. Password Security

**Bcrypt Hashing:**
```python
# Registration
password = "SecurePass123!"
salt = bcrypt.gensalt(rounds=12)  # 12 rounds = 4096 iterations
password_hash = bcrypt.hashpw(password.encode(), salt)
# Result: $2b$12$KIXVzRb... (60 characters)

# Login
stored_hash = "$2b$12$KIXVzRb..."
is_valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
```

**Security Features:**
- Automatic salt generation
- Configurable work factor (12 rounds recommended)
- Resistant to rainbow table attacks
- Slow by design (prevents brute force)

---

### 3. JWT Token Structure

```
Header:
{
  "alg": "HS256",        # Algorithm
  "typ": "JWT"           # Token type
}

Payload:
{
  "admin_id": "507f1f77bcf86cd799439012",
  "organization_id": "507f1f77bcf86cd799439011",
  "email": "admin@company1.com",
  "exp": 1702388400,     # Expiration (24 hours)
  "iat": 1702302000      # Issued at
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  SECRET_KEY
)
```

**Security Features:**
- Stateless authentication
- Tamper-proof signature
- Expiration time enforced
- Secret key stored in environment variable

---

### 4. Security Best Practices Implemented

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                        │
├─────────────────────────────────────────────────────────┤
│  1. Transport Security                                  │
│     ✓ HTTPS only in production                          │
│     ✓ TLS 1.2+ required                                 │
├─────────────────────────────────────────────────────────┤
│  2. Input Validation                                    │
│     ✓ Pydantic schema validation                        │
│     ✓ Email format validation                           │
│     ✓ Password strength requirements                    │
│     ✓ SQL injection prevention (parameterized queries)  │
├─────────────────────────────────────────────────────────┤
│  3. Authentication & Authorization                      │
│     ✓ JWT-based stateless auth                          │
│     ✓ Bcrypt password hashing (12 rounds)               │
│     ✓ Token expiration (24 hours)                       │
│     ✓ Role-based access control                         │
├─────────────────────────────────────────────────────────┤
│  4. Data Protection                                     │
│     ✓ No passwords in logs                              │
│     ✓ Sensitive data excluded from responses            │
│     ✓ Environment variables for secrets                 │
├─────────────────────────────────────────────────────────┤
│  5. Error Handling                                      │
│     ✓ Generic error messages (no info leakage)          │
│     ✓ Proper HTTP status codes                          │
│     ✓ No stack traces in production                     │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Organization Creation Flow

```
┌────────┐     POST /org/create      ┌─────────────┐
│ Client │─────────────────────────► │   Router    │
└────────┘  {org_name, email, pwd}   └──────┬──────┘
                                             │
                                             │ 1. Validate input
                                             ▼
                                      ┌─────────────┐
                                      │  Pydantic   │
                                      │  Validator  │
                                      └──────┬──────┘
                                             │
                                             │ 2. Call service
                                             ▼
                                      ┌─────────────────┐
                                      │ Organization    │
                                      │    Service      │
                                      └──────┬──────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                        ▼                    ▼                    ▼
              3. Check if exists    4. Hash password   5. Create collection
              ┌─────────────┐      ┌─────────────┐    ┌─────────────┐
              │Organization │      │  Security   │    │ Collection  │
              │   Model     │      │   Utils     │    │   Service   │
              └──────┬──────┘      └──────┬──────┘    └──────┬──────┘
                     │                    │                   │
                     │ Not exists         │ Hash              │ Create
                     ▼                    ▼                   ▼
              ┌──────────────────────────────────────────────────┐
              │              MongoDB Operations                  │
              │                                                  │
              │  1. Insert into 'admins' collection             │
              │  2. Insert into 'organizations' collection      │
              │  3. Create 'org_<name>' collection              │
              └──────────────────┬───────────────────────────────┘
                                 │
                                 │ 6. Return success
                                 ▼
                          ┌─────────────┐
                          │   Router    │
                          └──────┬──────┘
                                 │
                                 │ 7. HTTP 201 response
                                 ▼
                          ┌────────┐
                          │ Client │
                          └────────┘
```

---

### 2. Admin Login Flow

```
┌────────┐    POST /admin/login     ┌─────────────┐
│ Client │─────────────────────────►│   Router    │
└────────┘   {email, password}      └──────┬──────┘
                                            │
                                            │ 1. Validate input
                                            ▼
                                     ┌─────────────┐
                                     │Admin Service│
                                     └──────┬──────┘
                                            │
                                            │ 2. Get admin by email
                                            ▼
                                     ┌─────────────┐
                                     │ Admin Model │
                                     └──────┬──────┘
                                            │
                                            │ 3. Query database
                                            ▼
                                     ┌─────────────┐
                                     │   MongoDB   │
                                     │   'admins'  │
                                     └──────┬──────┘
                                            │
                                            │ 4. Return admin doc
                                            ▼
                                     ┌─────────────┐
                                     │  Security   │
                                     │    Utils    │
                                     └──────┬──────┘
                                            │
                                            │ 5. Verify password
                                            │    bcrypt.checkpw()
                                            ▼
                                     ┌─────────────┐
                                     │ Generate JWT│
                                     │    Token    │
                                     └──────┬──────┘
                                            │
                                            │ 6. Return token
                                            ▼
                                     ┌─────────────┐
                                     │   Router    │
                                     └──────┬──────┘
                                            │
                                            │ 7. HTTP 200 response
                                            ▼
                                     ┌────────┐
                                     │ Client │
                                     └────────┘
```

---

### 3. Organization Update Flow (with Data Migration)

```
┌────────┐   PUT /org/update        ┌─────────────┐
│ Client │─────────────────────────►│   Router    │
└────────┘   + JWT Token            └──────┬──────┘
                                            │
                                            │ 1. Extract JWT
                                            ▼
                                     ┌─────────────┐
                                     │Auth Guard   │
                                     │(Middleware) │
                                     └──────┬──────┘
                                            │
                                            │ 2. Verify token
                                            │    Get user context
                                            ▼
                                     ┌─────────────────┐
                                     │ Organization    │
                                     │    Service      │
                                     └──────┬──────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        │                   │                   │
                        ▼                   ▼                   ▼
              3. Verify ownership  4. Check new name   5. Create new
              ┌─────────────┐     ┌─────────────┐     collection
              │Organization │     │Organization │     ┌─────────────┐
              │   Model     │     │   Model     │     │ Collection  │
              └──────┬──────┘     └──────┬──────┘     │   Service   │
                     │                   │             └──────┬──────┘
                     │ Is owner?         │ Available?         │
                     ▼                   ▼                    ▼
              ┌──────────────────────────────────────────────────┐
              │         MongoDB Transaction (Atomic)             │
              │                                                  │
              │  1. Create 'org_<new_name>' collection          │
              │  2. Copy all data from 'org_<old_name>'         │
              │  3. Update 'organizations' collection           │
              │  4. Update 'admins' collection (if creds change)│
              │  5. Delete 'org_<old_name>' collection          │
              │                                                  │
              │  If any step fails → ROLLBACK                   │
              └──────────────────┬───────────────────────────────┘
                                 │
                                 │ 6. Return success
                                 ▼
                          ┌─────────────┐
                          │   Router    │
                          └──────┬──────┘
                                 │
                                 │ 7. HTTP 200 response
                                 ▼
                          ┌────────┐
                          │ Client │
                          └────────┘
```

---

### 4. Organization Deletion Flow

```
┌────────┐  DELETE /org/delete      ┌─────────────┐
│ Client │─────────────────────────►│   Router    │
└────────┘   + JWT Token            └──────┬──────┘
                                            │
                                            │ 1. Authenticate
                                            ▼
                                     ┌─────────────┐
                                     │Auth Guard   │
                                     └──────┬──────┘
                                            │
                                            │ 2. Verify ownership
                                            ▼
                                     ┌─────────────────┐
                                     │ Organization    │
                                     │    Service      │
                                     └──────┬──────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        │                   │                   │
                        ▼                   ▼                   ▼
              3. Delete org         4. Delete admins   5. Delete collection
              collection
              ┌─────────────┐      ┌─────────────┐    ┌─────────────┐
              │Organization │      │Admin Model  │    │ Collection  │
              │   Model     │      │             │    │   Service   │
              └──────┬──────┘      └──────┬──────┘    └──────┬──────┘
                     │                    │                   │
                     │                    │                   │
                     ▼                    ▼                   ▼
              ┌──────────────────────────────────────────────────┐
              │         MongoDB Transaction (Atomic)             │
              │                                                  │
              │  1. Drop 'org_<name>' collection                │
              │  2. Delete from 'admins' collection             │
              │  3. Delete from 'organizations' collection      │
              │                                                  │
              │  If any step fails → ROLLBACK                   │
              └──────────────────┬───────────────────────────────┘
                                 │
                                 │ 6. Return success
                                 ▼
                          ┌─────────────┐
                          │   Router    │
                          └──────┬──────┘
                                 │
                                 │ 7. HTTP 200 response
                                 ▼
                          ┌────────┐
                          │ Client │
                          └────────┘
```

---

## Scalability Analysis

### Current Architecture: Collection-Per-Tenant

#### Advantages ✓
1. **Strong Data Isolation**
   - Each organization's data in separate collection
   - Accidental data leaks less likely
   - Easy to comply with data privacy regulations (GDPR)

2. **Flexible Schema**
   - Each organization can have different schema
   - Easy to customize per tenant
   - No schema conflicts between tenants

3. **Easy Backup/Restore**
   - Can backup/restore individual organizations
   - Selective data migration
   - Organization-specific maintenance

4. **Performance per Tenant**
   - Queries only scan one tenant's data
   - Indexes specific to each tenant
   - No cross-tenant query overhead

5. **Easy to Scale Out**
   - Can move specific organization collections to different servers
   - Sharding by organization is natural
   - Load balancing opportunities

#### Disadvantages ✗
1. **Collection Limit**
   - MongoDB has soft limit of ~10,000 collections per database
   - Hard limit depends on namespace file size
   - Not suitable for 100,000+ tenants

2. **Resource Overhead**
   - Each collection has metadata overhead
   - Indexes consume memory for each collection
   - Connection pool shared across all collections

3. **Query Complexity**
   - Cross-organization analytics difficult
   - No global queries without aggregating all collections
   - Reporting across tenants complex

4. **Operational Complexity**
   - More collections to monitor
   - Backup strategies more complex
   - Index management multiplied

5. **Memory Usage**
   - MongoDB keeps collection metadata in RAM
   - With 1000s of collections, memory pressure increases
   - Working set may not fit in cache

---

### Scalability Limits

| Metric | Limit | Notes |
|--------|-------|-------|
| **Max Organizations** | ~5,000-10,000 | MongoDB collection limit |
| **Concurrent Users** | 10,000+ | With proper connection pooling |
| **Requests/Second** | 1,000+ | FastAPI + MongoDB performance |
| **Data per Org** | Unlimited | MongoDB document/collection limits |
| **Database Size** | TBs | Limited by disk space |

---

### Scaling Strategies

#### 1. Horizontal Scaling (Recommended)

```
┌────────────────────────────────────────────────────┐
│              Load Balancer (Nginx)                 │
└────────┬──────────┬──────────┬──────────┬──────────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │FastAPI │ │FastAPI │ │FastAPI │ │FastAPI │
    │Instance│ │Instance│ │Instance│ │Instance│
    │   1    │ │   2    │ │   3    │ │   4    │
    └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
         │          │          │          │
         └──────────┴──────────┴──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   MongoDB Cluster   │
         │  (Replica Set or    │
         │   Sharded Cluster)  │
         └─────────────────────┘
```

**Implementation:**
- Deploy multiple FastAPI instances
- Use Nginx/HAProxy for load balancing
- Stateless API design allows horizontal scaling
- JWT tokens work across all instances

---

#### 2. Database Sharding

```
Organizations 0-999      Organizations 1000-1999   Organizations 2000-2999
       ▼                         ▼                         ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Shard 1    │         │   Shard 2    │         │   Shard 3    │
│              │         │              │         │              │
│ org_company1 │         │ org_company2 │         │ org_company3 │
│ org_company4 │         │ org_company5 │         │ org_company6 │
│    ...       │         │    ...       │         │    ...       │
└──────────────┘         └──────────────┘         └──────────────┘
       │                         │                         │
       └─────────────────────────┴─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │   MongoDB Router    │
                    │     (mongos)        │
                    └─────────────────────┘
```

**Sharding Strategy:**
- Shard key: `organization_name` or `organization_id`
- Each shard handles subset of organizations
- Automatic query routing by MongoDB
- Scales to millions of organizations

---

#### 3. Caching Layer

```
┌────────┐                                    ┌─────────┐
│ Client │──────────────────────────────────►│FastAPI  │
└────────┘                                    └────┬────┘
                                                   │
                                                   │ 1. Check cache
                                                   ▼
                                            ┌────────────┐
                                            │   Redis    │
                                            │   Cache    │
                                            └─────┬──────┘
                                                  │
                                    Cache Hit ────┘
                                         │
                                         │ 2. Return cached data
                                         │
                                    Cache Miss
                                         │
                                         │ 3. Query database
                                         ▼
                                  ┌────────────┐
                                  │  MongoDB   │
                                  └─────┬──────┘
                                        │
                                        │ 4. Store in cache
                                        │
                                        │ 5. Return data
```

**Caching Strategy:**
- Cache organization metadata (rarely changes)
- Cache admin authentication data
- TTL: 5-15 minutes
- Invalidate on update/delete

---

### Performance Optimization

#### 1. Database Indexes
```javascript
// organizations collection
db.organizations.createIndex({ "organization_name": 1 }, { unique: true })
db.organizations.createIndex({ "admin_id": 1 })
db.organizations.createIndex({ "created_at": -1 })

// admins collection
db.admins.createIndex({ "email": 1 }, { unique: true })
db.admins.createIndex({ "organization_id": 1 })
db.admins.createIndex({ "email": 1, "organization_id": 1 })
```

#### 2. Connection Pooling
```python
# Optimal settings
minPoolSize = 10
maxPoolSize = 100
maxIdleTimeMS = 60000  # 1 minute
connectTimeoutMS = 5000  # 5 seconds
```

#### 3. Query Optimization
- Use projection to fetch only required fields
- Avoid large document scans
- Use aggregation pipeline for complex queries
- Limit result sets

---

## Trade-offs & Alternatives

### Alternative 1: Database-Per-Tenant

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Database   │  │  Database   │  │  Database   │
│   Company1  │  │   Company2  │  │   Company3  │
│             │  │             │  │             │
│ collection1 │  │ collection1 │  │ collection1 │
│ collection2 │  │ collection2 │  │ collection2 │
└─────────────┘  └─────────────┘  └─────────────┘
```

**Pros:**
- Strongest data isolation
- No collection limit concerns
- Easy to separate/migrate entire tenants
- Can use different DB versions per tenant

**Cons:**
- Connection overhead (connection pool per DB)
- Resource intensive
- More complex connection management
- Backup/monitoring complexity
- Not cost-effective for small tenants

**When to Use:**
- Large enterprise tenants
- Strong compliance requirements
- Tenants need dedicated resources
- <1000 total tenants

---

### Alternative 2: Schema-Per-Tenant (Not MongoDB)

For SQL databases like PostgreSQL:
```sql
CREATE SCHEMA company1;
CREATE SCHEMA company2;

company1.users
company1.products

company2.users
company2.products
```

**Pros:**
- Better than shared schema for isolation
- Single database connection pool
- Better than database-per-tenant for resource usage

**Cons:**
- Not applicable to MongoDB (no schema concept)
- Still have scaling limits
- Cross-schema queries complex

---

### Alternative 3: Shared Collection with Tenant ID

```javascript
// Single 'data' collection for all tenants
{
  "_id": ObjectId("..."),
  "tenant_id": "company1",  // ← Discriminator
  "data_type": "user",
  "content": { ... }
}

// Query with tenant_id filter
db.data.find({ "tenant_id": "company1" })
```

**Pros:**
- No collection limit
- Simple structure
- Easy cross-tenant analytics
- Lower resource overhead
- Scales to millions of tenants

**Cons:**
- Weaker data isolation (one mistake = data leak)
- Indexes shared across all tenants
- Complex query patterns (always filter by tenant_id)
- All tenants must have same schema
- One bad tenant can affect all (noisy neighbor)

**When to Use:**
- SaaS with 10,000+ small tenants
- Same schema across all tenants
- Cross-tenant analytics important
- Lower compliance requirements

---

### Comparison Matrix

| Feature | Collection-Per-Tenant<br>(Current) | Database-Per-Tenant | Shared Collection<br>+ Tenant ID |
|---------|------------|-----------------|------------------|
| **Data Isolation** | ✓✓ Strong | ✓✓✓ Strongest | ✓ Weak |
| **Tenant Limit** | ~10,000 | ~1,000 | Millions |
| **Resource Efficiency** | ✓✓ Good | ✓ Poor | ✓✓✓ Excellent |
| **Schema Flexibility** | ✓✓✓ Excellent | ✓✓✓ Excellent | ✓ Poor |
| **Query Performance** | ✓✓✓ Excellent | ✓✓✓ Excellent | ✓✓ Good |
| **Operational Complexity** | ✓✓ Medium | ✓ High | ✓✓✓ Low |
| **Cross-Tenant Analytics** | ✓ Difficult | ✓ Difficult | ✓✓✓ Easy |
| **Compliance (GDPR)** | ✓✓ Good | ✓✓✓ Excellent | ✓ Challenging |
| **Cost** | ✓✓ Medium | ✓ High | ✓✓✓ Low |

---

### Recommendation

**Current Architecture (Collection-Per-Tenant) is optimal when:**
1. Expected tenants: 100 - 5,000 organizations
2. Strong data isolation required
3. Per-tenant customization needed
4. MongoDB is the database choice
5. Budget allows for medium resource usage

**Switch to Shared Collection when:**
1. Expected tenants: > 10,000 organizations
2. SaaS application with many small tenants
3. Same schema across all tenants
4. Cross-tenant analytics important
5. Cost optimization is priority

**Switch to Database-Per-Tenant when:**
1. Large enterprise clients (< 500 tenants)
2. Regulatory compliance critical (healthcare, finance)
3. Tenants need dedicated resources/SLA
4. Budget allows for high resource usage

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | 0.104+ | High-performance async API framework |
| **Server** | Uvicorn | 0.24+ | ASGI server for FastAPI |
| **Database** | MongoDB | 6.0+ | NoSQL database for flexible schema |
| **ODM** | Motor | 3.3+ | Async MongoDB driver for Python |
| **Language** | Python | 3.10+ | Primary programming language |
| **Authentication** | PyJWT | 2.8+ | JWT token generation/validation |
| **Password Hashing** | Passlib | 1.7+ | Bcrypt password hashing |
| **Validation** | Pydantic | 2.5+ | Data validation and settings |
| **Testing** | Pytest | 7.4+ | Unit and integration testing |
| **Code Quality** | Black, Pylint | Latest | Code formatting and linting |

---

### Dependencies

```
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pymongo==4.6.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Configuration
pydantic[email]==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Code Quality
black==23.12.0
pylint==3.0.3
mypy==1.7.1
```

---

### Development Tools

```
# API Testing
- Postman / Thunder Client (VS Code extension)
- FastAPI Swagger UI (/docs endpoint)
- ReDoc (/redoc endpoint)

# Database Management
- MongoDB Compass (GUI)
- mongosh (CLI)
- Studio 3T (optional)

# Version Control
- Git
- GitHub

# IDE
- VS Code (recommended)
- PyCharm Professional
```

---

## Local Development Setup

### Running the Application Locally

This application is designed to run locally for development and testing. No cloud deployment is required for submission.

```
┌────────────────────────────────────────────────────┐
│              Local Development Machine             │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │         FastAPI Application                  │ │
│  │         (uvicorn app.main:app)               │ │
│  │         Port: 8000                           │ │
│  └────────────────┬─────────────────────────────┘ │
│                   │                                │
│                   │ Connects to                    │
│                   ▼                                │
│  ┌──────────────────────────────────────────────┐ │
│  │         MongoDB Database                     │ │
│  │                                              │ │
│  │  Option 1: Local MongoDB (localhost:27017)  │ │
│  │  Option 2: MongoDB Atlas FREE Tier          │ │
│  └──────────────────────────────────────────────┘ │
│                                                    │
│  Access:                                          │
│  - API: http://localhost:8000                     │
│  - Docs: http://localhost:8000/docs               │
│  - ReDoc: http://localhost:8000/redoc             │
└────────────────────────────────────────────────────┘
```

---

### Setup Options

#### Option 1: Local MongoDB (Recommended for Offline Work)

**Windows:**
```bash
# Download MongoDB Community Server from mongodb.com
# Install and run MongoDB as a service
# Default connection: mongodb://localhost:27017
```

**macOS:**
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Connection: mongodb://localhost:27017
```

**Linux (Ubuntu/Debian):**
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Connection: mongodb://localhost:27017
```

---

#### Option 2: MongoDB Atlas FREE Tier (Recommended for Simplicity)

**Benefits:**
- ✓ No local installation needed
- ✓ 512MB storage (free forever)
- ✓ Accessible from anywhere
- ✓ Built-in monitoring
- ✓ Automatic backups

**Setup Steps:**
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create a free account
3. Create a new cluster (select FREE tier - M0)
4. Choose your preferred cloud provider and region
5. Create database user (username + password)
6. Whitelist IP address (use 0.0.0.0/0 for development)
7. Get connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```
8. Add to `.env` file

---

#### Option 3: Docker MongoDB (For Consistent Environment)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: org_management_mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: org_management_db
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

volumes:
  mongodb_data:
```

**Run:**
```bash
docker-compose up -d
# Connection: mongodb://localhost:27017
```

---

### Environment Configuration

Create a `.env` file in your project root:

**Option 1: Local MongoDB**
```env
# .env
ENVIRONMENT=development
DEBUG=True
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=org_management
SECRET_KEY=your-secret-key-min-32-chars-long
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Option 2: MongoDB Atlas FREE Tier**
```env
# .env
ENVIRONMENT=development
DEBUG=True
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
DATABASE_NAME=org_management
SECRET_KEY=your-secret-key-min-32-chars-long
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**.env.example (for GitHub):**
```env
# Copy this file to .env and fill in your values
ENVIRONMENT=development
DEBUG=True
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=org_management
SECRET_KEY=change-this-to-a-secure-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

### Docker Configuration (Optional)

Docker is optional for local development. Use it if you prefer containerized environments.

**Dockerfile (Optional):**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run application with hot reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**docker-compose.yml (Optional - for local development):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - DATABASE_NAME=org_management
      - SECRET_KEY=dev-secret-key-change-this
      - DEBUG=True
    volumes:
      - ./app:/app/app  # Hot reload for development
    depends_on:
      - mongodb

  mongodb:
    image: mongo:6.0
    container_name: org_management_mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

**Run with Docker:**
```bash
# Start all services
docker-compose up

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

---

### Monitoring & Logging

#### Application Monitoring
```python
# Structured logging
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
```

#### Metrics to Monitor
```
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query time
- JWT token validation time
- Active database connections
- Memory usage
- CPU usage
```

#### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow()
    }
```

---

## Conclusion

This architecture provides a solid foundation for a multi-tenant organization management service with:

✓ **Strong data isolation** through collection-per-tenant
✓ **Scalability** up to 5,000-10,000 organizations
✓ **Security** with JWT + bcrypt
✓ **Performance** with MongoDB indexes and connection pooling
✓ **Maintainability** with clean layered architecture
✓ **Flexibility** with dynamic collection creation

### Future Enhancements

1. **Rate Limiting** - Prevent API abuse with request throttling
2. **Email Verification** - Verify admin emails on signup
3. **2FA** - Two-factor authentication for admins
4. **Audit Logs** - Track all organization changes with timestamps
5. **API Versioning** - Support multiple API versions (v1, v2)
6. **GraphQL** - Alternative to REST API for flexible queries
7. **Webhooks** - Notify external systems of organization events
8. **Password Reset** - Email-based password recovery
9. **Organization Members** - Support multiple users per organization
10. **Data Export** - Allow organizations to export their data

---

**Document Version:** 1.0
**Last Updated:** 2025-12-11
**Author:** Backend Development Team
**Status:** Ready for Local Development & Testing