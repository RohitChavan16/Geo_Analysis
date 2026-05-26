# API Reference

Base URL defaults to `http://localhost:8000/api`. Some shop endpoints also have legacy aliases without `/api`.

Authentication is not implemented. All endpoints are currently unauthenticated.

## Common Error Shape

Most route-level failures return:

```json
{
  "detail": "Error fetching shops: <message>"
}
```

The global exception handler returns:

```json
{
  "detail": "Internal server error",
  "error": "<exception text>"
}
```

## GET /api/health

Returns API process health.

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-05-26T10:00:00.000000",
  "version": "1.0.0"
}
```

## GET /api/health/database

Pings MongoDB and returns collection counts.

Response:

```json
{
  "database_status": "connected",
  "database_name": "geoshop_engine",
  "shops_count": 1250,
  "sync_logs_count": 12,
  "timestamp": "2026-05-26T10:00:00.000000"
}
```

If MongoDB is unavailable, the endpoint returns `database_status: disconnected` with an `error` string.

## GET /api/shops

Lists active shops. Supports filters:

| Query | Type | Purpose |
| --- | --- | --- |
| `limit` | integer | Max records. Defaults to `100`. |
| `offset` | integer | Pagination offset. Defaults to `0`. |
| `min_confidence` | float | Return active shops at or above confidence threshold. |
| `name` | string | Case-insensitive partial name search. |
| `lat` | float | Latitude for proximity search. |
| `lng` | float | Longitude for proximity search. |
| `radius` | float | Radius in kilometers. Defaults to `1.0`. |

Filter precedence is `name`, then `lat/lng`, then `min_confidence`, then default list.

Response:

```json
[
  {
    "id": "66062bd03a2d5a...",
    "name": "Example Cafe",
    "address": "1 Example Road, Singapore 123456",
    "lat": 1.3521,
    "lng": 103.8198,
    "sources": ["osm", "onemap"],
    "confidence_score": 72.5,
    "confidence_level": "HIGH",
    "is_active": true,
    "last_updated": "2026-05-26T10:00:00.000000"
  }
]
```

## GET /api/shops/stats

Returns active shop counts and the proportion that are high confidence.

```json
{
  "total_active_shops": 1250,
  "high_confidence_shops": 430,
  "confidence_percentage": 34.4
}
```

## GET /api/shops/{shop_id}

Returns one shop by Mongo `_id`. Returns `404` when not found.

## GET /api/sync/status

Returns aggregate sync status from `sync_logs` and shop counts.

```json
{
  "last_sync": "2026-05-26T10:00:00.000000",
  "total_shops": 1400,
  "active_shops": 1250,
  "inactive_shops": 150,
  "latest_sync_status": "success"
}
```

## GET /api/sync/progress

Returns process-local live progress.

```json
{
  "active_run_id": "c0a801...",
  "status": "running",
  "stage": "matching",
  "message": "Matching records across sources",
  "source_counts": { "osm": 400, "datagov": 800, "onemap": 200, "digital": 0, "total": 1400 },
  "matched_groups": 980,
  "scored_records": 0,
  "updated_records": 200,
  "live_change_summary": { "new_count": 20, "updated_count": 180, "closed_count": 5 },
  "progress_percent": 55,
  "last_updated": "2026-05-26T10:00:00.000000"
}
```

## GET /api/sync/history

Query:

- `limit`: integer from 1 to 100. Defaults to `20`.

Response:

```json
{
  "history": [
    {
      "run_id": "c0a801...",
      "status": "success",
      "started_at": "2026-05-26T09:55:00.000000",
      "completed_at": "2026-05-26T10:00:00.000000",
      "new_count": 20,
      "updated_count": 180,
      "closed_count": 5,
      "closed_low_conf_count": 1,
      "closed_missing_count": 4,
      "source_counts": { "osm": 400, "datagov": 800, "onemap": 200, "digital": 0, "total": 1400 },
      "error_message": null
    }
  ]
}
```

## GET /api/sync/changes

Query:

- `run_id`: optional sync run id. If omitted, the latest sync log is used.

Returns summary counts and sampled change rows. Each `new_shops`, `closed_shops`, and `updated_shops` list is capped in code to 30 sampled entries.

## POST /api/sync/trigger

Creates a sync log and enqueues `run_sync_pipeline`.

Response:

```json
{
  "message": "Sync triggered successfully",
  "run_id": "c0a801...",
  "status": "running"
}
```

## POST /api/update/realtime

Query:

- `min_confidence`: float, defaults to `50.0`.

Creates a sync log and enqueues `run_realtime_update_pipeline`.

Response:

```json
{
  "message": "Real-time update triggered successfully",
  "run_id": "realtime_c0a801...",
  "min_confidence": 50.0,
  "status": "running"
}
```

## GET /api/debug/pipeline-data

Query:

- `refresh`: boolean. `true` bypasses the 10-minute in-memory debug cache.

Runs source fetching, normalization, matching, and scoring inspection without persisting final records. This endpoint can be expensive and should be protected in production.

