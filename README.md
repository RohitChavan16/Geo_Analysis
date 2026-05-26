# GeoShop Engine

[![Backend CI](https://github.com/OWNER/geoshop-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/geoshop-engine/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/UI-React%20%2B%20Vite-61DAFB)](https://vite.dev/)
[![Database](https://img.shields.io/badge/Database-MongoDB-47A248)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GeoShop Engine is a Singapore-focused place intelligence system that detects active, new, updated, and likely closed commercial places by combining public geospatial sources, fuzzy matching, confidence scoring, and a real-time operations dashboard.

The project exists to solve a practical data quality problem: shop and place directories drift quickly. A location can appear in one registry, disappear from another, gain new contact metadata, or lose digital activity signals. GeoShop Engine ingests multiple sources, normalizes them into a shared schema, matches likely duplicate places by geography and text similarity, computes confidence and vitality scores, persists the results, and exposes the changes through an API and React dashboard.

## Key Highlights

- Multi-source ingestion from OpenStreetMap Overpass, data.gov.sg, OneMap, and optional JSON-LD/local digital snapshots.
- Singapore-specific category filtering for restaurants, cafes, attractions, hotels, amusement parks, malls, department stores, grocery stores, pharmacies, and fuel stations.
- Fuzzy entity resolution using Haversine distance, normalized text similarity, and postal-code tie breakers.
- Decision scoring that blends record confidence with digital-footprint vitality signals.
- MongoDB persistence with indexed `shops` and `sync_logs` collections.
- FastAPI service with background sync triggers, progress reporting, health checks, and debug pipeline inspection.
- React command center with live sync monitor, change feed, Recharts trend view, and Leaflet map.
- Offline-friendly mock fetchers and CLI pipeline modes for demos and diagnostics.

## Features

### Backend

- FastAPI application in `api/main.py`.
- Dual route aliases for several shop endpoints: `/api/...` and legacy `/...`.
- Background sync execution via `BackgroundTasks`.
- Parallel source fetches with `ThreadPoolExecutor`.
- In-memory progress state exposed through `/api/sync/progress`.
- Pipeline debug cache for `/api/debug/pipeline-data`.
- MongoDB CRUD layer with soft-delete semantics for closed shops.
- Sync logs with source counts, change summaries, and sampled change rows.

### Frontend

- Vite React dashboard in `frontend/`.
- Polling-based data refresh every 5 seconds.
- Manual sync and real-time update buttons.
- Light/dark theme toggle persisted in `localStorage`.
- Leaflet Singapore map with existing, updated, new, and closed markers.
- Recharts trend visualization for new, updated, closed, and net growth counts.
- GSAP animated stat counters.

### Data Pipeline

- Fetch: `data_fetchers/` pulls data from OSM, data.gov.sg, OneMap, and optional digital sources.
- Normalize: `processors/normalizer.py` standardizes data.gov.sg records.
- Filter: `processors/category_filter.py` enforces supported place categories.
- Match: `processors/matcher.py` groups cross-source records.
- Score: `signal_engine/signal_calculator.py` and `digital_footprint.py` compute confidence and decision scores.
- Store: `db/crud.py` inserts/updates MongoDB documents and sync logs.

### DevOps And Operations

- CLI entry points: `main.py`, `run_api.py`, and `scheduler/jobs.py`.
- Frontend build scripts through npm.
- MongoDB diagnostic script in `test_mongodb.py`.
- GitHub Actions workflow added for Python import checks and frontend build.
- No Dockerfile or docker-compose file is currently implemented.

### Security

- Secrets are loaded from `.env` through `python-dotenv`.
- MongoDB URI and OneMap token are environment-driven.
- Regex user/data input in `find_similar_shops` is escaped.
- Known gap: API authentication, authorization, rate limiting, strict CORS, and request schema validation are not yet implemented.

## Architecture Overview

```mermaid
flowchart LR
    OSM[OpenStreetMap Overpass] --> Fetch[data_fetchers]
    DG[data.gov.sg] --> Fetch
    OM[OneMap] --> Fetch
    DS[Optional digital snapshots / JSON-LD] --> Fetch
    Fetch --> Normalize[Normalization and category filtering]
    Normalize --> Match[Fuzzy geospatial matching]
    Match --> Score[Confidence + digital vitality scoring]
    Score --> Mongo[(MongoDB shops + sync_logs)]
    Mongo --> API[FastAPI]
    API --> UI[React command center]
    API --> Ops[Health, sync progress, debug endpoints]
```

### Request Flow

1. The dashboard calls `VITE_API_BASE` endpoints from `frontend/src/lib/api.js`.
2. FastAPI routes in `api/main.py` query MongoDB through `db/crud.py`.
3. Sync endpoints create a `sync_logs` document and enqueue a background pipeline.
4. The pipeline fetches sources in parallel, normalizes records, matches places, computes scores, and writes new/updated/closed state.
5. The UI polls stats, progress, history, shops, and changes to refresh the command center.

### Authentication Flow

There is no implemented user authentication. All API routes are publicly callable wherever the server is reachable. Production deployments should add API keys, JWT/session auth, or an identity-aware gateway before exposing sync-triggering or debug endpoints.

### Deployment Flow

The implemented deployment path is process-based:

- Backend: install `requirements.txt`, configure `.env`, then run `python run_api.py` or `uvicorn api.main:app`.
- Frontend: install dependencies in `frontend/`, configure `VITE_API_BASE`, build with `npm run build`, then serve `frontend/dist`.
- Database: provision MongoDB or MongoDB Atlas and set `MONGODB_URL`.

Docker and infrastructure-as-code are not present yet. See [docs/deployment.md](docs/deployment.md).

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | React 18, Vite 5, Tailwind CSS, Leaflet, React Leaflet, Recharts, GSAP, Lucide React |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Database | MongoDB via PyMongo |
| Authentication | Not implemented; OneMap bearer token is supported for upstream API access |
| Realtime Communication | Polling-based dashboard refresh; no WebSocket/SSE implementation |
| DevOps | npm scripts, Python scripts, GitHub Actions CI |
| Observability | Health endpoints, sync logs, progress endpoint, console logging |
| AI/ML | No trained ML model; deterministic scoring and heuristic decision engine |
| APIs | OpenStreetMap Overpass, data.gov.sg datastore, OneMap search, optional JSON-LD listing pages |
| Tooling | python-dotenv, schedule, requests, npm, Vite |
| Infrastructure | MongoDB/MongoDB Atlas, static frontend hosting, Python ASGI host |

## Folder Structure

```text
geoshop_engine/
├── api/
│   └── main.py                  # FastAPI app, routes, background sync pipeline
├── config/
│   └── settings.py              # data.gov.sg base URL constant
├── data_fetchers/
│   ├── datagov_fetcher.py       # data.gov.sg metadata lookup, datastore paging, retry/cache
│   ├── digital_sources_fetcher.py # optional local snapshot and JSON-LD ingestion
│   ├── onemap_fetcher.py        # OneMap category searches with pagination
│   └── osm_fetcher.py           # Overpass API queries with endpoint failover
├── db/
│   ├── crud.py                  # MongoDB CRUD, search, sync-log helpers
│   ├── database.py              # MongoDB connection and index initialization
│   ├── models.py                # Pydantic document/response models
│   └── models_new.py            # older duplicate model snapshot; not used by imports
├── docs/                        # production engineering documentation
├── frontend/
│   ├── src/
│   │   ├── components/          # TopBar, StatCard, SectionCard
│   │   ├── hooks/               # generic polling hook
│   │   ├── lib/api.js           # frontend API client
│   │   ├── sections/            # dashboard panels
│   │   └── App.jsx              # dashboard orchestration
│   ├── package.json             # frontend dependencies/scripts
│   └── vite.config.js
├── processors/
│   ├── category_filter.py       # supported category mapping/classification
│   ├── matcher.py               # Haversine + fuzzy text matching
│   ├── normalizer.py            # data.gov.sg normalization
│   └── result_formatter.py      # placeholder
├── scheduler/
│   └── jobs.py                  # schedule-based full pipeline runner
├── signal_engine/
│   ├── digital_footprint.py     # source reliability and activity signals
│   └── signal_calculator.py     # confidence and decision score calculation
├── main.py                      # CLI pipeline runner
├── run_api.py                   # development API server launcher
├── test_e2e.py                  # mixed e2e diagnostics; API server required
├── test_mongodb.py              # MongoDB connectivity diagnostic
├── test_pipeline.py             # stale SQLAlchemy-era component test
└── verify.py                    # stale SQLAlchemy-era verification script
```

## Installation

### Prerequisites

- Python 3.10 or newer.
- Node.js 18 or newer.
- MongoDB local instance or MongoDB Atlas cluster.
- Network access to public APIs if running live ingestion.

### Backend Setup

```bash
cd geoshop_engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python test_mongodb.py
python run_api.py
```

The API defaults to `http://localhost:8000`; interactive OpenAPI docs are available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd geoshop_engine/frontend
npm install
npm run dev
```

Set `VITE_API_BASE=http://localhost:8000/api` when the API is hosted somewhere other than the default.

### CLI Pipeline

```bash
cd geoshop_engine
python main.py demo       # mock-data demo
python main.py run        # live source run
python main.py schedule   # schedule runner every 3 days
```

Note: `main.py schedule` references scheduler functions without importing them, so use `python -m scheduler.jobs` until that entry point is fixed.

### Docker

Docker files are not currently present. A production Docker setup should include separate backend and frontend images plus MongoDB connection configuration. See [docs/deployment.md](docs/deployment.md).

## Environment Variables

| Variable | Purpose | Example | Required |
| --- | --- | --- | --- |
| `APP_ENV` | Runtime environment label. | `development` | Optional |
| `APP_HOST` | Host passed to Uvicorn in `run_api.py`. | `0.0.0.0` | Optional |
| `APP_PORT` | API port. | `8000` | Optional |
| `MONGODB_URL` | MongoDB connection string. | `mongodb+srv://user:pass@cluster/db` | Required for persistence |
| `DATABASE_NAME` | MongoDB database name. | `geoshop_engine` | Optional |
| `DATA_GOV_COLLECTION_ID` | data.gov.sg collection metadata id. | `2` | Optional |
| `DATA_GOV_MAX_RECORDS` | Max data.gov.sg records per sync. | `1000` | Optional |
| `DATA_GOV_CACHE_TTL_SECONDS` | In-memory data.gov.sg fetch cache TTL. | `3600` | Optional |
| `ONEMAP_ACCESS_TOKEN` | Optional OneMap bearer token. | `eyJ...` | Optional |
| `ONEMAP_API_KEY` | Alternative env name supported by code. | `eyJ...` | Optional |
| `ONEMAP_MAX_PAGES` | Max OneMap pages per query. | `8` | Optional |
| `DIGITAL_SOURCE_FETCH_ENABLED` | Enables optional digital-source fetcher. | `false` | Optional |
| `DIGITAL_SOURCE_SNAPSHOT_PATH` | Local JSON snapshot path for digital records. | `data/digital.json` | Optional |
| `DIGITAL_INFER_FROM_PRIMARY` | Builds inferred digital records from primary sources when digital fetch returns empty. | `true` | Optional |
| `CHOPE_LISTING_URL` | Optional listing page containing LocalBusiness JSON-LD. | `https://...` | Optional |
| `BURPPLE_LISTING_URL` | Optional listing page containing LocalBusiness JSON-LD. | `https://...` | Optional |
| `WHYQ_LISTING_URL` | Optional listing page containing LocalBusiness JSON-LD. | `https://...` | Optional |
| `SHA_LISTING_URL` | Optional listing page containing LocalBusiness JSON-LD. | `https://...` | Optional |
| `MALL_DIRECTORY_URL` | Optional listing page containing LocalBusiness JSON-LD. | `https://...` | Optional |
| `MIN_CONFIDENCE_UPDATE` | Minimum decision score for updating matched shops. | `50.0` | Optional |
| `NEW_SHOP_CONF_THRESHOLD` | Minimum decision score for inserting new shops. | `30` | Optional |
| `CLOSE_SHOP_CONF_THRESHOLD` | Decision score below which matched shops are closed. | `30` | Optional |
| `SCHEDULER_INTERVAL_DAYS` | Intended scheduler interval; current scheduler hard-codes 3 days. | `3` | Optional |
| `LOG_LEVEL` | Intended logging level; current code mostly uses `print`. | `info` | Optional |
| `VITE_API_BASE` | Frontend API base URL. | `http://localhost:8000/api` | Optional for frontend |

## API Documentation

Full endpoint documentation is in [docs/api-reference.md](docs/api-reference.md).

| Method | Endpoint | Purpose | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/health` | API health status. | None |
| `GET` | `/api/health/database` | MongoDB ping and collection counts. | None |
| `GET` | `/api/shops` | List/search shops by pagination, name, location, or confidence. | None |
| `GET` | `/api/shops/stats` | Active and high-confidence counts. | None |
| `GET` | `/api/shops/{shop_id}` | Fetch one shop. | None |
| `GET` | `/api/sync/status` | Last sync and active/inactive counts. | None |
| `GET` | `/api/sync/progress` | In-memory live progress state. | None |
| `GET` | `/api/sync/history` | Recent sync logs. | None |
| `GET` | `/api/sync/changes` | Latest or selected run changes. | None |
| `POST` | `/api/sync/trigger` | Enqueue default sync. | None |
| `POST` | `/api/update/realtime` | Enqueue real-time update with optional threshold. | None |
| `GET` | `/api/debug/pipeline-data` | Inspect live pipeline stage counts and samples. | None |

## Database Documentation

MongoDB contains two primary collections:

- `shops`: normalized place records with source metadata, confidence scores, decision fields, raw records, timestamps, and activity flags.
- `sync_logs`: pipeline run history with source counts, change summaries, sample changed shops, status, timestamps, and error messages.

Indexes are created in `db/database.py` for shop name, address, coordinates, sources, confidence, activity state, update time, unique sync run id, and sync start time. See [docs/database-design.md](docs/database-design.md).

## Security

Current implementation is suitable for local development and internal demos. Before public or company-wide deployment, add:

- Authentication and authorization for all write/debug endpoints.
- Strict CORS allow-list instead of `allow_origins=["*"]`.
- Rate limiting for sync triggers and debug pipeline calls.
- Request validation for thresholds, pagination, and filters.
- Structured secrets management outside committed `.env` files.
- Dependency scanning and CI security checks.

Detailed notes are in [docs/security.md](docs/security.md).

## Realtime Systems

The current system is near-real-time through background sync plus polling. It does not use WebSockets, WebRTC, Socket.IO, or Server-Sent Events. The dashboard polls every 5 seconds and reads `/api/sync/progress`, `/api/sync/history`, and `/api/sync/changes`.

## Observability And Monitoring

Implemented:

- `/api/health`
- `/api/health/database`
- `/api/sync/status`
- `/api/sync/progress`
- `sync_logs` persistence
- console logs during ingestion and scoring

Not implemented:

- Prometheus metrics
- Grafana dashboards
- tracing
- structured JSON logs
- alerting
- synthetic monitoring

See [docs/monitoring-observability.md](docs/monitoring-observability.md).

## Performance Optimizations

- Parallel source fetching in the real-time pipeline.
- In-memory TTL cache for data.gov.sg fetches.
- Pipeline debug endpoint cache.
- MongoDB indexes for common read paths.
- Frontend limits map base points to 900 markers to reduce Leaflet rendering load.
- Frontend route data is fetched concurrently with `Promise.all`.

Current bottlenecks include O(n²) matching behavior, in-process progress state, process-local caches, and full active-shop scans during closure detection.

## Deployment

See [docs/deployment.md](docs/deployment.md) for local, staging, and production deployment guidance.

Recommended production shape:

- FastAPI behind a reverse proxy or managed container runtime.
- Static frontend on CDN/object hosting.
- MongoDB Atlas with TLS, restricted network access, backups, and monitoring.
- Scheduled sync through a worker, cron, or external scheduler rather than the web process.
- Separate environment variables per environment.

## Screenshots And Demo

Place screenshots under `docs/assets/`:

```text
docs/assets/dashboard-light.png
docs/assets/dashboard-dark.png
docs/assets/map-view.png
docs/assets/change-feed.png
```

Suggested demo flow:

1. Start MongoDB and the FastAPI server.
2. Start the Vite dashboard.
3. Open the dashboard and trigger a sync.
4. Watch the sync monitor, source counts, map, and change feed update.

## Engineering Decisions And Tradeoffs

- MongoDB was selected for flexible source payloads and evolving scoring fields.
- Matching is deterministic and explainable rather than model-driven.
- Closure detection uses absence from the latest observed source set plus low decision score rules; this is useful for review workflows but should not be treated as irreversible ground truth.
- In-memory sync progress keeps the implementation simple but does not survive restarts or scale across multiple API instances.
- Public APIs are fetched directly from the application process; production should isolate ingestion into workers.

## Codebase Quality Audit

Production-readiness score: **5.8 / 10**.

Strengths:

- Clear ingestion-normalize-match-score-store pipeline.
- Practical FastAPI surface for operations.
- Useful React dashboard for validating system behavior.
- MongoDB indexes cover several common query paths.
- Source fetchers have retry/fallback behavior.

Risks:

- No authentication, authorization, rate limiting, or strict CORS.
- Some tests and verification scripts reference removed SQLAlchemy APIs.
- `main.py schedule` references `schedule_jobs()` and `run_once()` without importing them.
- `models_new.py`, `utils/helpers.py`, and `processors/result_formatter.py` are unused or placeholders.
- Sync progress is global process memory and not multi-instance safe.
- Matching is O(n²) and can become expensive as source volume grows.
- Write behavior may create duplicates because `create_shop` always inserts and no unique place key exists.
- Console logging and broad exception handling make production debugging harder.

See [docs/development-workflow.md](docs/development-workflow.md), [docs/scaling-strategy.md](docs/scaling-strategy.md), and [docs/troubleshooting.md](docs/troubleshooting.md).

## Future Roadmap

- Add authentication and role-based access for operations endpoints.
- Move ingestion to a dedicated worker with durable job state.
- Replace O(n²) matching with spatial buckets or geospatial indexes.
- Add canonical place IDs and idempotent upsert semantics.
- Convert test suite to `pytest` and remove SQLAlchemy-era assumptions.
- Add Dockerfile, docker-compose, and deployment manifests.
- Add structured logging, Prometheus metrics, and alerting.
- Add API request/response models for all endpoints.
- Add frontend integration tests and visual regression checks.
- Add OpenAPI examples and generated client types.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contributing.md](docs/contributing.md).

Quick workflow:

1. Create a branch: `feature/short-description`, `fix/short-description`, or `docs/short-description`.
2. Install backend and frontend dependencies.
3. Run import checks and frontend build before opening a PR.
4. Use Conventional Commits such as `feat: add geospatial bucket matching`.
5. Include screenshots for dashboard changes and sample API responses for API changes.

## License

This project is documented with an MIT license suggestion in [LICENSE](LICENSE). Confirm ownership and dependency constraints before publishing publicly.

## Final Improvement Checklist

- [ ] Add real authentication, authorization, CORS allow-list, and rate limiting.
- [ ] Fix stale tests and convert them to CI-friendly `pytest`.
- [ ] Add Dockerfile and docker-compose for backend, frontend, and MongoDB.
- [ ] Move sync jobs into a durable worker queue.
- [ ] Add structured logging and metrics.
- [ ] Add geospatial indexing/upserts to reduce duplicates and speed matching.
- [x] Add `.env.example` with safe placeholder values.
- [ ] Replace placeholder modules or remove them.
- [ ] Add screenshots under `docs/assets/`.
- [ ] Replace README badge `OWNER` placeholder after creating the GitHub repository.