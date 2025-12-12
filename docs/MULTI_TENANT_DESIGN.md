# 🏛️ Multi-Tenant Design

## 📋 Overview

The Organization Management Service uses a **collection-per-tenant** model where each organization gets its own isolated MongoDB collection for storing data.

### 🎯 Design Goals

| Goal | Achievement |
|------|-------------|
| **🔒 Data Isolation** | Complete physical separation per tenant |
| **⚡ Performance** | Fast queries without org_id filtering |
| **🛡️ Security** | Breach containment and access control |
| **📈 Scalability** | Independent sharding and backup |

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                      MONGODB DATABASE                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   MASTER DATABASE                           │ │
│  │              (Shared Metadata & Control Plane)              │ │
│  │                                                             │ │
│  │  ┌──────────────────────┐      ┌──────────────────────┐   │ │
│  │  │  organizations       │      │  admins              │   │ │
│  │  │  ─────────────────   │      │  ─────────────────   │   │ │
│  │  │  _id                 │◄────►│  _id                 │   │ │
│  │  │  organization_name*  │      │  email*              │   │ │
│  │  │  collection_name*    │      │  password_hash       │   │ │
│  │  │  admin_id            │      │  organization_id     │   │ │
│  │  │  created_at          │      │  last_login          │   │ │
│  │  │  updated_at          │      │  created_at          │   │ │
│  │  │                      │      │                      │   │ │
│  │  │  * = unique index    │      │  * = unique index    │   │ │
│  │  └──────────────────────┘      └──────────────────────┘   │ │
│  │                                                             │ │
│  │  Purpose:                                                   │ │
│  │  • Store organization metadata                             │ │
│  │  • Manage admin users                                      │ │
│  │  • Track collection mappings                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │            DYNAMIC TENANT COLLECTIONS                       │ │
│  │              (Isolated Data Plane)                          │ │
│  │                                                             │ │
│  │  ┌──────────────────┐  ┌──────────────────┐               │ │
│  │  │  org_acme_corp   │  │  org_techstart   │               │ │
│  │  │  ──────────────  │  │  ──────────────  │               │ │
│  │  │  {             } │  │  {             } │               │ │
│  │  │  {  user data  } │  │  {  user data  } │               │ │
│  │  │  {  documents  } │  │  {  documents  } │               │ │
│  │  │  {  ...        } │  │  {  ...        } │               │ │
│  │  │                  │  │                  │               │ │
│  │  └──────────────────┘  └──────────────────┘               │ │
│  │                                                             │ │
│  │  ┌──────────────────┐  ┌──────────────────┐               │ │
│  │  │  org_restaurant  │  │  org_...         │               │ │
│  │  │  ──────────────  │  │  ──────────────  │               │ │
│  │  │  {             } │  │  {             } │               │ │
│  │  │  {  user data  } │  │  {  user data  } │               │ │
│  │  │  {  documents  } │  │  {  documents  } │               │ │
│  │  │  {  ...        } │  │  {  ...        } │               │ │
│  │  │                  │  │                  │               │ │
│  │  └──────────────────┘  └──────────────────┘               │ │
│  │                                                             │ │
│  │  Characteristics:                                           │ │
│  │  • Created dynamically on org registration                 │ │
│  │  • Complete data isolation                                 │ │
│  │  • Can have custom schemas                                 │ │
│  │  • Migrated atomically on rename                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## 🏷️ Collection Naming Strategy

### 📝 Naming Convention

```python
# Pattern: org_{sanitized_organization_name}

def to_collection_name(organization_name: str) -> str:
    """
    Convert organization name to safe collection name.
    
    Rules:
    1. Convert to lowercase
    2. Replace spaces with underscores
    3. Remove all non-alphanumeric except underscores
    4. Prefix with 'org_'
    """
    sanitized = organization_name.lower()
    sanitized = sanitized.replace(" ", "_")
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)
    return f"org_{sanitized}"
```

### 📊 Examples

| Organization Name | Collection Name | Valid? |
|-------------------|-----------------|--------|
| `Acme Corp` | `org_acme_corp` | ✅ Yes |
| `Tech-Startup 2024` | `org_techstartup2024` | ✅ Yes |
| `Café & Restaurant` | `org_caf_restaurant` | ✅ Yes |
| `123 Company` | `org_123_company` | ✅ Yes |
| `__test__` | `org___test__` | ✅ Yes |

### Validation Rules

```python
class OrganizationNameValidator:
    @staticmethod
    def validate(name: str) -> str:
        """
        Validate organization name.
        
        Rules:
        - 3-50 characters
        - Alphanumeric, spaces, hyphens, underscores
        - No leading/trailing whitespace
        - Not empty after sanitization
        """
        if not name or len(name.strip()) < 3:
            raise ValueError("Name must be at least 3 characters")
        
        if len(name) > 50:
            raise ValueError("Name must be at most 50 characters")
        
        if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
            raise ValueError("Name contains invalid characters")
        
        return name.strip()
```

## 🤔 Why Collection-Per-Tenant?

### 🎯 Decision Rationale

We chose collection-per-tenant over other multi-tenancy models for the following reasons:

### ✨ Advantages

#### 1. **Complete Data Isolation**

```
Traditional Shared Collection:
┌────────────────────────────┐
│  shared_data               │
│  ┌──────────────────────┐  │
│  │ {org_id: "A", ...}   │  │  ⚠️ Risk: Query bugs expose data
│  │ {org_id: "B", ...}   │  │  ⚠️ Risk: Index on org_id required
│  │ {org_id: "A", ...}   │  │  ⚠️ Risk: Accidental cross-tenant
│  │ {org_id: "C", ...}   │  │
│  └──────────────────────┘  │
└────────────────────────────┘

Collection-Per-Tenant:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ org_a        │  │ org_b        │  │ org_c        │
│ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ {...}    │ │  │ │ {...}    │ │  │ │ {...}    │ │
│ │ {...}    │ │  │ │ {...}    │ │  │ │ {...}    │ │
│ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │
└──────────────┘  └──────────────┘  └──────────────┘
✅ Impossible to query wrong tenant
✅ No org_id filtering needed
✅ Physical separation
```

#### 2. **Security Benefits**

| Benefit | Description |
|---------|-------------|
| **Breach Containment** | If one org's collection is compromised, others remain safe |
| **Access Control** | Collection-level permissions possible |
| **Audit Trail** | Easy to track all access to specific org |
| **Compliance** | Easier GDPR/HIPAA compliance (data deletion, export) |

#### 3. **Performance Benefits**

```
Query Performance:

Shared Collection:
db.shared_data.find({org_id: "A", status: "active"})
├─ Scan entire collection
├─ Filter by org_id (index required)
└─ Filter by status
   Time: O(n) where n = total documents

Collection-Per-Tenant:
db.org_a.find({status: "active"})
├─ Scan only org A's documents
└─ Filter by status
   Time: O(m) where m = org A's documents

Result: Faster queries, smaller indexes
```

#### 4. **Scalability Benefits**

- **Sharding**: Can shard collections independently
- **Backup**: Backup individual organizations
- **Migration**: Move specific orgs to different servers
- **Archival**: Archive inactive orgs easily

#### 5. **Flexibility**

```python
# Each organization can have custom schema
org_acme_corp:
{
  "customer_id": "...",
  "custom_field_1": "...",  # Acme-specific
  "custom_field_2": "..."   # Acme-specific
}

org_techstart:
{
  "user_id": "...",
  "different_field": "...",  # TechStart-specific
  "metadata": {...}          # TechStart-specific
}
```

### ⚠️ Trade-offs & Limitations

#### 📊 1. Collection Limit

| Aspect | Details |
|--------|---------|
| **MongoDB Limit** | ~24,000 collections per database |
| **Practical Limit** | ~10,000 organizations recommended |
| **Mitigation** | Monitor collection count, alert at threshold |

#### 2. **Management Complexity**

```
Challenges:
├─ More collections to monitor
├─ More complex migrations (rename = new collection)
├─ Backup strategy more complex
└─ Need automated monitoring

Solutions:
├─ Automated monitoring scripts
├─ Atomic migration with rollback
├─ Collection-aware backup tools
└─ Admin dashboard for collection health
```

#### 3. **Cross-Tenant Queries**

```
Problem:
Cannot easily query across all organizations

Example:
"Find all users with email domain @example.com across all orgs"

Solution:
├─ Maintain aggregated views in master DB
├─ Use background jobs for analytics
└─ Accept this limitation for security benefits
```

## 🔒 Data Isolation & Security

### 🛡️ Isolation Guarantees

```
┌─────────────────────────────────────────────────────────┐
│              MULTI-LAYER ISOLATION                      │
└─────────────────────────────────────────────────────────┘

Layer 1: Application Layer
├─ JWT contains organization_id
├─ Every request validates org ownership
└─ Services enforce org_id checks

Layer 2: Collection Layer
├─ Each org has separate collection
├─ No shared data structures
└─ Physical separation

Layer 3: Query Layer
├─ Queries target specific collection
├─ No cross-collection joins
└─ Impossible to accidentally query wrong org

Layer 4: Database Layer
├─ Collection-level permissions (future)
├─ Separate backup/restore
└─ Independent sharding
```

### Security Considerations

#### 1. **Collection Name Validation**

```python
# Prevent injection attacks
def validate_collection_name(name: str):
    """
    Ensure collection name is safe.
    
    Prevents:
    - Command injection
    - Path traversal
    - Special characters
    """
    if not re.match(r'^org_[a-z0-9_]+$', name):
        raise ValueError("Invalid collection name")
    
    if len(name) > 100:
        raise ValueError("Collection name too long")
    
    return name
```

#### 2. **Authorization Checks**

```python
async def verify_organization_access(
    current_user: TokenData,
    organization_id: str
):
    """
    Verify user has access to organization.
    
    Prevents:
    - Cross-tenant access
    - Privilege escalation
    - Unauthorized operations
    """
    if current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
```

#### 3. **Collection Existence Checks**

```python
async def ensure_collection_exists(collection_name: str):
    """
    Verify collection exists before operations.
    
    Prevents:
    - Operating on non-existent collections
    - Creating unintended collections
    - Data loss
    """
    collections = await db.list_collection_names()
    if collection_name not in collections:
        raise ValueError(f"Collection {collection_name} does not exist")
```

## Migration Strategy

### Organization Rename Flow

```
┌─────────────────────────────────────────────────────────┐
│          ATOMIC COLLECTION MIGRATION                    │
└─────────────────────────────────────────────────────────┘

Step 1: Create New Collection
├─ db.create_collection("org_new_name")
└─ Status: org_old_name ✅ | org_new_name ✅

Step 2: Migrate Documents
├─ Copy all docs from org_old_name → org_new_name
└─ Status: org_old_name ✅ | org_new_name ✅ (with data)

Step 3: Update Metadata
├─ organizations.update({collection_name: "org_new_name"})
└─ Status: Metadata points to new collection

Step 4: Delete Old Collection
├─ db.drop_collection("org_old_name")
└─ Status: org_new_name ✅ (migration complete)

On Failure (Any Step):
├─ Delete org_new_name
├─ Restore metadata
├─ Ensure org_old_name exists
└─ Raise HTTP 409
```

## Monitoring & Limits

### Collection Count Monitoring

```python
async def monitor_collection_count():
    """
    Monitor collection count and alert if approaching limit.
    """
    collections = await db.list_collection_names()
    org_collections = [c for c in collections if c.startswith("org_")]
    
    count = len(org_collections)
    limit = 10000  # Recommended limit
    
    if count > limit * 0.8:  # 80% threshold
        logger.warning(f"Collection count: {count}/{limit}")
        # Send alert
    
    return count
```

### Health Checks

```python
async def check_collection_health(collection_name: str):
    """
    Verify collection health.
    """
    collection = db[collection_name]
    
    # Check document count
    doc_count = await collection.count_documents({})
    
    # Check indexes
    indexes = await collection.index_information()
    
    # Check size
    stats = await db.command("collStats", collection_name)
    size_mb = stats["size"] / (1024 * 1024)
    
    return {
        "collection": collection_name,
        "documents": doc_count,
        "indexes": len(indexes),
        "size_mb": size_mb,
        "healthy": True
    }
```

## 📊 Summary

### ✨ Key Benefits

| Benefit | Impact |
|---------|--------|
| ✅ **Complete Data Isolation** | Physical separation prevents cross-tenant access |
| ✅ **Enhanced Security** | Breach containment and access control |
| ✅ **Better Performance** | Faster queries without org_id filtering |
| ✅ **Flexible Schemas** | Per-tenant customization possible |
| ✅ **Easy Compliance** | GDPR/HIPAA data deletion and export |
| ✅ **Independent Scaling** | Shard, backup, migrate per organization |

### ⚠️ Acceptable Trade-offs

| Trade-off | Mitigation |
|-----------|------------|
| **Collection Limit** | Monitor count, alert at 80% threshold (~10K orgs) |
| **Migration Complexity** | Atomic operations with comprehensive rollback |
| **Management Overhead** | Automated monitoring and health checks |
| **Cross-Tenant Queries** | Aggregated views in master DB, background jobs |

### 🎯 Ideal Use Case

This design is **perfect** for:
- 🏢 **SaaS Applications** requiring strong tenant isolation
- 🏛️ **Enterprise Systems** with compliance requirements
- 📦 **Multi-Tenant Platforms** with varying data schemas
- 🔒 **High-Security Environments** needing breach containment
