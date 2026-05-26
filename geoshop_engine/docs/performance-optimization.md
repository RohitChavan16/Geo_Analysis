# Performance Optimization

## Implemented Optimizations

- Parallel source fetches in `run_realtime_update_pipeline`.
- data.gov.sg in-memory fetch cache.
- `/api/debug/pipeline-data` 10-minute cache.
- MongoDB indexes for common filters.
- Frontend `Promise.all` for dashboard fetches.
- Map base marker cap of 900 records.

## Bottlenecks

- Matching compares each record with later records.
- Closure detection compares old active shops to observed records.
- `get_all_active_shops(limit=100000)` can become heavy.
- Regex name search is basic and may not use optimal indexes.
- Sync work runs inside the API process.

## Recommendations

- Add geohash bucketing before fuzzy matching.
- Add MongoDB geospatial index and `$near` queries.
- Persist source snapshots and diff them incrementally.
- Move sync to a worker queue.
- Add caching for read-heavy dashboard endpoints.
- Add frontend marker clustering.

