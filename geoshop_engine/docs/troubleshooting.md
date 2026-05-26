# Troubleshooting

## Database Connectivity Diagnostics

Run:

```bash
python test_mongodb.py
```

Check:

- `MONGODB_URL` exists.
- Atlas cluster is running.
- IP allow-list permits the host.
- username/password are URL encoded.
- database user has read/write permission.

## Dashboard Data Flow Checks

Check:

- FastAPI is running.
- `VITE_API_BASE` points to the API base ending in `/api`.
- MongoDB has `shops` documents.
- Browser network tab has no CORS or 500 errors.

## Source Fetch Diagnostics

Check:

- public API network access;
- source rate limits;
- `DATA_GOV_COLLECTION_ID`;
- `ONEMAP_MAX_PAGES`;
- Overpass endpoint availability.

## Component Tests Need Consolidation

The test roadmap is to consolidate legacy component checks into a MongoDB-backed `pytest` suite that mirrors the active API and persistence architecture.

## Map Marker Rendering Checks

Check that shop records have finite numeric `lat` and `lng`. The frontend drops invalid coordinates.

