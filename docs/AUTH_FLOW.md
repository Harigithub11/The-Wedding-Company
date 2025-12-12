# 🔐 Authentication Flow

## 📋 Overview

The Organization Management Service uses **JWT (JSON Web Token)** authentication with bcrypt password hashing for secure admin authentication.

### 🎯 Authentication Strategy

| Component | Technology | Purpose |
|-----------|------------|----------|
| **🔑 Token Type** | JWT (JSON Web Token) | Stateless authentication |
| **🔒 Password Hashing** | bcrypt (13 rounds) | Secure password storage |
| **⏱️ Token Lifetime** | 24 hours | Balance security/UX |
| **🔐 Algorithm** | HS256 (HMAC-SHA256) | Fast, secure signing |
| **🛡️ Timing Attack Protection** | Constant-time comparison | Prevent password enumeration |

## Complete Authentication Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│                  ADMIN LOGIN FLOW                               │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐                                          ┌──────────┐
│  Client  │                                          │  Server  │
└────┬─────┘                                          └────┬─────┘
     │                                                      │
     │  POST /org/admin/login                              │
     │  {                                                   │
     │    "email": "admin@acme.com",                       │
     │    "password": "SecurePass123"                      │
     │  }                                                   │
     ├─────────────────────────────────────────────────────►│
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 1. Sanitize Input    │
     │                                          │    - Remove XSS      │
     │                                          │    - Trim whitespace │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 2. Lookup Admin      │
     │                                          │    Query:            │
     │                                          │    admins.find({     │
     │                                          │      email: "..."    │
     │                                          │    })                │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                                   Found?
     │                                                      │
     │                                              ┌───────┴───────┐
     │                                              │ Not Found     │
     │                                              └───────┬───────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  401 Unauthorized                                   │
     │  {"detail": "Invalid credentials"}                  │
     │                                                      │
     │                                              ┌───────┴───────┐
     │                                              │ Found         │
     │                                              └───────┬───────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 3. Verify Password   │
     │                                          │    bcrypt.verify(    │
     │                                          │      plain_password, │
     │                                          │      password_hash   │
     │                                          │    )                 │
     │                                          │    Constant-time     │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                                  Valid?
     │                                                      │
     │                                              ┌───────┴───────┐
     │                                              │ Invalid       │
     │                                              └───────┬───────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  401 Unauthorized                                   │
     │  {"detail": "Invalid credentials"}                  │
     │                                                      │
     │                                              ┌───────┴───────┐
     │                                              │ Valid         │
     │                                              └───────┬───────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 4. Update last_login │
     │                                          │    admins.update({   │
     │                                          │      last_login: now │
     │                                          │    })                │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 5. Generate JWT      │
     │                                          │    Payload:          │
     │                                          │    {                 │
     │                                          │      admin_id,       │
     │                                          │      organization_id,│
     │                                          │      email,          │
     │                                          │      type: "admin",  │
     │                                          │      jti: uuid,      │
     │                                          │      exp: now+24h,   │
     │                                          │      iat: now        │
     │                                          │    }                 │
     │                                          │    Sign with SECRET  │
     │                                          └───────────┬──────────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  200 OK                                             │
     │  {                                                   │
     │    "access_token": "eyJhbGc...",                    │
     │    "token_type": "bearer",                          │
     │    "expires_in": 86400                              │
     │  }                                                   │
     │                                                      │
┌────┴─────┐                                          ┌────┴─────┐
│  Client  │                                          │  Server  │
│  Stores  │                                          │          │
│  Token   │                                          │          │
└──────────┘                                          └──────────┘
```

## 🎫 JWT Token Structure

### 📝 Token Format

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZG1pbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMSIsIm9yZ2FuaXphdGlvbl9pZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMCIsImVtYWlsIjoiYWRtaW5AYWNtZS5jb20iLCJ0eXBlIjoiYWRtaW4iLCJqdGkiOiJhYmMxMjMiLCJleHAiOjE3MDI0NzQ4MDAsImlhdCI6MTcwMjM4ODQwMH0.signature

├─ Header (Base64)
│  {
│    "alg": "HS256",
│    "typ": "JWT"
│  }
│
├─ Payload (Base64)
│  {
│    "admin_id": "507f1f77bcf86cd799439011",
│    "organization_id": "507f1f77bcf86cd799439010",
│    "email": "admin@acme.com",
│    "type": "admin",
│    "jti": "abc123",
│    "exp": 1702474800,
│    "iat": 1702388400
│  }
│
└─ Signature (HMAC-SHA256)
   HMACSHA256(
     base64UrlEncode(header) + "." + base64UrlEncode(payload),
     SECRET_KEY
   )
```

### Token Claims

| Claim | Type | Description | Example |
|-------|------|-------------|---------|
| `admin_id` | string | Admin user ID | `"507f1f77bcf86cd799439011"` |
| `organization_id` | string | Organization ID | `"507f1f77bcf86cd799439010"` |
| `email` | string | Admin email | `"admin@acme.com"` |
| `type` | string | Token type | `"admin"` |
| `jti` | string | JWT ID (unique) | `"abc123-def456"` |
| `exp` | int | Expiration time | `1702474800` |
| `iat` | int | Issued at time | `1702388400` |

### Token Generation

```python
from jose import jwt
from datetime import datetime, timedelta
import uuid

def create_token_for_admin(admin_doc: dict) -> str:
    """
    Generate JWT token for authenticated admin.
    """
    # Calculate expiration
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # Create payload
    payload = {
        "admin_id": str(admin_doc["_id"]),
        "organization_id": str(admin_doc["organization_id"]),
        "email": admin_doc["email"],
        "type": "admin",
        "jti": str(uuid.uuid4()),  # Unique token ID
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    # Sign token
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM  # HS256
    )
    
    return token
```

## 🔓 Request Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│           AUTHENTICATED REQUEST FLOW                            │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐                                          ┌──────────┐
│  Client  │                                          │  Server  │
└────┬─────┘                                          └────┬─────┘
     │                                                      │
     │  PUT /org/update                                    │
     │  Authorization: Bearer eyJhbGc...                   │
     │  {                                                   │
     │    "organization_name": "new_name"                  │
     │  }                                                   │
     ├─────────────────────────────────────────────────────►│
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 1. Extract Token     │
     │                                          │    header = request  │
     │                                          │      .headers.get(   │
     │                                          │        "Authorization"│
     │                                          │      )               │
     │                                          │    token = header    │
     │                                          │      .split(" ")[1]  │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 2. Decode & Verify   │
     │                                          │    jwt.decode(       │
     │                                          │      token,          │
     │                                          │      SECRET_KEY,     │
     │                                          │      algorithms=["HS256"]│
     │                                          │    )                 │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                                  Valid?
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Invalid Signature    │
     │                                          └───────────┬──────────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  401 Unauthorized                                   │
     │  {"detail": "Could not validate credentials"}       │
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Valid Signature      │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 3. Check Expiration  │
     │                                          │    if now > exp:     │
     │                                          │      raise Expired   │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                                  Expired?
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Token Expired        │
     │                                          └───────────┬──────────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  401 Unauthorized                                   │
     │  {"detail": "Token has expired"}                    │
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Not Expired          │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 4. Extract Claims    │
     │                                          │    current_user =    │
     │                                          │      TokenData(      │
     │                                          │        admin_id,     │
     │                                          │        org_id,       │
     │                                          │        email         │
     │                                          │      )               │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 5. Verify Access     │
     │                                          │    Check org         │
     │                                          │    ownership         │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                                  Authorized?
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Not Authorized       │
     │                                          └───────────┬──────────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  403 Forbidden                                      │
     │  {"detail": "Access denied"}                        │
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ Authorized           │
     │                                          └───────────┬──────────┘
     │                                                      │
     │                                          ┌───────────┴──────────┐
     │                                          │ 6. Execute Request   │
     │                                          │    Update org...     │
     │                                          └───────────┬──────────┘
     │                                                      │
     │  ◄─────────────────────────────────────────────────┤
     │  200 OK                                             │
     │  {                                                   │
     │    "message": "Organization updated successfully"   │
     │  }                                                   │
     │                                                      │
┌────┴─────┐                                          ┌────┴─────┐
│  Client  │                                          │  Server  │
└──────────┘                                          └──────────┘
```

## 🔒 Password Security

### 🛡️ Bcrypt Hashing

```python
from passlib.context import CryptContext

# Initialize bcrypt context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    """
    Hash password using bcrypt with 13 rounds.
    
    Security features:
    - Automatic salt generation
    - 13 rounds (2^13 iterations)
    - Resistant to rainbow tables
    - Resistant to GPU attacks
    """
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password using constant-time comparison.
    
    Security features:
    - Constant-time comparison (timing attack prevention)
    - Automatic salt extraction
    - Secure comparison
    """
    return pwd_context.verify(plain_password, hashed_password)
```

### Password Hashing Flow

```
Plain Password: "SecurePass123"
    │
    ├─► Generate Salt (random)
    │   Salt: "$2b$13$abcdefghijklmnopqrstuv"
    │
    ├─► Hash with bcrypt (13 rounds)
    │   Iterations: 2^13 = 8,192
    │
    └─► Hashed Password
        "$2b$13$abcdefghijklmnopqrstuv.wxyzABCDEFGHIJKLMNOPQRSTU"
        
        Format:
        $2b$     - bcrypt identifier
        13$      - cost factor (rounds)
        abcd...  - salt (22 chars)
        wxyz...  - hash (31 chars)
```

## ❌ Token Rejection Reasons

### 1️⃣ Missing Token

```http
Request:
PUT /org/update
# No Authorization header

Response:
401 Unauthorized
{
  "detail": "Not authenticated"
}
```

### 2️⃣ Invalid Format

```http
Request:
PUT /org/update
Authorization: InvalidFormat

Response:
401 Unauthorized
{
  "detail": "Could not validate credentials"
}
```

### 3️⃣ Invalid Signature

```http
Request:
PUT /org/update
Authorization: Bearer eyJhbGc...TAMPERED

Response:
401 Unauthorized
{
  "detail": "Could not validate credentials"
}

Reason: Token signature doesn't match
```

### 4️⃣ Expired Token

```http
Request:
PUT /org/update
Authorization: Bearer eyJhbGc...EXPIRED

Response:
401 Unauthorized
{
  "detail": "Token has expired"
}

Reason: Current time > exp claim
```

### 5. Future Token (IAT Check)

```http
Request:
PUT /org/update
Authorization: Bearer eyJhbGc...FUTURE

Response:
401 Unauthorized
{
  "detail": "Token not yet valid"
}

Reason: iat (issued at) is in the future
```

### 6. Algorithm Confusion

```http
Request:
PUT /org/update
Authorization: Bearer eyJhbGc:none...

Response:
401 Unauthorized
{
  "detail": "Could not validate credentials"
}

Reason: Algorithm mismatch (expected HS256)
```

## ⚙️ Middleware Implementation

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Validate JWT token and extract user data.
    
    Raises:
        HTTPException 401: Invalid or expired token
    """
    token = credentials.credentials
    
    try:
        # Decode and verify token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract claims
        admin_id = payload.get("admin_id")
        organization_id = payload.get("organization_id")
        email = payload.get("email")
        
        if not admin_id or not organization_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Return user data
        return TokenData(
            admin_id=admin_id,
            organization_id=organization_id,
            email=email
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

## 🛡️ Security Best Practices

### 🔑 1. Secret Key Management

```python
# ❌ Bad: Hardcoded secret
SECRET_KEY = "my-secret-key"

# ✅ Good: Environment variable
SECRET_KEY = os.getenv("SECRET_KEY")

# ✅ Better: Generate strong secret
import secrets
SECRET_KEY = secrets.token_urlsafe(32)
```

### ⏱️ 2. Token Expiration

```python
# Short-lived tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Refresh tokens (future)
REFRESH_TOKEN_EXPIRE_DAYS = 30
```

### 🔒 3. HTTPS Only

```python
# Production: Require HTTPS
if not request.url.scheme == "https":
    raise HTTPException(401, "HTTPS required")
```

### 🚦 4. Rate Limiting (Future)

```python
# Limit login attempts
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes
```

## 📊 Summary

### ✨ Security Features

| Feature | Implementation | Benefit |
|---------|----------------|----------|
| ✅ **Password Hashing** | bcrypt (13 rounds, auto-salt) | Rainbow table & GPU attack resistance |
| ✅ **JWT Authentication** | HS256, stateless tokens | Scalable, no session storage needed |
| ✅ **Timing Attack Protection** | Constant-time comparison | Prevents password enumeration |
| ✅ **Token Expiration** | 24-hour lifetime | Balance security & UX |
| ✅ **Comprehensive Validation** | Signature, expiration, claims | Multi-layer security |
| ✅ **Error Messages** | Generic responses | No information leakage |
| ✅ **Organization Isolation** | org_id in token | Tenant separation |

### 🛡️ Attack Prevention

| Attack Type | Prevention Mechanism |
|-------------|----------------------|
| **Password Cracking** | bcrypt with 13 rounds (8,192 iterations) |
| **Rainbow Tables** | Automatic salt generation per password |
| **Timing Attacks** | Constant-time password comparison |
| **Token Forgery** | HMAC-SHA256 signature verification |
| **Token Replay** | JTI (token ID) for future revocation |
| **Information Leakage** | Generic error messages for auth failures |
| **Brute Force** | Rate limiting (future implementation) |
