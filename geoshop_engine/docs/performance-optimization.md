# Performance Optimization

GeoShop Engine includes performance-minded design choices across ingestion, persistence, and dashboard rendering. The roadmap extends those choices toward larger datasets and multi-instance operation.

## Implemented Optimizations

- Parallel source fetches in `run_realtime_update_pipeline`.
- data.gov.sg in-memory fetch cache.
- `/api/debug/pipeline-data` 10-minute cache.
- MongoDB indexes for common filters.
- Frontend `Promise.all` for dashboard fetches.
- Map base marker cap of 900 records.
- Source record caps and pagination controls.

## Performance Evolution Areas

- Candidate matching can evolve from pairwise comparison to spatial bucketing.
- Closure detection can evolve from active-set comparison to incremental source snapshots.
- Active-shop retrieval can be partitioned by geography, update window, or source.
- Name search can use text indexes and ranking strategies.
- Sync execution can move from API background tasks to worker queues.

## Roadmap

- Add geohash bucketing before fuzzy matching.
- Add MongoDB geospatial index and `$near` queries.
- Persist source snapshots and diff them incrementally.
- Move sync to a worker queue.
- Add caching for read-heavy dashboard endpoints.
- Add frontend marker clustering.

