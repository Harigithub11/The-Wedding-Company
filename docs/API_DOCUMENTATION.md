# API Documentation

Complete REST API reference for the Organization Management Service. All endpoints return JSON responses and follow RESTful conventions.

## 🌐 Base URLs

| Environment | URL | Description |
|-------------|-----|-------------|
| **Development** | `http://localhost:8000` | Local development server |
| **Staging** | `https://staging-api.yourcompany.com` | Testing environment |
| **Production** | `https://api.yourcompany.com` | Live production API |

## 🔒 Authentication

Most endpoints require JWT authentication. Include the token in the `Authorization` header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting a Token

1. Call `POST /org/admin/login` with valid credentials
2. Extract the `access_token` from the response
3. Include it in subsequent requests

### Token Lifetime

- **Expiration:** 24 hours (1440 minutes)
- **Refresh:** Re-login after expiration
- **Revocation:** Not currently supported (planned feature)

## 📦 Common Response Codes

| Code | Status | Meaning |
|------|--------|----------|
| **200** | OK | Request successful |
| **201** | Created | Resource created successfully |
| **400** | Bad Request | Invalid input or business rule violation |
| **401** | Unauthorized | Missing or invalid authentication |
| **403** | Forbidden | Authenticated but not authorized |
| **404** | Not Found | Resource doesn't exist |
| **409** | Conflict | Resource already exists or conflict |
| **422** | Unprocessable Entity | Validation error |
| **500** | Internal Server Error | Server-side error |

## 📚 Endpoint Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/org/create` | ❌ No | Create a new organization |
| POST | `/org/admin/login` | ❌ No | Authenticate and get JWT token |
| GET | `/org/get` | ❌ No | Retrieve organization details |
| PUT | `/org/update` | ✅ Yes | Update organization (with migration) |
| DELETE | `/org/delete` | ✅ Yes | Delete organization and all data |

---

## 📡 API Endpoints

---

### 1️⃣ Create Organization

Create a new organization with an admin user. This endpoint performs multiple actions atomically:
- Creates organization metadata
- Hashes and stores admin credentials
- Creates a dynamic MongoDB collection for the organization

#### Endpoint Details

```http
POST /org/create
```

**Authentication:** ❌ Not required (public registration)

#### Request Body

```json
{
  "organization_name": "string",
  "email": "string",
  "password": "string"
}
```

**Field Specifications:**

| Field | Type | Requirements | Example |
|-------|------|--------------|----------|
| `organization_name` | string | 3-50 chars, alphanumeric + `_` `-` | `acme_corp` |
| `email` | string | Valid email format | `admin@acme.com` |
| `password` | string | Min 8 chars, 1 uppercase, 1 lowercase, 1 number | `SecurePass123` |

**Response:** `201 Created`
```json
{
  "message": "Organization created successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "acme_corp",
    "collection_name": "org_acme_corp",
    "admin_email": "admin@acme.com",
    "created_at": "2025-12-12T00:00:00Z",
    "updated_at": "2025-12-12T00:00:00Z"
  },
  "admin_id": "507f1f77bcf86cd799439012"
}
```

**Error Responses:**

`400 Bad Request` - Organization name already exists
```json
{
  "detail": "Organization 'acme_corp' already exists"
}
```

`422 Unprocessable Entity` - Validation error
```json
{
  "detail": "Invalid email format"
}
```

`500 Internal Server Error` - Server error
```json
{
  "detail": "Failed to create organization. Please try again later."
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme_corp",
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

**Notes:**
- Organization name is converted to lowercase and sanitized
- Password is hashed using bcrypt before storage
- A dynamic MongoDB collection is created for the organization
- Admin user is created and linked to the organization

---

### 2️⃣ Admin Login

Authenticate an admin user and receive a JWT access token for subsequent API calls.

#### Endpoint Details

```http
POST /org/admin/login
```

**Authentication:** ❌ Not required (authentication endpoint)

#### Request Body

```json
{
  "email": "string",
  "password": "string"
}
```

**Field Specifications:**

| Field | Type | Requirements | Example |
|-------|------|--------------|----------|
| `email` | string | Valid registered email | `admin@acme.com` |
| `password` | string | Correct password | `SecurePass123` |

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error Responses:**

`401 Unauthorized` - Invalid credentials
```json
{
  "detail": "Invalid credentials"
}
```

`500 Internal Server Error` - Server error
```json
{
  "detail": "Failed to process login. Please try again later."
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123"
  }'
```

**JWT Token Contents:**
```json
{
  "admin_id": "507f1f77bcf86cd799439012",
  "organization_id": "507f1f77bcf86cd799439011",
  "email": "admin@acme.com",
  "type": "admin",
  "jti": "unique-jwt-id",
  "exp": 1702474800,
  "iat": 1702388400
}
```

**Notes:**
- Token expires after 24 hours (configurable)
- Use the access_token in subsequent requests
- Last login timestamp is updated automatically
- Failed login attempts are logged for security

---

### 3. Get Organization

Retrieve organization details by name.

**Endpoint:** `GET /org/get`

**Authentication:** None (public)

**Query Parameters:**
- `organization_name` (required): Organization name to retrieve

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "organization_name": "acme_corp",
  "collection_name": "org_acme_corp",
  "admin_email": "admin@acme.com",
  "created_at": "2025-12-12T00:00:00Z",
  "updated_at": "2025-12-12T00:00:00Z"
}
```

**Error Responses:**

`404 Not Found` - Organization doesn't exist
```json
{
  "detail": "Organization 'nonexistent_org' not found"
}
```

`422 Unprocessable Entity` - Validation error
```json
{
  "detail": "Organization name must be between 3 and 50 characters"
}
```

`500 Internal Server Error` - Server error
```json
{
  "detail": "Failed to retrieve organization. Please try again later."
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/org/get?organization_name=acme_corp"
```

**Notes:**
- Sensitive data (passwords, internal IDs) are excluded
- Organization name is case-insensitive
- Returns admin email for contact purposes

---

### 4. Update Organization

Update organization name and/or admin credentials with atomic migration.

**Endpoint:** `PUT /org/update`

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "organization_name": "string (optional, 3-50 chars)",
  "email": "string (optional, valid email)",
  "password": "string (optional, min 8 chars)"
}
```

**Response:** `200 OK`
```json
{
  "message": "Organization updated successfully",
  "organization": {
    "id": "507f1f77bcf86cd799439011",
    "organization_name": "acme_corporation",
    "collection_name": "org_acme_corporation",
    "admin_email": "newemail@acme.com",
    "created_at": "2025-12-12T00:00:00Z",
    "updated_at": "2025-12-12T01:00:00Z"
  }
}
```

**Error Responses:**

`400 Bad Request` - New organization name already exists
```json
{
  "detail": "Organization name 'acme_corporation' already exists"
}
```

`401 Unauthorized` - Missing or invalid JWT
```json
{
  "detail": "Could not validate credentials"
}
```

`403 Forbidden` - User doesn't own this organization
```json
{
  "detail": "You do not have access to this organization"
}
```

`404 Not Found` - Organization not found
```json
{
  "detail": "Organization not found"
}
```

`409 Conflict` - Migration failed
```json
{
  "detail": "Failed to migrate organization data: <error details>"
}
```

`422 Unprocessable Entity` - Validation error
```json
{
  "detail": "Invalid email format"
}
```

`500 Internal Server Error` - Server error
```json
{
  "detail": "Failed to update organization. Please try again later."
}
```

**cURL Example:**
```bash
# Get token first
TOKEN=$(curl -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"SecurePass123"}' \
  | jq -r '.access_token')

# Update organization
curl -X PUT "http://localhost:8000/org/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "organization_name": "acme_corporation",
    "email": "newemail@acme.com",
    "password": "NewSecurePass456"
  }'
```

**Atomic Migration Process:**

When changing organization name:
1. Create new collection (`org_acme_corporation`)
2. Migrate all documents from old to new collection
3. Update organization metadata
4. Delete old collection (`org_acme_corp`)

**Rollback on Failure:**
- New collection is deleted
- Old metadata is restored
- Old collection is recreated if missing
- HTTP 409 is returned

**Notes:**
- All fields are optional (update only what you provide)
- Password is re-hashed if updated
- Email must be unique across all admins
- Migration is atomic - either all succeed or all rollback
- User must be authenticated as admin of the organization

---

### 5. Delete Organization

Delete an organization and all associated data (cascade delete).

**Endpoint:** `DELETE /org/delete`

**Authentication:** Required (JWT Bearer token)

**Request Body:** None

**Response:** `200 OK`
```json
{
  "message": "Organization 'acme_corp' deleted successfully"
}
```

**Error Responses:**

`401 Unauthorized` - Missing or invalid JWT
```json
{
  "detail": "Could not validate credentials"
}
```

`403 Forbidden` - User doesn't own this organization
```json
{
  "detail": "You do not have access to this organization"
}
```

`404 Not Found` - Organization not found
```json
{
  "detail": "Organization not found"
}
```

`500 Internal Server Error` - Server error
```json
{
  "detail": "Failed to delete organization. Please try again later."
}
```

**cURL Example:**
```bash
# Get token first
TOKEN=$(curl -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"SecurePass123"}' \
  | jq -r '.access_token')

# Delete organization
curl -X DELETE "http://localhost:8000/org/delete" \
  -H "Authorization: Bearer $TOKEN"
```

**Cascade Deletion:**

The following are deleted in order:
1. Organization's dynamic collection (`org_acme_corp`)
2. All admin users associated with the organization
3. Organization document from master database

**Notes:**
- This operation is irreversible
- All organization data is permanently deleted
- Repeated deletion returns 404 (idempotent)
- User must be authenticated as admin of the organization
- Deletion is logged for audit purposes

---

## Common Response Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Duplicate resource, invalid business logic |
| 401 | Unauthorized | Missing/invalid JWT, wrong credentials |
| 403 | Forbidden | Valid JWT but no permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Migration/update conflict |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server/database error |

---

## Rate Limiting

Currently not implemented. Future versions will include:
- 100 requests per minute per user
- 1000 requests per hour per organization

---

## Pagination

Not applicable for current endpoints. Future versions with list endpoints will support:
```
GET /org/list?page=1&limit=20
```

---

## Versioning

API version is included in the response headers:
```
X-API-Version: 1.0.0
```

Future breaking changes will use URL versioning:
```
/v2/org/create
```

---

## Error Response Format

All errors follow this format:
```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), additional details may be included:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Best Practices

### 1. Token Management
```javascript
// Store token securely
localStorage.setItem('token', response.access_token);

// Include in requests
fetch('/org/update', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

// Handle expiration
if (response.status === 401) {
  // Redirect to login
}
```

### 2. Error Handling
```javascript
try {
  const response = await fetch('/org/create', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error(error.detail);
  }
} catch (error) {
  console.error('Network error:', error);
}
```

### 3. Idempotency
- GET requests are naturally idempotent
- POST /org/create is NOT idempotent (creates new resource)
- PUT /org/update is idempotent (same result if called multiple times)
- DELETE /org/delete is idempotent (returns 404 on second call)

---

## Interactive Documentation

Visit these URLs when the server is running:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API testing
  - Try out endpoints
  - See request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Clean, readable documentation
  - Better for reading
  - Printable format

---

## SDK Examples

### Python
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/org/admin/login",
    json={"email": "admin@acme.com", "password": "SecurePass123"}
)
token = response.json()["access_token"]

# Update organization
response = requests.put(
    "http://localhost:8000/org/update",
    headers={"Authorization": f"Bearer {token}"},
    json={"organization_name": "new_name"}
)
print(response.json())
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

// Login
const loginResponse = await axios.post(
  'http://localhost:8000/org/admin/login',
  { email: 'admin@acme.com', password: 'SecurePass123' }
);
const token = loginResponse.data.access_token;

// Update organization
const updateResponse = await axios.put(
  'http://localhost:8000/org/update',
  { organization_name: 'new_name' },
  { headers: { Authorization: `Bearer ${token}` } }
);
console.log(updateResponse.data);
```

### cURL
```bash
# Complete workflow
# 1. Create organization
curl -X POST "http://localhost:8000/org/create" \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"test","email":"admin@test.com","password":"Pass123"}'

# 2. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/org/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"Pass123"}' \
  | jq -r '.access_token')

# 3. Get organization
curl "http://localhost:8000/org/get?organization_name=test"

# 4. Update organization
curl -X PUT "http://localhost:8000/org/update" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"organization_name":"test_updated"}'

# 5. Delete organization
curl -X DELETE "http://localhost:8000/org/delete" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Support

For API support:
- Email: api-support@yourcompany.com
- Documentation: https://docs.yourcompany.com
- Status Page: https://status.yourcompany.com
