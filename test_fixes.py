"""
Quick test to verify the fixes work correctly.
Tests:
1. POST /org/create - Must not crash with ObjectId(admin_id) error
2. PUT /org/update - Must not crash with AttributeError: 'bool' object has no attribute 'get'
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

print("=" * 70)
print("TESTING SECURITY FIXES")
print("=" * 70)

# Test 1: POST /org/create
print("\n🟢 TEST 1: POST /org/create (Should not crash with ObjectId error)")
print("-" * 70)

create_data = {
    "organization_name": f"TestOrg_{int(time.time())}",
    "email": f"admin_{int(time.time())}@test.com",
    "password": "SecurePassword123!"
}

try:
    response = requests.post(f"{BASE_URL}/org/create", json=create_data)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ SUCCESS: Organization created")
        print(f"   Organization: {result['organization']['organization_name']}")
        print(f"   Admin ID: {result['admin_id']}")
        
        # Save for update test
        org_name = result['organization']['organization_name']
        admin_email = create_data['email']
        admin_password = create_data['password']
    else:
        print(f"❌ FAILED: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

# Test 2: Login to get token
print("\n🔑 Logging in to get token...")
print("-" * 70)

login_data = {
    "email": admin_email,
    "password": admin_password
}

try:
    response = requests.post(f"{BASE_URL}/org/admin/login", json=login_data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        print(f"✅ Login successful")
    else:
        print(f"❌ Login failed: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

# Test 3: PUT /org/update
print("\n🟢 TEST 2: PUT /org/update (Should not crash with 'bool' has no attribute 'get')")
print("-" * 70)

update_data = {
    "organization_name": f"UpdatedOrg_{int(time.time())}"
}

headers = {
    "Authorization": f"Bearer {access_token}"
}

try:
    response = requests.put(f"{BASE_URL}/org/update", json=update_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS: Organization updated")
        print(f"   New Name: {result['organization']['organization_name']}")
    elif response.status_code == 400:
        # Duplicate name is acceptable
        print(f"⚠️ Expected Error (Duplicate Name): {response.json()['detail']}")
    else:
        print(f"❌ FAILED: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - FIXES ARE WORKING CORRECTLY")
print("=" * 70)
print("\nSummary:")
print("✅ Fix 1: admin_id=None handled correctly (no ObjectId crash)")
print("✅ Fix 2: Boolean result checked correctly (no .get() crash)")
