# Organization Management Service

A multi-tenant backend service for managing organizations with JWT-based authentication, built with FastAPI and MongoDB.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Architecture](#architecture)

## 🎯 Overview

This service provides a RESTful API for managing organizations in a multi-tenant architecture. Each organization gets its own MongoDB collection for data isolation, while a Master Database maintains global metadata and authentication information.

## ✨ Features

- ✅ Organization CRUD operations
- ✅ Dynamic MongoDB collection creation per organization
- ✅ JWT-based authentication
- ✅ Bcrypt password hashing
- ✅ Admin user management
- ✅ Multi-tenant architecture (collection-per-tenant)
- ✅ RESTful API design
- ✅ Automatic API documentation (Swagger UI)
- ✅ Class-based modular design
- ✅ Async/await for high performance

## 🛠️ Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **FastAPI** | Web framework | 0.104.1 |
| **MongoDB** | Database | 6.0+ |
| **Motor** | Async MongoDB driver | 3.3.2 |
| **Pydantic** | Data validation | 2.5.0 |
| **PyJWT** | JWT authentication | 3.3.0 |
| **Passlib** | Password hashing | 1.7.4 |
| **Uvicorn** | ASGI server | 0.24.0 |
| **Pytest** | Testing | 7.4.3 |

## 📁 Project Structure

```
organization-management-service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   │
│   ├── core/                        # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                # Settings & environment variables
│   │   ├── database.py              # MongoDB connection manager
│   │   └── security.py              # JWT & password hashing utilities
│   │
│   ├── models/                      # Database models (to be implemented)
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   └── admin.py
│   │
│   ├── schemas/                     # Pydantic schemas (to be implemented)
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   ├── admin.py
│   │   └── token.py
│   │
│   ├── services/                    # Business logic (to be implemented)
│   │   ├── __init__.py
│   │   ├── organization_service.py
│   │   ├── admin_service.py
│   │   └── collection_service.py
│   │
│   ├── routers/                     # API routes (to be implemented)
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   └── admin.py
│   │
│   ├── middleware/                  # Custom middleware
│   │   ├── __init__.py
│   │   └── error_handler.py
│   │
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       └── validators.py
│
├── tests/                           # Test suite
│   └── __init__.py
│
├── docs/                            # Documentation
│
├── .env                             # Environment variables (not in git)
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── test_connection.py               # MongoDB connection test script
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MongoDB (local installation OR MongoDB Atlas account)
- Git

### Step 1: Clone the Repository

```bash
cd organization-management-service
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup MongoDB

Choose one of the following options:

#### Option A: Local MongoDB (Windows)

1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install and run MongoDB as a service
3. MongoDB will run at `mongodb://localhost:27017`

#### Option B: Local MongoDB (Mac)

```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Option C: Local MongoDB (Linux/Ubuntu)

```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option D: MongoDB Atlas (FREE Tier - Recommended)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a free account
3. Create a new cluster (M0 - FREE tier)
4. Create a database user
5. Whitelist your IP (use `0.0.0.0/0` for development)
6. Get your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/
   ```
7. Update `.env` file with this connection string

#### Option E: Docker

```bash
# Start MongoDB in Docker
docker run -d --name mongodb -p 27017:27017 mongo:6.0
```

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your MongoDB connection details
# For local MongoDB, the default settings should work
# For MongoDB Atlas, update MONGODB_URL with your connection string
```

Example `.env` file:

```env
# Environment
ENVIRONMENT=development
DEBUG=True

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=org_management

# JWT Configuration
SECRET_KEY=change-this-to-a-secure-random-string-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=DEBUG
```

### Step 6: Verify Setup

Run the connection test script:

```bash
python test_connection.py
```

This will verify:
- All dependencies are installed
- MongoDB connection is working
- Environment variables are configured

## 🎮 Running the Application

### Development Mode (with auto-reload)

```bash
uvicorn app.main:app --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Using Python directly

```bash
python -m app.main
```

The application will start at: `http://localhost:8000`

## 📚 API Documentation

Once the application is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### API Endpoints (To Be Implemented)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/org/create` | Create new organization | No |
| GET | `/org/get` | Get organization by name | No |
| PUT | `/org/update` | Update organization | Yes |
| DELETE | `/org/delete` | Delete organization | Yes |
| POST | `/admin/login` | Admin login | No |

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_organization.py

# Run with verbose output
pytest -v
```

## 🏗️ Architecture

### Database Design

**Master Database Collections:**
- `organizations` - Organization metadata and collection names
- `admins` - Admin user credentials (hashed passwords)

**Dynamic Collections:**
- `org_<organization_name>` - One collection per organization for data isolation

### Security

- **Password Hashing**: Bcrypt with 12 rounds
- **JWT Tokens**: HS256 algorithm, 24-hour expiration
- **Authentication**: Bearer token in Authorization header

### Design Patterns

- **Singleton**: Database connection manager
- **Dependency Injection**: FastAPI dependencies for auth
- **Service Layer**: Business logic separated from routes
- **Repository Pattern**: Data access layer abstraction

## 🐛 Troubleshooting

### MongoDB Connection Issues

**Error: "Connection refused"**
- Ensure MongoDB is running
- Check if MongoDB is listening on the correct port
- Verify firewall settings

**Error: "Authentication failed"**
- Check MongoDB Atlas username/password
- Verify connection string format
- Ensure IP is whitelisted in Atlas

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>
```

## 📝 Development Notes

### Current Status: Phase 1 Complete ✅

- [x] Project structure created
- [x] Dependencies installed
- [x] MongoDB connection manager implemented
- [x] Configuration system setup
- [x] Security utilities (JWT & password hashing)
- [x] FastAPI application initialized
- [ ] Models implementation (Phase 2)
- [ ] API endpoints (Phase 4)
- [ ] Testing suite (Phase 6)

### Next Steps

1. Implement database models
2. Create Pydantic schemas
3. Build service layer
4. Develop API endpoints
5. Write comprehensive tests

## 📄 License

This project is developed as part of a coding assignment for The Wedding Company.

## 👤 Author

Backend Developer Intern Candidate

---

**Last Updated**: 2025-12-11
**Version**: 1.0.0
**Status**: Phase 1 Complete - Ready for Development
