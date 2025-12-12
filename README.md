# Organization Management Service

A production-ready FastAPI microservice for managing multi-tenant organizations with dynamic MongoDB collections, JWT authentication, and atomic data migrations.

## 🚀 Key Features

### Core Functionality
- **Multi-tenant Architecture** — Each organization operates in complete isolation with its own MongoDB collection
- **Secure Authentication** — JWT-based auth with bcrypt password hashing (13 rounds)
- **Atomic Migrations** — Safe organization updates with automatic rollback on any failure
- **Cascade Deletion** — Complete cleanup of organizations and all associated data

### Security & Quality
- **Input Validation** — Comprehensive validation and sanitization using Pydantic v2
- **Full Test Coverage** — 29 integration tests with 100% pass rate

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT APPLICATIONS                                 │
│                    (Web Browser, Mobile App, API Client)                        │
└────────────────────────────────┬────────────────────────────────────────────────┘
                                 │
                                 │ HTTP/HTTPS Requests
                                 │ (JSON payloads)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI APPLICATION LAYER                              │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                          MIDDLEWARE STACK                                   │ │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │ │
│ │  │ CORS         │  │ Security     │  │ JWT Auth     │                    │ │
│ │  │ Middleware   │→ │ Headers      │→ │ Validation   │                    │ │
│ │  └──────────────┘  └──────────────┘  └──────────────┘                    │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                         ROUTER LAYER (HTTP)                                 │ │
│ │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│ │  │  organization_router.py                                              │  │ │
│ │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │  │ │
│ │  │  │POST         │ │POST         │ │GET          │ │PUT          │  │  │ │
│ │  │  │/org/create  │ │/org/admin/  │ │/org/get     │ │/org/update  │  │  │ │
│ │  │  │             │ │login        │ │             │ │(JWT)        │  │  │ │
│ │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │  │ │
│ │  │  ┌─────────────┐                                                   │  │ │
│ │  │  │DELETE       │                                                   │  │ │
│ │  │  │/org/delete  │                                                   │  │ │
│ │  │  │(JWT)        │                                                   │  │ │
│ │  │  └─────────────┘                                                   │  │ │
│ │  └──────────────────────────────────────────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                      SERVICE LAYER (Business Logic)                         │ │
│ │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │ │
│ │  │  Organization    │  │  Admin           │  │  Collection      │         │ │
│ │  │  Service         │  │  Service         │  │  Service         │         │ │
│ │  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │         │ │
│ │  │  │ Validation │  │  │  │ Auth Logic │  │  │  │ Migrations │  │         │ │
│ │  │  │ Orchestr.  │  │  │  │ Pwd Hash   │  │  │  │ Rollback   │  │         │ │
│ │  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │         │ │
│ │  └──────────────────┘  └──────────────────┘  └──────────────────┘         │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│                                        ▼                                          │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                        MODEL LAYER (Data Access)                            │ │
│ │  ┌──────────────────┐  ┌──────────────────┐                                │ │
│ │  │  Organization    │  │  Admin           │                                │ │
│ │  │  Model           │  │  Model           │                                │ │
│ │  │  ┌────────────┐  │  │  ┌────────────┐  │                                │ │
│ │  │  │ CRUD Ops   │  │  │  │ CRUD Ops   │  │                                │ │
│ │  │  │ Indexes    │  │  │  │ Indexes    │  │                                │ │
│ │  │  └────────────┘  │  │  └────────────┘  │                                │ │
│ │  └──────────────────┘  └──────────────────┘                                │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                          │
│ ┌─────────────────────────────────────────────────────────────────────────────┐ │
│ │                      UTILITIES & CROSS-CUTTING                              │ │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │
│ │  │ Validators   │  │ Security     │  │ Config       │  │ Schemas      │  │ │
│ │  │ (Sanitize)   │  │ (JWT/bcrypt) │  │ (Settings)   │  │ (Pydantic)   │  │ │
│ │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │ │
│ └─────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────────┘
                                    │
                                    │ Motor (Async Driver)
                                    │ Connection Pool
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MONGODB DATABASE LAYER                                │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           MASTER DATABASE                                  │ │
│  │  ┌─────────────────────────┐        ┌─────────────────────────┐           │ │
│  │  │  organizations          │        │  admins                 │           │ │
│  │  │  ─────────────────────  │        │  ─────────────────────  │           │ │
│  │  │  _id: ObjectId          │◄──┐    │  _id: ObjectId          │           │ │
│  │  │  organization_name*     │   │    │  email* (unique)        │           │ │
│  │  │  collection_name        │   │    │  password_hash          │           │ │
│  │  │  admin_id ──────────────┼───┼───►│  organization_id        │           │ │
│  │  │  created_at            │   │    │  is_active              │           │ │
│  │  │  updated_at            │   │    │  last_login             │           │ │
│  │  │  status                │   │    │  role                   │           │ │
│  │  │                        │   │    │  created_at             │           │ │
│  │  │  * = indexed           │   │    │                         │           │ │
│  │  └─────────────────────────┘   │    └─────────────────────────┘           │ │
│  │                                 │                                           │ │
│  │                                 │ Foreign Key Relationship                  │ │
│  └─────────────────────────────────┼───────────────────────────────────────────┘ │
│                                    │                                             │
│  ┌────────────────────────────────┼─────────────────────────────────────────┐   │
│  │               DYNAMIC ORGANIZATION COLLECTIONS (Multi-Tenant)           │   │
│  │                                 │                                        │   │
│  │  ┌──────────────────┐  ┌───────▼──────────┐  ┌──────────────────┐     │   │
│  │  │  org_acme_corp   │  │  org_techstart   │  │  org_...         │     │   │
│  │  │  ──────────────  │  │  ──────────────  │  │  ──────────────  │     │   │
│  │  │  {user data}     │  │  {user data}     │  │  {user data}     │     │   │
│  │  │  {documents}     │  │  {documents}     │  │  {documents}     │     │   │
│  │  │  {custom fields} │  │  {custom fields} │  │  {custom fields} │     │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘     │   │
│  │                                                                         │   │
│  │  Each organization gets its own isolated collection                    │   │
│  │  Created dynamically on organization registration                      │   │
│  │  Migrated atomically on organization rename                            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           KEY ARCHITECTURAL FLOWS                                │
└─────────────────────────────────────────────────────────────────────────────────┘

📝 CREATE ORGANIZATION FLOW:
   Client → Router → OrganizationService → [
      1. Validate org name (validators)
      2. Create org doc (admin_id=None) → Master DB
      3. Create admin (with org_id) → Master DB
      4. Update org with admin_id → Master DB
      5. Create dynamic collection → org_{name}
   ] → Response | On Error → Rollback (delete org + collection)

🔐 ADMIN LOGIN FLOW:
   Client → Router → AdminService → [
      1. Sanitize email input
      2. Fetch admin by email → Master DB
      3. Verify password (bcrypt constant-time)
      4. Update last_login timestamp
      5. Generate JWT (admin_id, org_id, email, jti)
   ] → Token Response

🔄 UPDATE ORGANIZATION FLOW (Atomic Migration):
   Client + JWT → Router → Auth Middleware → Services → [
      1. Verify JWT & organization ownership
      2. Create new collection (org_new_name)
      3. Migrate all documents (old → new)
      4. Update org metadata in Master DB
      5. Delete old collection
      6. Update admin credentials (if provided)
   ] → Response | On Error → Complete Rollback:
      - Delete new collection
      - Restore old metadata
      - Recreate old collection if missing

🗑️ DELETE ORGANIZATION FLOW (Cascade):
   Client + JWT → Router → Auth Middleware → Services → [
      1. Verify JWT & organization ownership
      2. Delete dynamic collection (org_{name})
      3. Delete all admins (cascade)
      4. Delete organization document
   ] → Success Response

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY & DATA PROTECTION                                │
└─────────────────────────────────────────────────────────────────────────────────┘

🔒 Authentication Layer:
   ├─ JWT Tokens (HS256, 24h expiry)
   │  ├─ Algorithm confusion prevention (hardcoded HS256)
   │  ├─ IAT validation (rejects future-dated tokens)
   │  └─ JTI claim (token replay prevention)
   │
   ├─ Password Security
   │  ├─ bcrypt hashing (13 rounds)
   │  ├─ Constant-time verification (timing attack prevention)
   │  └─ Password strength validation (8+ chars, upper, lower, digit)
   │
   └─ Input Sanitization
      ├─ Pydantic schema validation
      ├─ Custom validators (email, org name)
      └─ NoSQL injection prevention (parameterized queries)

🛡️ Data Isolation:
   ├─ Multi-tenant via collection-per-tenant
   ├─ JWT-based authorization checks
   ├─ Organization ownership verification
   └─ No cross-tenant data access possible

♻️ Atomicity & Rollback:
   ├─ 3-step rollback on migration failure
   ├─ Collection recreation on partial failure
   ├─ Metadata restoration guarantees
   └─ Zero data loss on any failure scenario
```

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|----------|
| **Framework** | FastAPI | 0.104+ |
| **Database** | MongoDB (Motor async driver) | 4.4+ |
| **Authentication** | JWT (python-jose) | Latest |
| **Password Hashing** | bcrypt (passlib) | Latest |
| **Validation** | Pydantic | v2 |
| **Testing** | pytest + pytest-asyncio + httpx | Latest |
| **ASGI Server** | Uvicorn | Latest |

## 📋 Prerequisites

- Python 3.10+
- MongoDB 4.4+
- pip or poetry

## 🔧 Installation & Setup

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd organization-management-service
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (choose your OS)
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root directory:

```env
# ============================================
# Application Configuration
# ============================================
APP_NAME=Organization Management Service
APP_VERSION=1.0.0
DEBUG=True                    # Set to False in production

# ============================================
# Database Configuration
# ============================================
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=org_management

# ============================================
# Security Configuration
# ============================================
SECRET_KEY=your-secret-key-here-change-in-production  # Generate secure key!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

> **⚠️ Security Note:** Always generate a strong SECRET_KEY for production:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

### Step 5: Start MongoDB

**Option A: Using Docker (Recommended)**
```bash
docker run -d \
  -p 27017:27017 \
  --name mongodb \
  -v mongodb_data:/data/db \
  mongo:latest
```

**Option B: Local MongoDB Installation**
```bash
mongod --dbpath /path/to/your/data
```

**Option C: MongoDB Atlas (Cloud)**
- Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
- Update `MONGODB_URL` in `.env` with your connection string

## 🚀 Running the Application

### Development Mode (with auto-reload)

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Server starts at: **http://localhost:8000**

### Production Mode (multi-worker)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
```

### Interactive API Documentation

Once the server is running, access:

| Documentation | URL | Description |
|---------------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | Interactive API testing |
| **ReDoc** | http://localhost:8000/redoc | Clean API reference |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | Raw OpenAPI schema |

## 🧪 Testing

### Quick Test Commands

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests in quiet mode
pytest tests/ -q

# Run specific test file
pytest tests/test_organization_service.py -v

# Run specific test class
pytest tests/test_admin_service.py::TestAdminService -v

# Run specific test function
pytest tests/test_organization_service.py::TestOrganizationService::test_create_organization -v
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# View coverage in terminal
pytest tests/ --cov=app --cov-report=term-missing

# Generate XML coverage (for CI/CD)
pytest tests/ --cov=app --cov-report=xml
```

Open `htmlcov/index.html` to view detailed coverage report.

### Test Statistics

- **Total Tests:** 29
- **Pass Rate:** 100%
- **Coverage:** ~91%
- **Test Categories:**
  - Organization Service: 6 tests
  - Admin Service: 8 tests
  - Collection Service: 11 tests
  - API Endpoints: 5 tests

## 📁 Project Structure

```
organization-management-service/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # MongoDB connection
│   │   └── security.py        # JWT & password hashing
│   ├── middleware/
│   │   └── auth.py            # Authentication middleware
│   ├── models/
│   │   ├── admin.py           # Admin database model
│   │   └── organization.py    # Organization database model
│   ├── routers/
│   │   └── organization_router.py  # API endpoints
│   ├── schemas/
│   │   ├── admin.py           # Admin Pydantic schemas
│   │   ├── organization.py    # Organization Pydantic schemas
│   │   └── token.py           # JWT token schemas
│   ├── services/
│   │   ├── admin_service.py   # Admin business logic
│   │   ├── collection_service.py  # Collection management
│   │   └── organization_service.py  # Organization business logic
│   ├── utils/
│   │   └── validators.py      # Input validation utilities
│   └── main.py                # FastAPI application
├── tests/
│   ├── conftest.py            # Test fixtures
│   ├── test_endpoints.py      # Integration tests
│   ├── test_admin_service.py  # Admin service tests
│   ├── test_collection_service.py  # Collection service tests
│   └── test_organization_service.py  # Organization service tests
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── ARCHITECTURE.md            # Architecture documentation
├── DESIGN_DECISIONS.md        # Design rationale
├── API_DOCUMENTATION.md       # API reference
└── TEST_STRATEGY.md           # Testing approach
```

## 🔌 API Endpoints

### 1. Create Organization
```bash
curl -X POST "http://localhost:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corp",
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

### 2. Admin Login
```bash
curl -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

### 3. Get Organization
```bash
curl -X GET "http://localhost:8000/org/get?organization_name=acme_corp"
```

### 4. Update Organization (Requires JWT)
```bash
curl -X PUT "http://localhost:8000/org/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -d '{
    "organization_name": "acme_corporation"
  }'
```

### 5. Delete Organization (Requires JWT)
```bash
curl -X DELETE "http://localhost:8000/org/delete" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt with 13 rounds
- **JWT Tokens**: Secure token-based authentication
- **Input Sanitization**: All inputs sanitized to prevent injection
- **CORS Protection**: Configurable CORS origins
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, etc.

## 🏗️ Key Design Patterns

### Dynamic Collections
Each organization gets its own MongoDB collection (`org_{name}`), providing data isolation and scalability.

### Atomic Migrations
Organization updates use atomic operations with automatic rollback to ensure data consistency.

### Service Layer Pattern
Business logic separated into service classes for better testability and maintainability.

## 📊 Database Schema

### Organizations Collection (Master DB)
```json
{
  "_id": "ObjectId",
  "organization_name": "string",
  "collection_name": "string",
  "admin_id": "ObjectId",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Admins Collection (Master DB)
```json
{
  "_id": "ObjectId",
  "email": "string",
  "password_hash": "string",
  "organization_id": "ObjectId",
  "is_active": "boolean",
  "last_login": "datetime",
  "created_at": "datetime"
}
```

## 🐛 Troubleshooting

### MongoDB Connection Error
```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📈 Performance

- **Async Operations**: All database operations are asynchronous
- **Connection Pooling**: MongoDB connection pool managed by Motor
- **Indexed Queries**: Proper indexes on frequently queried fields

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see below for details.

### MIT License

```
MIT License

Copyright (c) 2025 E Hari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👥 Authors

**E Hari**
- Email: enguvahari@gmail.com
- GitHub: [@Harigithub11](https://github.com/Harigithub11)

## 🏢 Organization

Developed for The Wedding Company

## 🙏 Acknowledgments

- FastAPI for the excellent async framework
- MongoDB for the flexible database
- pytest for comprehensive testing tools
