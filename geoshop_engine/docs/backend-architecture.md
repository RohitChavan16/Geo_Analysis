# Backend Architecture

The backend is a Python FastAPI application.

## Entry Points

- `run_api.py`: loads `.env` and starts `uvicorn api.main:app` with reload enabled.
- `api/main.py`: defines the FastAPI app, routes, progress state, and background sync pipeline.
- `main.py`: command-line pipeline runner with mock/demo support.
- `scheduler/jobs.py`: schedule-based pipeline runner intended to run every 3 days.

## Route Groups

- Shops: list, stats, detail.
- Sync: status, progress, history, changes, trigger.
- Update: real-time update trigger.
- Debug: pipeline inspection.
- Health: API and database checks.

## Pipeline Stages

1. Load thresholds from environment.
2. Snapshot existing active shops.
3. Fetch OSM, data.gov.sg, OneMap, and digital sources in parallel.
4. Normalize data.gov.sg.
5. Optionally infer digital records from primary sources.
6. Match records into groups.
7. Merge groups and calculate scores.
8. Update existing shops or create new shops.
9. Mark closure candidates inactive through decision-score and observation rules.
10. Persist sync log summaries and update progress.

## Exception Handling Strategy

Route handlers convert operational exceptions into HTTP responses, while the global exception handler provides a consistent response shape during development. The production evolution path is to standardize client-safe errors and route detailed diagnostics into structured logs.


