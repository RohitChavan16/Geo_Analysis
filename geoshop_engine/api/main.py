from datetime import datetime, timedelta
from typing import List, Optional
import os
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db.database import init_database, get_database
from db.crud import (
    complete_sync_log,
    count_shops,
    create_sync_log,
    detect_closed_shops_since_last_sync,
    detect_new_shops_since_last_sync,
    get_all_active_shops,
    get_high_confidence_shops,
    get_shop,
    get_shops_by_location,
    get_shops_by_name,
    get_sync_status,
)
from db.models import ShopResponse
from main import run_pipeline
from processors.matcher import match_shops, merge_shop_groups
from processors.normalizer import normalize_datagov
from signal_engine.signal_calculator import calculate_confidence
from data_fetchers.datagov_fetcher import fetch_datagov_data
from data_fetchers.osm_fetcher import fetch_osm_shops
from data_fetchers.onemap_fetcher import fetch_onemap_shops


app = FastAPI(
    title="GeoShop Engine API",
    description="Real-time geolocation-based shop intelligence platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PIPELINE_DEBUG_CACHE = {"data": None, "at": None}
PIPELINE_DEBUG_CACHE_TTL = timedelta(minutes=10)
SYNC_PROGRESS = {
    "active_run_id": None,
    "status": "idle",
    "stage": "idle",
    "message": "No sync running",
    "source_counts": {"osm": 0, "datagov": 0, "onemap": 0, "total": 0},
    "matched_groups": 0,
    "scored_records": 0,
    "updated_records": 0,
    "last_updated": None,
}


@app.on_event("startup")
async def startup_event():
    success = init_database()
    if success:
        print("GeoShop Engine API started with database connectivity")
    else:
        print("GeoShop Engine API started in offline mode (database unavailable)")


def update_sync_progress(**kwargs):
    SYNC_PROGRESS.update(kwargs)
    SYNC_PROGRESS["last_updated"] = datetime.utcnow().isoformat()


@app.get("/api/shops", response_model=List[ShopResponse])
@app.get("/shops", response_model=List[ShopResponse])
async def get_shops(
    limit: int = Query(100),
    offset: int = Query(0),
    min_confidence: Optional[float] = Query(None),
    name: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius: float = Query(1.0),
):
    try:
        if name:
            shops = get_shops_by_name(name, limit)
        elif lat is not None and lng is not None:
            shops = get_shops_by_location(lat, lng, radius)
        elif min_confidence is not None:
            shops = get_high_confidence_shops(min_confidence, limit)
        else:
            shops = get_all_active_shops(limit, offset)
        return [ShopResponse(**shop) for shop in shops]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shops: {e}")


@app.get("/api/shops/stats")
@app.get("/shops/stats")
async def get_shop_stats():
    try:
        total_shops = count_shops(active_only=True)
        high_confidence = len(get_high_confidence_shops(min_confidence=70.0))
        return {
            "total_active_shops": total_shops,
            "high_confidence_shops": high_confidence,
            "confidence_percentage": (high_confidence / total_shops * 100) if total_shops > 0 else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {e}")


@app.get("/api/shops/{shop_id}", response_model=ShopResponse)
@app.get("/shops/{shop_id}", response_model=ShopResponse)
async def get_shop_by_id(shop_id: str):
    shop = get_shop(shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return ShopResponse(**shop)


@app.get("/api/sync/status")
async def get_sync_status_endpoint():
    try:
        return get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {e}")


@app.get("/api/sync/progress")
async def get_sync_progress():
    return SYNC_PROGRESS


@app.get("/api/sync/changes")
async def get_sync_changes():
    try:
        new_shops = detect_new_shops_since_last_sync()
        closed_shops = detect_closed_shops_since_last_sync()
        return {
            "new_shops": [ShopResponse(**shop) for shop in new_shops],
            "closed_shops": [ShopResponse(**shop) for shop in closed_shops],
            "new_count": len(new_shops),
            "closed_count": len(closed_shops),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync changes: {e}")


@app.post("/api/sync/trigger")
async def trigger_sync(background_tasks: BackgroundTasks):
    try:
        run_id = str(uuid.uuid4())
        sync_log_id = create_sync_log(run_id)
        if not sync_log_id:
            raise HTTPException(status_code=500, detail="Failed to create sync log")

        update_sync_progress(
            active_run_id=run_id,
            status="running",
            stage="queued",
            message="Sync queued",
            source_counts={"osm": 0, "datagov": 0, "onemap": 0, "total": 0},
            matched_groups=0,
            scored_records=0,
            updated_records=0,
        )

        background_tasks.add_task(run_sync_pipeline, run_id)
        return {"message": "Sync triggered successfully", "run_id": run_id, "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering sync: {e}")


def run_sync_pipeline(run_id: str):
    try:
        update_sync_progress(
            active_run_id=run_id,
            status="running",
            stage="pipeline",
            message="Running full pipeline",
        )
        stats = run_pipeline()
        complete_sync_log(run_id, "success")
        update_sync_progress(
            active_run_id=run_id,
            status="success" if stats.get("success") else "failed",
            stage="completed",
            message="Sync completed" if stats.get("success") else stats.get("error", "Sync failed"),
            updated_records=stats.get("stored_count", 0),
        )
        print(f"Sync completed successfully: {stats}")
    except Exception as e:
        error_msg = str(e)
        complete_sync_log(run_id, "failed", error_msg)
        update_sync_progress(
            active_run_id=run_id,
            status="failed",
            stage="failed",
            message=error_msg,
        )
        print(f"Sync failed: {error_msg}")


@app.post("/api/update/realtime")
async def trigger_realtime_update(
    background_tasks: BackgroundTasks,
    min_confidence: float = Query(50.0),
):
    try:
        run_id = f"realtime_{uuid.uuid4()}"
        sync_log_id = create_sync_log(run_id)
        if not sync_log_id:
            raise HTTPException(status_code=500, detail="Failed to create sync log")

        update_sync_progress(
            active_run_id=run_id,
            status="running",
            stage="queued",
            message="Realtime update queued",
            source_counts={"osm": 0, "datagov": 0, "onemap": 0, "total": 0},
            matched_groups=0,
            scored_records=0,
            updated_records=0,
        )

        background_tasks.add_task(run_realtime_update_pipeline, run_id, min_confidence)
        return {
            "message": "Real-time update triggered successfully",
            "run_id": run_id,
            "min_confidence": min_confidence,
            "status": "running",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering real-time update: {e}")


def run_realtime_update_pipeline(run_id: str, min_confidence: float):
    try:
        print("Fetching fresh data from all sources...")
        update_sync_progress(
            active_run_id=run_id,
            status="running",
            stage="fetching",
            message="Fetching from OSM, data.gov.sg, and OneMap",
        )

        try:
            osm_data = fetch_osm_shops()
        except Exception as e:
            print(f"Warning: Error fetching OSM data: {e}")
            osm_data = []
        update_sync_progress(
            stage="fetching",
            message="Fetched OpenStreetMap data",
            source_counts={
                "osm": len(osm_data),
                "datagov": 0,
                "onemap": 0,
                "total": len(osm_data),
            },
        )

        try:
            datagov_data = fetch_datagov_data(collection_id=2, max_records=1000)
        except Exception as e:
            print(f"Warning: Error fetching DataGov data: {e}")
            datagov_data = []
        update_sync_progress(
            stage="fetching",
            message="Fetched data.gov.sg data",
            source_counts={
                "osm": len(osm_data),
                "datagov": len(datagov_data),
                "onemap": 0,
                "total": len(osm_data) + len(datagov_data),
            },
        )

        try:
            onemap_data = fetch_onemap_shops()
        except Exception as e:
            print(f"Warning: Error fetching OneMap data: {e}")
            onemap_data = []
        update_sync_progress(
            stage="fetching",
            message="Fetched OneMap data",
            source_counts={
                "osm": len(osm_data),
                "datagov": len(datagov_data),
                "onemap": len(onemap_data),
                "total": len(osm_data) + len(datagov_data) + len(onemap_data),
            },
        )

        update_sync_progress(stage="normalizing", message="Normalizing source records")
        normalized_datagov = normalize_datagov(datagov_data)
        all_records = osm_data + normalized_datagov + onemap_data

        if not all_records:
            complete_sync_log(run_id, "failed", "No live source data fetched (all sources empty)")
            update_sync_progress(
                status="failed",
                stage="failed",
                message="No live source data fetched (all sources empty)",
            )
            print("Real-time update failed: all source fetches returned empty")
            return

        update_sync_progress(stage="matching", message="Matching records across sources")
        matched_groups = match_shops(all_records)
        update_sync_progress(matched_groups=len(matched_groups))
        updates_made = 0

        update_sync_progress(stage="scoring", message="Scoring and storing matched groups")
        for group in matched_groups:
            if not group:
                continue

            merged_group = merge_shop_groups(group)
            confidence_data = calculate_confidence(merged_group)
            confidence_score = confidence_data.get("confidence_score", 0)
            if confidence_score < min_confidence:
                continue

            shop_data = {
                "name": merged_group.get("name"),
                "address": merged_group.get("address"),
                "lat": merged_group.get("lat"),
                "lng": merged_group.get("lng"),
                "sources": merged_group.get("sources", []),
                "phone": merged_group.get("phone"),
                "website": merged_group.get("website"),
                "opening_hours": merged_group.get("opening_hours"),
                "shop_type": merged_group.get("shop_type"),
                "postal_code": merged_group.get("postal_code"),
                "confidence_score": confidence_score,
                "confidence_level": confidence_data.get("confidence_level", "LOW"),
                "match_quality": confidence_data.get("confidence_level", "LOW"),
                "raw_data": merged_group.get("all_records", []),
                "last_updated": datetime.utcnow(),
                "is_active": True,
            }

            from db.crud import create_shop, find_similar_shops, update_shop

            existing_shops = find_similar_shops(
                shop_data["name"],
                shop_data["lat"],
                shop_data["lng"],
            )

            if existing_shops:
                shop_id = existing_shops[0]["_id"]
                update_shop(shop_id, shop_data)
            else:
                create_shop(shop_data)

            updates_made += 1
            if updates_made % 100 == 0:
                update_sync_progress(updated_records=updates_made)

        complete_sync_log(run_id, "success", f"Updated {updates_made} shops with confidence >= {min_confidence}%")
        update_sync_progress(
            status="success",
            stage="completed",
            message=f"Realtime update completed ({updates_made} records updated)",
            updated_records=updates_made,
            scored_records=len(matched_groups),
        )
        print(f"Real-time update completed: {updates_made} shops updated")

    except Exception as e:
        error_msg = str(e)
        complete_sync_log(run_id, "failed", error_msg)
        update_sync_progress(
            status="failed",
            stage="failed",
            message=error_msg,
        )
        print(f"Real-time update failed: {error_msg}")


@app.get("/api/debug/pipeline-data")
async def inspect_data_pipeline(
    refresh: bool = Query(False, description="Force refresh instead of returning cached debug payload")
):
    try:
        now = datetime.utcnow()
        cached_at = PIPELINE_DEBUG_CACHE.get("at")
        if not refresh and cached_at and (now - cached_at) < PIPELINE_DEBUG_CACHE_TTL:
            return PIPELINE_DEBUG_CACHE.get("data")

        print("Starting data pipeline inspection...")

        try:
            osm_raw = fetch_osm_shops()
        except Exception as e:
            print(f"Warning: Error fetching OSM data in pipeline: {e}")
            osm_raw = []

        try:
            datagov_raw = fetch_datagov_data(collection_id=2, max_records=1000)
        except Exception as e:
            print(f"Warning: Error fetching DataGov data in pipeline: {e}")
            datagov_raw = []

        try:
            onemap_raw = fetch_onemap_shops()
        except Exception as e:
            print(f"Warning: Error fetching OneMap data in pipeline: {e}")
            onemap_raw = []

        total_raw = len(osm_raw) + len(datagov_raw) + len(onemap_raw)

        normalized_datagov = normalize_datagov(datagov_raw)
        all_normalized = osm_raw + normalized_datagov + onemap_raw

        matched_groups = match_shops(all_normalized)
        merged_groups = [merge_shop_groups(group) for group in matched_groups if group]

        final_shops = []
        for group in merged_groups:
            confidence_data = calculate_confidence(group)
            confidence_score = confidence_data.get("confidence_score", 0)
            confidence_level = confidence_data.get("confidence_level", "LOW")
            final_shops.append(
                {
                    "name": group.get("name"),
                    "address": group.get("address"),
                    "lat": group.get("lat"),
                    "lng": group.get("lng"),
                    "sources": group.get("sources", []),
                    "shop_type": group.get("shop_type"),
                    "confidence_score": confidence_score,
                    "confidence_level": confidence_level,
                    "raw_records_count": len(group.get("all_records", [])),
                }
            )

        payload = {
            "pipeline_status": "complete",
            "timestamp": datetime.utcnow(),
            "stage_1_counts": {
                "osm": len(osm_raw),
                "datagov": len(datagov_raw),
                "onemap": len(onemap_raw),
                "total": total_raw,
            },
            "stage_2_normalized_count": len(all_normalized),
            "stage_3_matched_groups": len(merged_groups),
            "stage_4_final": {
                "total_shops": len(final_shops),
                "sample": final_shops[:10],
            },
        }
        PIPELINE_DEBUG_CACHE["data"] = payload
        PIPELINE_DEBUG_CACHE["at"] = now
        return payload

    except Exception as e:
        return {
            "pipeline_status": "error",
            "error": str(e),
            "troubleshooting": [
                "Check data source availability",
                "Verify network connectivity",
                "Check server logs",
            ],
        }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow(), "version": "1.0.0"}


@app.get("/api/health/database")
async def database_health_check():
    try:
        db = get_database()
        db.command("ping")
        shops_count = db.shops.count_documents({})
        sync_logs_count = db.sync_logs.count_documents({})
        return {
            "database_status": "connected",
            "database_name": db.name,
            "shops_count": shops_count,
            "sync_logs_count": sync_logs_count,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        return {
            "database_status": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow(),
        }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


