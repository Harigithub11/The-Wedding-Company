# 🚀 Local Setup Guide

## 📋 Overview

This guide provides step-by-step instructions to set up and run the Organization Management Service on your local machine.

### ⏱️ Estimated Setup Time

| Experience Level | Time Required |
|------------------|---------------|
| **Experienced Developer** | 10-15 minutes |
| **Intermediate** | 20-30 minutes |
| **Beginner** | 30-45 minutes |

## 📝 Prerequisites

Before you begin, ensure you have the following installed:

| Software | Version | Download |
|----------|---------|----------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **MongoDB** | 4.4+ | [mongodb.com](https://www.mongodb.com/try/download/community) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/downloads) |
| **pip** | Latest | Included with Python |

### ✅ Verify Installation

```bash
# Check Python version
python --version
# Expected: Python 3.10.0 or higher

# Check pip version
pip --version
# Expected: pip 21.0 or higher

# Check MongoDB version
mongod --version
# Expected: db version v4.4.0 or higher

# Check Git version
git --version
# Expected: git version 2.30.0 or higher
```

## 🛠️ Step-by-Step Setup

### 1️⃣ Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>

# Navigate to project directory
cd organization-management-service

# Verify you're in the correct directory
ls
# Expected: app/ tests/ requirements.txt README.md etc.
```

### 2️⃣ Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (prompt should show (venv))
which python  # macOS/Linux
where python  # Windows
# Expected: Path should point to venv/bin/python or venv\Scripts\python
```

### 3️⃣ Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list
# Expected: Should show fastapi, motor, pytest, etc.
```

### 4️⃣ Step 4: Set Up MongoDB

#### 📦 Option A: Local MongoDB Installation

```bash
# Start MongoDB (macOS/Linux)
mongod --dbpath /path/to/your/data

# Start MongoDB (Windows)
mongod --dbpath C:\path\to\your\data

# Verify MongoDB is running
mongosh
# Expected: MongoDB shell should connect
```

#### 🐳 Option B: MongoDB with Docker

```bash
# Pull MongoDB image
docker pull mongo:latest

# Run MongoDB container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:latest

# Verify container is running
docker ps
# Expected: Should show mongodb container

# Connect to MongoDB
docker exec -it mongodb mongosh
# Expected: MongoDB shell should connect
```

#### ☁️ Option C: MongoDB Atlas (Cloud)

1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get connection string
4. Update `.env` file with connection string

### 5️⃣ Step 5: Configure Environment Variables

```bash
# Create .env file
touch .env  # macOS/Linux
type nul > .env  # Windows

# Edit .env file with your favorite editor
# Add the following content:
```

**.env file content:**

```env
# ============================================
# Application Configuration
# ============================================
APP_NAME=Organization Management Service
APP_VERSION=1.0.0
DEBUG=True

# ============================================
# Database Configuration
# ============================================
# For local MongoDB:
MONGODB_URL=mongodb://localhost:27017

# For MongoDB Atlas:
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

DATABASE_NAME=org_management

# ============================================
# Security Configuration
# ============================================
# Generate a secure secret key:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-secret-key-here-change-this

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# CORS Configuration
# ============================================
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# ============================================
# Logging Configuration
# ============================================
LOG_LEVEL=INFO
```

### 6️⃣ Step 6: Generate Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output and paste it in .env file as SECRET_KEY
# Example output: dGhpcyBpcyBhIHNlY3JldCBrZXk...
```

### 7️⃣ Step 7: Verify Configuration

```bash
# Test MongoDB connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('mongodb://localhost:27017').admin.command('ping')); print('MongoDB connected!')"

# Expected: MongoDB connected!
```

## 🏃 Running the Application

### ▶️ Start the Server

```bash
# Make sure virtual environment is activated
# Make sure MongoDB is running

# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

### ✅ Verify Server is Running

```bash
# Open a new terminal (keep the server running in the first terminal)

# Test health endpoint
curl http://localhost:8000/

# Expected: {"message": "Organization Management Service"}

# Or open in browser:
# http://localhost:8000/docs
# Expected: Swagger UI should load
```

### 📚 Access API Documentation

Open your browser and navigate to:

| Documentation | URL | Description |
|---------------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | Interactive API testing |
| **ReDoc** | http://localhost:8000/redoc | Clean API reference |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | Raw OpenAPI schema |

## 🧪 Running Tests

### 🏃 Run All Tests

```bash
# Make sure virtual environment is activated
# Make sure MongoDB is running

# Run all tests
pytest tests/ -v

# Expected output:
# ============================= test session starts =============================
# collected 29 items
# tests/test_admin_service.py::test_create_admin PASSED
# tests/test_organization_service.py::test_create_organization PASSED
# ...
# ============================= 29 passed in 22.63s ==============================
```

### 📝 Run Specific Test File

```bash
# Run organization service tests
pytest tests/test_organization_service.py -v

# Run admin service tests
pytest tests/test_admin_service.py -v

# Run collection service tests
pytest tests/test_collection_service.py -v

# Run endpoint tests
pytest tests/test_endpoints.py -v
```

### 📊 Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Expected: Creates htmlcov/ directory

# View coverage report
# Open htmlcov/index.html in browser
```

### Run Specific Test

```bash
# Run single test function
pytest tests/test_organization_service.py::TestOrganizationService::test_create_organization -v

# Run single test class
pytest tests/test_admin_service.py::TestAdminService -v
```

## 📂 Project Directory Structure

```
organization-management-service/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # MongoDB connection
│   │   └── security.py            # JWT & password hashing
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py                # Authentication middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── admin.py               # Admin database model
│   │   └── organization.py        # Organization database model
│   ├── routers/
│   │   ├── __init__.py
│   │   └── organization_router.py # API endpoints
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── admin.py               # Admin Pydantic schemas
│   │   ├── organization.py        # Organization Pydantic schemas
│   │   └── token.py               # JWT token schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── admin_service.py       # Admin business logic
│   │   ├── collection_service.py  # Collection management
│   │   └── organization_service.py # Organization business logic
│   ├── utils/
│   │   ├── __init__.py
│   │   └── validators.py          # Input validation utilities
│   ├── __init__.py
│   └── main.py                    # FastAPI application
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Test fixtures
│   ├── test_admin_service.py      # Admin service tests
│   ├── test_collection_service.py # Collection service tests
│   ├── test_endpoints.py          # API endpoint tests
│   └── test_organization_service.py # Organization service tests
├── .env                           # Environment variables (create this)
├── .gitignore                     # Git ignore file
├── requirements.txt               # Python dependencies
├── README.md                      # Project README
├── ARCHITECTURE_OVERVIEW.md       # Architecture documentation
├── MULTI_TENANT_DESIGN.md         # Multi-tenancy design
├── AUTH_FLOW.md                   # Authentication flow
├── ORG_UPDATE_FLOW.md             # Update flow documentation
├── ORG_DELETE_FLOW.md             # Delete flow documentation
├── SCALABILITY_AND_TRADEOFFS.md   # Scalability analysis
└── LOCAL_SETUP_GUIDE.md           # This file
```

## 🧪 Testing the API

### 1️⃣ Create Organization

```bash
curl -X POST "http://localhost:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "test_company",
    "email": "admin@test.com",
    "password": "SecurePass123"
  }'

# Expected: 201 Created
# {
#   "message": "Organization created successfully",
#   "organization": {...},
#   "admin_id": "..."
# }
```

### 2️⃣ Admin Login

```bash
curl -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "SecurePass123"
  }'

# Expected: 200 OK
# {
#   "access_token": "eyJhbGc...",
#   "token_type": "bearer",
#   "expires_in": 86400
# }

# Save the access_token for next requests
```

### 3️⃣ Get Organization

```bash
curl -X GET "http://localhost:8000/org/get?organization_name=test_company"

# Expected: 200 OK
# {
#   "id": "...",
#   "organization_name": "test_company",
#   "collection_name": "org_test_company",
#   "admin_email": "admin@test.com",
#   ...
# }
```

### 4️⃣ Update Organization (Requires JWT)

```bash
# Replace <TOKEN> with the access_token from login
curl -X PUT "http://localhost:8000/org/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "organization_name": "test_company_updated"
  }'

# Expected: 200 OK
# {
#   "message": "Organization updated successfully",
#   "organization": {...}
# }
```

### 5️⃣ Delete Organization (Requires JWT)

```bash
# Replace <TOKEN> with the access_token from login
curl -X DELETE "http://localhost:8000/org/delete" \
  -H "Authorization: Bearer <TOKEN>"

# Expected: 200 OK
# {
#   "message": "Organization 'test_company_updated' deleted successfully"
# }
```

## ⚠️ Common Issues & Solutions

### 🛑 Issue 1: MongoDB Connection Error

```
Error: pymongo.errors.ServerSelectionTimeoutError
```

**Solution:**
```bash
# Check if MongoDB is running
mongosh

# If not running, start MongoDB
mongod --dbpath /path/to/data

# Or start Docker container
docker start mongodb
```

### 🛑 Issue 2: Port Already in Use

```
Error: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn app.main:app --port 8001
```

### 🛑 Issue 3: Module Not Found

```
Error: ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### 🛑 Issue 4: Secret Key Error

```
Error: SECRET_KEY not set
```

**Solution:**
```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env file
SECRET_KEY=<generated-key>
```

## ✅ Pre-Commit Checklist

Before committing code, ensure:

### 📊 Code Quality

```bash
# Run all tests
pytest tests/ -v
# Expected: All tests pass

# Check code coverage
pytest tests/ --cov=app --cov-report=term-missing
# Expected: Coverage > 90%

# Format code (optional, if using black)
black app/ tests/
# Expected: Code formatted

# Lint code (optional, if using flake8)
flake8 app/ tests/
# Expected: No errors
```

### 🔒 Environment

```bash
# Verify .env file is not committed
git status
# Expected: .env should be in .gitignore

# Verify no sensitive data in code
grep -r "SECRET_KEY\|password\|token" app/
# Expected: No hardcoded secrets
```

### 📝 Documentation

```bash
# Update README if needed
# Update CHANGELOG if needed
# Add docstrings to new functions
# Update API documentation if endpoints changed
```

## 🔄 Development Workflow

### 1️⃣ Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2️⃣ Make Changes

```bash
# Edit code
# Add tests
# Update documentation
```

### 3️⃣ Test Changes

```bash
# Run tests
pytest tests/ -v

# Test manually
# Start server and test endpoints
```

### 4️⃣ Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 5️⃣ Push and Create PR

```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **MongoDB Documentation**: https://docs.mongodb.com/
- **Motor Documentation**: https://motor.readthedocs.io/
- **Pytest Documentation**: https://docs.pytest.org/
- **Pydantic Documentation**: https://docs.pydantic.dev/

## 🆘 Getting Help

If you encounter issues:

1. Check this guide
2. Review error messages carefully
3. Check project documentation
4. Search GitHub issues
5. Ask team members
6. Create a new GitHub issue

## 🎉 Summary

### ✅ Setup Checklist

| Task | Status |
|------|--------|
| ✅ Python 3.10+ installed | Complete |
| ✅ MongoDB running (local/Docker/Atlas) | Complete |
| ✅ Virtual environment created & activated | Complete |
| ✅ Dependencies installed | Complete |
| ✅ Environment variables configured | Complete |
| ✅ Server running on http://localhost:8000 | Complete |
| ✅ Tests passing (29/29) | Complete |
| ✅ API documentation accessible | Complete |

### 🚀 You're Ready to Go!

**Server URL:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs  
**Test Coverage:** 91%  
**Test Pass Rate:** 100% (29/29)  

**Happy coding!** 🚀
