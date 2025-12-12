"""
Test script to verify MongoDB connection and application setup.
Run this to ensure everything is configured correctly.
"""

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


async def test_mongodb_connection():
    """Test MongoDB connection."""
    print("=" * 60)
    print("Testing MongoDB Connection")
    print("=" * 60)

    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME")

    print(f"\nMongoDB URL: {mongodb_url}")
    print(f"Database Name: {database_name}")

    try:
        print("\n1. Creating MongoDB client...")
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=5000
        )

        print("2. Testing connection (ping)...")
        await client.admin.command("ping")
        print("   [OK] Connection successful!")

        print("3. Accessing database...")
        db = client[database_name]
        print(f"   [OK] Database '{database_name}' accessed")

        print("4. Listing collections...")
        collections = await db.list_collection_names()
        if collections:
            print(f"   [OK] Existing collections: {', '.join(collections)}")
        else:
            print("   [OK] No collections yet (fresh database)")

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed! MongoDB is ready.")
        print("=" * 60)

        client.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print("\n" + "=" * 60)
        print("MongoDB Connection Failed!")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Is MongoDB running locally?")
        print("   - Windows: Check Services for 'MongoDB Server'")
        print("   - Mac/Linux: Run 'sudo systemctl status mongod'")
        print("\n2. Using MongoDB Atlas?")
        print("   - Verify connection string in .env file")
        print("   - Check IP whitelist (use 0.0.0.0/0 for development)")
        print("   - Verify username/password")
        print("\n3. Check .env file configuration")
        print("=" * 60)
        return False


async def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    modules_to_test = [
        ("FastAPI", "fastapi"),
        ("Motor (MongoDB)", "motor.motor_asyncio"),
        ("JWT", "jose.jwt"),
        ("Passlib (Password Hashing)", "passlib.context"),
        ("Pydantic", "pydantic"),
        ("Python-dotenv", "dotenv"),
    ]

    all_passed = True
    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"[OK] {name}")
        except ImportError as e:
            print(f"[FAIL] {name} - {e}")
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All dependencies installed correctly!")
    else:
        print("\n[ERROR] Some dependencies are missing. Run: pip install -r requirements.txt")

    print("=" * 60)
    return all_passed


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Organization Management Service - Setup Verification")
    print("=" * 60 + "\n")

    # Test imports
    imports_ok = await test_imports()

    if not imports_ok:
        print("\n[ERROR] Please install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    # Test MongoDB connection
    connection_ok = await test_mongodb_connection()

    if connection_ok:
        print("\n[SUCCESS] Setup Complete! You can now run the application:")
        print("   uvicorn app.main:app --reload")
        print("\n[INFO] API Documentation will be available at:")
        print("   http://localhost:8000/docs")
        sys.exit(0)
    else:
        print("\n[ERROR] Please setup MongoDB before running the application.")
        print("\nQuick Options:")
        print("1. Install MongoDB locally")
        print("2. Use MongoDB Atlas (free tier)")
        print("3. Use Docker: docker-compose up -d")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
