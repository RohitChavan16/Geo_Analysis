from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class ShopDocument(BaseModel):
    """Shop document model for MongoDB."""

    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str
    address: Optional[str] = None
    lat: float
    lng: float

    # Data sources
    sources: List[str] = Field(default_factory=list)

    # Additional metadata
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    shop_type: Optional[str] = None
    postal_code: Optional[str] = None

    # Confidence scoring
    confidence_score: float = 0.0
    confidence_level: str = "MEDIUM"
    match_quality: Optional[str] = None

    # Raw data from all sources
    raw_data: Optional[List[Dict[str, Any]]] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None

    # Flags
    is_active: bool = True
    is_duplicate: bool = False

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }


class SyncLogDocument(BaseModel):
    """Sync log document model for MongoDB."""

    id: Optional[str] = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    run_id: str
    status: str = "running"
    error_message: Optional[str] = None

    # Stats
    osm_count: int = 0
    datagov_count: int = 0
    onemap_count: int = 0
    total_raw: int = 0
    total_matched: int = 0
    total_stored: int = 0
    duplicates_found: int = 0

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }


# API Response Models
class ShopResponse(BaseModel):
    """Response model for shop data."""
    id: str
    name: str
    address: Optional[str]
    lat: float
    lng: float
    sources: List[str]
    confidence_score: float
    confidence_level: str
    is_active: bool
    last_updated: datetime

    class Config:
        json_encoders = {
            ObjectId: str
        }


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    last_sync: Optional[datetime]
    total_shops: int
    active_shops: int
    new_shops_last_sync: int
    closed_shops_last_sync: int


class UpdateResult(BaseModel):
    """Response model for update operations."""
    success: bool
    message: str
    new_shops: int = 0
    updated_shops: int = 0
    closed_shops: int = 0
    total_processed: int = 0