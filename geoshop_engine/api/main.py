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
    create_shop,
    find_similar_shops,
    get_all_active_shops,
    get_high_confidence_shops,
    get_shop,
    get_sync_log_by_run_id,
    get_sync_logs,
    get_latest_sync_log,
    get_shops_by_location,
    get_shops_by_name,
    get_sync_status,
    update_shop,
    update_sync_log,
)
from db.models import ShopResponse
from processors.matcher import match_shops, merge_shop_groups, calculate_distance, string_similarity
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
    "progress_percent": 0,
    "last_updated": None,
}


def _to_shop_response_payload(shop: dict) -> dict:
    """Normalize DB document shape to ShopResponse payload."""
    return {
        "id": str(shop.get("_id") or shop.get("id") or ""),
        "name": shop.get("name") or "Unknown Shop",
        "address": shop.get("address"),
        "lat": float(shop.get("lat") or 0),
        "lng": float(shop.get("lng") or 0),
        "sources": shop.get("sources") or [],
        "confidence_score": float(shop.get("confidence_score") or 0),
        "confidence_level": shop.get("confidence_level") or "LOW",
        "is_active": bool(shop.get("is_active", True)),
        "last_updated": shop.get("last_updated") or datetime.utcnow(),
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
        return [ShopResponse(**_to_shop_response_payload(shop)) for shop in shops]
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
    return ShopResponse(**_to_shop_response_payload(shop))


@app.get("/api/sync/status")
async def get_sync_status_endpoint():
    try:
        return get_sync_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {e}")


@app.get("/api/sync/progress")
async def get_sync_progress():
    return SYNC_PROGRESS


@app.get("/api/sync/history")
async def get_sync_history(limit: int = Query(20, ge=1, le=100)):
    try:
        logs = get_sync_logs(limit=limit)
        history = []
        for log in logs:
            summary = log.get("change_summary", {})
            history.append({
                "run_id": log.get("run_id"),
                "status": log.get("status"),
                "started_at": log.get("started_at"),
                "completed_at": log.get("completed_at"),
                "new_count": summary.get("new_count", 0),
                "updated_count": summary.get("updated_count", 0),
                "closed_count": summary.get("closed_count", 0),
                "closed_low_conf_count": summary.get("closed_low_conf_count", 0),
                "closed_missing_count": summary.get("closed_missing_count", 0),
                "source_counts": log.get("source_counts", {"osm": 0, "datagov": 0, "onemap": 0, "total": 0}),
                "error_message": log.get("error_message"),
            })
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync history: {e}")


@app.get("/api/sync/changes")
async def get_sync_changes(run_id: Optional[str] = Query(None, description="Specific run_id; defaults to latest sync")):
    try:
        sync_log = get_sync_log_by_run_id(run_id) if run_id else get_latest_sync_log()
        if not sync_log:
            return {
                "run_id": None,
                "new_count": 0,
                "closed_count": 0,
                "closed_low_conf_count": 0,
                "closed_missing_count": 0,
                "updated_count": 0,
                "new_shops": [],
                "closed_shops": [],
                "updated_shops": [],
                "source_counts": {"osm": 0, "datagov": 0, "onemap": 0, "total": 0},
            }

        change_summary = sync_log.get("change_summary", {})
        source_counts = sync_log.get("source_counts", {"osm": 0, "datagov": 0, "onemap": 0, "total": 0})

        return {
            "run_id": sync_log.get("run_id"),
            "started_at": sync_log.get("started_at"),
            "completed_at": sync_log.get("completed_at"),
            "status": sync_log.get("status"),
            "new_count": change_summary.get("new_count", 0),
            "closed_count": change_summary.get("closed_count", 0),
            "closed_low_conf_count": change_summary.get("closed_low_conf_count", 0),
            "closed_missing_count": change_summary.get("closed_missing_count", 0),
            "updated_count": change_summary.get("updated_count", 0),
            "new_shops": sync_log.get("new_shops", []),
            "closed_shops": sync_log.get("closed_shops", []),
            "updated_shops": sync_log.get("updated_shops", []),
            "source_counts": source_counts,
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
            progress_percent=0,
        )

        background_tasks.add_task(run_sync_pipeline, run_id)
        return {"message": "Sync triggered successfully", "run_id": run_id, "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering sync: {e}")


def run_sync_pipeline(run_id: str):
    try:
        min_confidence = float(os.getenv("MIN_CONFIDENCE_UPDATE", "50.0"))
        run_realtime_update_pipeline(run_id, min_confidence)
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
            progress_percent=0,
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
    def _source_weight_factor(source_name: str, source_counts: dict) -> float:
        # Base reliability. Give higher weight to data.gov.sg for closure/opening confidence.
        base = {"data_gov": 1.0, "datagov": 1.0, "onemap": 0.8, "osm": 0.6}.get(source_name, 0.5)
        count = source_counts.get(source_name) or source_counts.get("datagov" if source_name == "data_gov" else source_name) or 0
        # If a source fetched very little data this run, down-weight its evidence.
        if count < 10:
            return base * 0.5
        if count < 50:
            return base * 0.75
        return base

    def _format_change(shop: dict, status: str, recommendation: str, source_counts: dict, reason: str, closure_type: Optional[str] = None) -> dict:
        sources = shop.get("sources", [])
        weighted_confidence = float(shop.get("confidence_score", 0)) / 100.0
        if sources:
            factors = [_source_weight_factor(s, source_counts) for s in sources]
            weighted_confidence = max(0.05, min(0.99, weighted_confidence * (sum(factors) / len(factors))))

        return {
            "place_name": shop.get("name", "Unknown Place"),
            "address": shop.get("address", "Unknown Address"),
            "category": shop.get("shop_type") or "general",
            "coordinates": {"lat": shop.get("lat"), "lng": shop.get("lng")},
            "match_in_database": "Found" if shop.get("_existing") else "Not Found",
            "predicted_status": status,
            "confidence": round(weighted_confidence, 2),
            "confirmed_from": ", ".join(sources) if sources else "single source",
            "recommendation": recommendation,
            "reason": reason,
            "closure_type": closure_type,
            "sources": sources,
            "phone": shop.get("phone"),
            "website": shop.get("website"),
            "opening_hours": shop.get("opening_hours"),
            "postal_code": shop.get("postal_code"),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def _exists_in_observed(db_shop: dict, observed: list) -> bool:
        for current in observed:
            try:
                dist = calculate_distance(db_shop.get("lat"), db_shop.get("lng"), current.get("lat"), current.get("lng"))
            except Exception:
                continue
            if dist > 0.07:
                continue
            name_sim = string_similarity(db_shop.get("name", ""), current.get("name", ""))
            addr_sim = string_similarity(db_shop.get("address", ""), current.get("address", ""))
            if name_sim >= 0.6 or addr_sim >= 0.65:
                return True
        return False

    try:
        datagov_max_records = int(os.getenv("DATA_GOV_MAX_RECORDS", "1000"))
        new_threshold = float(os.getenv("NEW_SHOP_CONF_THRESHOLD", "30"))
        close_threshold = float(os.getenv("CLOSE_SHOP_CONF_THRESHOLD", "30"))
        print("Fetching fresh data from all sources...")
        update_sync_progress(
            active_run_id=run_id,
            status="running",
            stage="fetching",
            message="Fetching from OSM, data.gov.sg, and OneMap",
            progress_percent=10,
        )

        existing_active_before = get_all_active_shops(limit=100000, offset=0)

        try:
            osm_data = fetch_osm_shops()
        except Exception as e:
            print(f"Warning: Error fetching OSM data: {e}")
            osm_data = []
        update_sync_progress(
            stage="fetching",
            message="Fetched OpenStreetMap data",
            source_counts={"osm": len(osm_data), "datagov": 0, "onemap": 0, "total": len(osm_data)},
            progress_percent=20,
        )

        try:
            datagov_data = fetch_datagov_data(collection_id=2, max_records=datagov_max_records)
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
            progress_percent=30,
        )

        try:
            onemap_data = fetch_onemap_shops()
        except Exception as e:
            print(f"Warning: Error fetching OneMap data: {e}")
            onemap_data = []
        source_counts = {
            "osm": len(osm_data),
            "datagov": len(datagov_data),
            "onemap": len(onemap_data),
            "total": len(osm_data) + len(datagov_data) + len(onemap_data),
        }
        update_sync_progress(stage="fetching", message="Fetched OneMap data", source_counts=source_counts)

        update_sync_progress(stage="normalizing", message="Normalizing source records")
        normalized_datagov = normalize_datagov(datagov_data)
        all_records = osm_data + normalized_datagov + onemap_data

        if not all_records:
            complete_sync_log(run_id, "failed", "No live source data fetched (all sources empty)")
            update_sync_log(
                run_id,
                {
                    "source_counts": source_counts,
                    "change_summary": {
                        "new_count": 0,
                        "closed_count": 0,
                        "closed_low_conf_count": 0,
                        "closed_missing_count": 0,
                        "updated_count": 0,
                    },
                },
            )
            update_sync_progress(status="failed", stage="failed", message="No live source data fetched (all sources empty)", progress_percent=100)
            return

        update_sync_progress(stage="matching", message="Matching records across sources", progress_percent=45)
        matched_groups = match_shops(all_records)
        update_sync_progress(matched_groups=len(matched_groups))

        update_sync_progress(stage="scoring", message="Scoring and storing matched groups", progress_percent=55)
        observed_records = []
        new_shops = []
        updated_shops = []
        low_conf_closed = []
        new_count = 0
        updated_count = 0
        low_conf_closed_count = 0
        closed_ids = set()

        for group in matched_groups:
            if not group:
                continue

            merged_group = merge_shop_groups(group)
            confidence_data = calculate_confidence(merged_group)
            confidence_score = confidence_data.get("confidence_score", 0)
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

            observed_records.append(shop_data)
            existing_shops = find_similar_shops(shop_data["name"], shop_data["lat"], shop_data["lng"])

            if existing_shops:
                shop_id = existing_shops[0]["_id"]
                if confidence_score < close_threshold:
                    update_shop(shop_id, {"is_active": False, "closed_at": datetime.utcnow(), "closure_reason": f"Low confidence ({confidence_score:.1f})"})
                    closed_ids.add(shop_id)
                    low_conf_closed_count += 1
                    if len(low_conf_closed) < 30:
                        low_conf_closed.append(
                            _format_change(
                                {**shop_data, "_existing": True},
                                "Closed Place",
                                "Review",
                                source_counts,
                                f"Existing DB place confidence {confidence_score:.1f} < {close_threshold}; auto-marked closed.",
                                "low_confidence",
                            )
                        )
                elif confidence_score >= min_confidence:
                    update_shop(shop_id, shop_data)
                    updated_count += 1
                    if len(updated_shops) < 30:
                        updated_shops.append(
                            _format_change(
                                {**shop_data, "_existing": True},
                                "Existing Place",
                                "Accept",
                                source_counts,
                                "Matched an existing active shop in database.",
                            )
                        )
            else:
                if confidence_score >= new_threshold:
                    create_shop(shop_data)
                    new_count += 1
                    if len(new_shops) < 30:
                        new_shops.append(
                            _format_change(
                                {**shop_data, "_existing": False},
                                "New Place",
                                "Review",
                                source_counts,
                                f"Not found in DB and confidence {confidence_score:.1f} >= {new_threshold}. data.gov.sg weighted highest for opening signal.",
                            )
                        )

            if (updated_count + new_count) % 100 == 0:
                progress = 55 + min(25, ((updated_count + new_count) // 100) * 2)
                update_sync_progress(updated_records=updated_count + new_count, progress_percent=progress)

        update_sync_progress(stage="closure_check", message="Detecting closed shops", progress_percent=85)
        closed_shops = []
        missing_closed_count = 0
        for old_shop in existing_active_before:
            if not old_shop.get("is_active", True):
                continue
            if old_shop.get("_id") in closed_ids:
                continue
            if _exists_in_observed(old_shop, observed_records):
                continue
            update_shop(old_shop.get("_id"), {"is_active": False, "closed_at": datetime.utcnow()})
            missing_closed_count += 1
            if len(closed_shops) < 30:
                old_shop["confidence_score"] = old_shop.get("confidence_score", 0)
                closed_shops.append(
                    _format_change(
                        {**old_shop, "_existing": True},
                        "Closed Place",
                        "Review",
                        source_counts,
                        "Previously active shop not observed in latest multi-source sync. data.gov.sg absence contributes strongest closure signal; low-volume sources are down-weighted.",
                        "not_observed",
                    )
                )

        # include low-confidence closed records in closed list/count
        closed_shops = low_conf_closed + closed_shops
        closed_count = low_conf_closed_count + missing_closed_count

        change_summary = {
            "new_count": new_count,
            "closed_count": closed_count,
            "closed_low_conf_count": low_conf_closed_count,
            "closed_missing_count": missing_closed_count,
            "updated_count": updated_count,
        }
        update_sync_log(
            run_id,
            {
                "source_counts": source_counts,
                "change_summary": change_summary,
                "new_shops": new_shops,
                "closed_shops": closed_shops,
                "updated_shops": updated_shops,
                "total_raw": source_counts["total"],
                "total_matched": len(matched_groups),
                "total_stored": updated_count + new_count,
            },
        )

        complete_sync_log(
            run_id,
            "success",
            f"new={new_count}, updated={updated_count}, closed={closed_count} "
            f"(low_conf={low_conf_closed_count}, missing={missing_closed_count})",
        )
        update_sync_progress(
            status="success",
            stage="completed",
            message=(
                f"Completed: {new_count} new, {updated_count} updated, {closed_count} closed "
                f"(low_conf={low_conf_closed_count}, missing={missing_closed_count})"
            ),
            updated_records=updated_count + new_count,
            scored_records=len(matched_groups),
            progress_percent=100,
        )
        print(f"Realtime update completed: {change_summary}")

    except Exception as e:
        error_msg = str(e)
        complete_sync_log(run_id, "failed", error_msg)
        update_sync_progress(status="failed", stage="failed", message=error_msg, progress_percent=100)
        print(f"Real-time update failed: {error_msg}")


@app.get("/api/debug/pipeline-data")
async def inspect_data_pipeline(
    refresh: bool = Query(False, description="Force refresh instead of returning cached debug payload")
):
    try:
        datagov_max_records = int(os.getenv("DATA_GOV_MAX_RECORDS", "1000"))
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
            datagov_raw = fetch_datagov_data(collection_id=2, max_records=datagov_max_records)
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


