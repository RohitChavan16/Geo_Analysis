from datetime import datetime
from typing import List, Optional, Dict, Any
from db.database import get_database
from db.models import ShopDocument, SyncLogDocument, ShopResponse
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
import uuid


# ============ Shop CRUD Operations ============

def create_shop(shop_data: Dict[str, Any]) -> Optional[str]:
    """Create a new shop document."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        # Create shop document
        shop_doc = ShopDocument(**shop_data)
        result = shops_collection.insert_one(shop_doc.dict(by_alias=True))
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error creating shop: {e}")
        return None


def get_shop(shop_id: str) -> Optional[Dict[str, Any]]:
    """Get a shop by ID."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        shop = shops_collection.find_one({"_id": shop_id})
        return shop
    except Exception as e:
        print(f"Error getting shop: {e}")
        return None


def get_shops_by_name(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get shops by name (partial match)."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        shops = list(shops_collection.find(
            {"name": {"$regex": name, "$options": "i"}, "is_active": True}
        ).limit(limit))
        return shops
    except Exception as e:
        print(f"Error getting shops by name: {e}")
        return []


def get_shops_by_location(lat: float, lng: float, radius_km: float = 1.0) -> List[Dict[str, Any]]:
    """Get shops near a location (simple distance calculation)."""
    db = get_database()
    shops_collection: Collection = db.shops

    # Rough approximation: 1 degree ≈ 111 km
    delta = radius_km / 111.0

    try:
        shops = list(shops_collection.find({
            "lat": {"$gte": lat - delta, "$lte": lat + delta},
            "lng": {"$gte": lng - delta, "$lte": lng + delta},
            "is_active": True
        }))
        return shops
    except Exception as e:
        print(f"Error getting shops by location: {e}")
        return []


def get_high_confidence_shops(min_confidence: float = 70.0, limit: int = 100) -> List[Dict[str, Any]]:
    """Get shops with high confidence scores."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        shops = list(shops_collection.find(
            {"confidence_score": {"$gte": min_confidence}, "is_active": True}
        ).sort("confidence_score", -1).limit(limit))
        return shops
    except Exception as e:
        print(f"Error getting high confidence shops: {e}")
        return []


def get_shops_by_source(source: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get shops from a specific source."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        shops = list(shops_collection.find(
            {"sources": source, "is_active": True}
        ).limit(limit))
        return shops
    except Exception as e:
        print(f"Error getting shops by source: {e}")
        return []


def update_shop(shop_id: str, shop_data: Dict[str, Any]) -> bool:
    """Update a shop document."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        # Add last_updated timestamp
        shop_data["last_updated"] = datetime.utcnow()

        result = shops_collection.update_one(
            {"_id": shop_id},
            {"$set": shop_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating shop: {e}")
        return False


def mark_as_duplicate(shop_id: str) -> bool:
    """Mark a shop as duplicate."""
    return update_shop(shop_id, {"is_duplicate": True, "is_active": False})


def delete_shop(shop_id: str) -> bool:
    """Soft delete a shop (mark inactive)."""
    return update_shop(shop_id, {"is_active": False})


def verify_shop(shop_id: str) -> bool:
    """Mark a shop as recently verified."""
    return update_shop(shop_id, {"last_verified": datetime.utcnow()})


def get_all_active_shops(limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all active shops with pagination."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        shops = list(shops_collection.find({"is_active": True})
                    .skip(offset)
                    .limit(limit)
                    .sort("last_updated", -1))
        return shops
    except Exception as e:
        print(f"Error getting active shops: {e}")
        return []


def count_shops(active_only: bool = True) -> int:
    """Count total shops."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        if active_only:
            return shops_collection.count_documents({"is_active": True})
        else:
            return shops_collection.count_documents({})
    except Exception as e:
        print(f"Error counting shops: {e}")
        return 0


def find_similar_shops(name: str, lat: float, lng: float, threshold: float = 0.1) -> List[Dict[str, Any]]:
    """Find shops similar to the given parameters (for deduplication)."""
    db = get_database()
    shops_collection: Collection = db.shops

    # Simple proximity search (can be enhanced with more sophisticated matching)
    delta = threshold / 111.0  # Convert km to degrees

    try:
        shops = list(shops_collection.find({
            "name": {"$regex": name.split()[0], "$options": "i"},  # Match first word
            "lat": {"$gte": lat - delta, "$lte": lat + delta},
            "lng": {"$gte": lng - delta, "$lte": lng + delta},
            "is_active": True
        }))
        return shops
    except Exception as e:
        print(f"Error finding similar shops: {e}")
        return []


# ============ SyncLog CRUD Operations ============

def create_sync_log(run_id: str) -> Optional[str]:
    """Create a new sync log entry."""
    db = get_database()
    sync_logs_collection: Collection = db.sync_logs

    try:
        sync_log = SyncLogDocument(run_id=run_id)
        result = sync_logs_collection.insert_one(sync_log.dict(by_alias=True))
        return str(result.inserted_id)
    except DuplicateKeyError:
        print(f"Sync log with run_id {run_id} already exists")
        return None
    except Exception as e:
        print(f"Error creating sync log: {e}")
        return None


def update_sync_log(run_id: str, data: Dict[str, Any]) -> bool:
    """Update a sync log entry."""
    db = get_database()
    sync_logs_collection: Collection = db.sync_logs

    try:
        result = sync_logs_collection.update_one(
            {"run_id": run_id},
            {"$set": data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating sync log: {e}")
        return False


def complete_sync_log(run_id: str, status: str = "success", error: str = None) -> bool:
    """Mark sync log as complete."""
    data = {
        "status": status,
        "completed_at": datetime.utcnow(),
    }
    if error:
        data["error_message"] = error

    return update_sync_log(run_id, data)


def get_latest_sync_log() -> Optional[Dict[str, Any]]:
    """Get the most recent sync log."""
    db = get_database()
    sync_logs_collection: Collection = db.sync_logs

    try:
        sync_log = sync_logs_collection.find_one(
            {},
            sort=[("started_at", -1)]
        )
        return sync_log
    except Exception as e:
        print(f"Error getting latest sync log: {e}")
        return None


def get_sync_log_by_run_id(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a sync log by run_id."""
    db = get_database()
    sync_logs_collection: Collection = db.sync_logs

    try:
        return sync_logs_collection.find_one({"run_id": run_id})
    except Exception as e:
        print(f"Error getting sync log by run_id: {e}")
        return None


def get_sync_logs(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent sync logs."""
    db = get_database()
    sync_logs_collection: Collection = db.sync_logs

    try:
        sync_logs = list(sync_logs_collection.find({})
                        .sort("started_at", -1)
                        .limit(limit))
        return sync_logs
    except Exception as e:
        print(f"Error getting sync logs: {e}")
        return []


# ============ Analytics Operations ============

def get_sync_status() -> Dict[str, Any]:
    """Get overall sync status and statistics."""
    db = get_database()

    try:
        latest_sync = get_latest_sync_log()
        total_shops = count_shops(active_only=True)
        all_shops = count_shops(active_only=False)

        return {
            "last_sync": latest_sync.get("completed_at") if latest_sync else None,
            "total_shops": all_shops,
            "active_shops": total_shops,
            "inactive_shops": all_shops - total_shops,
            "latest_sync_status": latest_sync.get("status") if latest_sync else "never",
        }
    except Exception as e:
        print(f"Error getting sync status: {e}")
        return {
            "last_sync": None,
            "total_shops": 0,
            "active_shops": 0,
            "inactive_shops": 0,
            "latest_sync_status": "error",
        }


def detect_new_shops_since_last_sync() -> List[Dict[str, Any]]:
    """Detect shops added since last successful sync."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        latest_sync = get_latest_sync_log()
        if not latest_sync or not latest_sync.get("completed_at"):
            return []  # No previous sync

        last_sync_time = latest_sync["completed_at"]

        new_shops = list(shops_collection.find({
            "created_at": {"$gt": last_sync_time},
            "is_active": True
        }).sort("created_at", -1))

        return new_shops
    except Exception as e:
        print(f"Error detecting new shops: {e}")
        return []


def detect_closed_shops_since_last_sync() -> List[Dict[str, Any]]:
    """Detect shops marked as inactive since last successful sync."""
    db = get_database()
    shops_collection: Collection = db.shops

    try:
        latest_sync = get_latest_sync_log()
        if not latest_sync or not latest_sync.get("completed_at"):
            return []  # No previous sync

        last_sync_time = latest_sync["completed_at"]

        closed_shops = list(shops_collection.find({
            "last_updated": {"$gt": last_sync_time},
            "is_active": False
        }).sort("last_updated", -1))

        return closed_shops
    except Exception as e:
        print(f"Error detecting closed shops: {e}")
        return []
