#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Helps diagnose MongoDB Atlas connection issues
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

def test_mongodb_connection():
    """Test MongoDB connection and provide troubleshooting."""

    # Load environment variables
    load_dotenv()

    mongodb_url = os.getenv("MONGODB_URL")
    database_name = os.getenv("DATABASE_NAME", "geoshop_engine")

    print("🔍 MongoDB Connection Diagnostic")
    print("=" * 50)

    if not mongodb_url:
        print("❌ ERROR: MONGODB_URL not found in .env file")
        print("\n📋 To fix this:")
        print("1. Go to MongoDB Atlas: https://cloud.mongodb.com")
        print("2. Select your project/cluster")
        print("3. Click 'Connect' → 'Connect your application'")
        print("4. Choose 'Python' and version '3.6+'")
        print("5. Copy the connection string")
        print("6. Replace MONGODB_URL in .env file")
        return False

    print(f"📍 Database URL: {mongodb_url.replace('mongodb+srv://', 'mongodb+srv://[HIDDEN]@')}")
    print(f"📍 Database Name: {database_name}")
    print()

    try:
        print("🔌 Attempting connection...")
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=10000)

        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")

        # Test database access
        db = client[database_name]
        collections = db.list_collection_names()
        print(f"✅ Database access successful!")
        print(f"📊 Available collections: {collections}")

        # Test basic operations
        shops_count = db.shops.count_documents({})
        print(f"📊 Shops collection: {shops_count} documents")

        client.close()
        return True

    except ConnectionFailure as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Possible causes:")
        print("- Wrong connection string")
        print("- Network connectivity issues")
        print("- Firewall blocking connection")
        print("- MongoDB Atlas cluster paused")

    except OperationFailure as e:
        if "bad auth" in str(e).lower():
            print(f"❌ Authentication failed: {e}")
            print("\n🔧 To fix authentication:")
            print("1. Check username/password in connection string")
            print("2. Verify user has correct permissions")
            print("3. Check if user account is active")
            print("4. Try resetting password in MongoDB Atlas")
        else:
            print(f"❌ Database operation failed: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n📋 Quick fix checklist:")
    print("□ MongoDB Atlas cluster is running (not paused)")
    print("□ IP address whitelisted (0.0.0.0/0 for testing)")
    print("□ Database user has read/write permissions")
    print("□ Connection string copied correctly from Atlas")
    print("□ No special characters in password (URL encode if needed)")

    return False

if __name__ == "__main__":
    success = test_mongodb_connection()
    if success:
        print("\n🎉 MongoDB connection is working!")
        print("You can now run: python run_api.py")
    else:
        print("\n⚠️  MongoDB connection failed.")
        print("Fix the issues above before running the API.")