import os
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "geoshop_engine")

# Global database connection
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_database() -> Database:
    """Get MongoDB database instance."""
    global _client, _db

    if _db is None:
        try:
            _client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            _db = _client[DATABASE_NAME]

            # Test connection
            _db.command('ping')
            print("✅ Connected to MongoDB Atlas")

        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("⚠️  Running in offline/mock mode")
            raise

    return _db


def close_database():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        print("✅ MongoDB connection closed")


def init_database():
    """Initialize database connection and collections."""
    try:
        db = get_database()
        init_collections()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print("(This is normal if MongoDB is not running yet)")
        return False


def init_collections():
    """Initialize collections and indexes."""
    try:
        db = get_database()

        # Create collections if they don't exist
        collections = ['shops', 'sync_logs']

        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                print(f"✅ Created collection: {collection_name}")

        # Create indexes for shops collection
        shops_collection = db.shops
        shops_collection.create_index([("name", 1)])
        shops_collection.create_index([("address", 1)])
        shops_collection.create_index([("lat", 1), ("lng", 1)])
        shops_collection.create_index([("sources", 1)])
        shops_collection.create_index([("confidence_score", -1)])
        shops_collection.create_index([("is_active", 1)])
        shops_collection.create_index([("last_updated", -1)])

        # Create indexes for sync_logs collection
        sync_logs_collection = db.sync_logs
        sync_logs_collection.create_index([("run_id", 1)], unique=True)
        sync_logs_collection.create_index([("started_at", -1)])

        print("✅ Database indexes created")
        return True

    except Exception as e:
        print(f"⚠️  Failed to initialize collections: {e}")
        return False


# Remove automatic initialization on import - let FastAPI handle it
# try:
#     init_collections()
# except Exception as e:
#     print(f"⚠️  Database initialization warning: {e}")
#     print("   (This is normal if MongoDB is not running yet)")
