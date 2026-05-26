# Troubleshooting

## API Starts But Database Is Disconnected

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

## Dashboard Shows No Data

Check:

- FastAPI is running.
- `VITE_API_BASE` points to the API base ending in `/api`.
- MongoDB has `shops` documents.
- Browser network tab has no CORS or 500 errors.

## Sync Returns No Source Records

Check:

- public API network access;
- source rate limits;
- `DATA_GOV_COLLECTION_ID`;
- `ONEMAP_MAX_PAGES`;
- Overpass endpoint availability.

## Tests Fail With SQLAlchemy Import Errors

`test_pipeline.py` and `verify.py` are stale and expect old SQLite/SQLAlchemy symbols. Rewrite them around MongoDB or mock `db.crud` before using them.

## Map Markers Do Not Render

Check that shop records have finite numeric `lat` and `lng`. The frontend drops invalid coordinates.

