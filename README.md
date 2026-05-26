# GeoShop Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/UI-React%20%2B%20Vite-61DAFB)](https://vite.dev/)
[![Database](https://img.shields.io/badge/Database-MongoDB-47A248)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GeoShop Engine is a production-inspired geospatial intelligence platform for detecting active, new, updated, and likely closed commercial places across Singapore. It combines multi-source ingestion, geospatial entity resolution, deterministic confidence scoring, operational sync workflows, MongoDB persistence, FastAPI services, and a React command center.

The project demonstrates backend architecture, data pipeline engineering, observability awareness, and system design thinking in a real-world problem space: commercial place data changes continuously across public registries, maps, and digital footprints. GeoShop Engine turns those signals into a structured synchronization pipeline that can be inspected, operated, and evolved.

## Engineering Highlights

- Multi-source ingestion across OpenStreetMap Overpass, data.gov.sg, OneMap, and configurable digital JSON-LD/snapshot sources.
- Category-aware Singapore place intelligence for restaurants, cafes, attractions, hotels, amusement parks, malls, department stores, grocery stores, pharmacies, and fuel stations.
- Geospatial matching engine using Haversine distance, normalized text similarity, source separation, and postal-code tie breakers.
- Confidence and decision scoring model that blends record quality, source diversity, coordinate validity, field completeness, and digital vitality.
- Real-time synchronization workflow with source counts, pipeline stages, live progress, sampled changes, and durable sync history.
- MongoDB document model with indexed `shops` and `sync_logs` collections for flexible source metadata and evolving signal payloads.
- FastAPI backend with operational endpoints for shops, sync status, change history, health checks, and pipeline inspection.
- React command center with live metrics, map visualization, sync monitor, change feed, trend chart, and dark/light mode.
- CLI and scheduler-oriented workflows for manual runs, demos, diagnostics, and recurring ingestion.
- Documentation suite covering architecture, API behavior, data design, security posture, scaling strategy, observability, deployment, and development workflow.

## What The System Does

GeoShop Engine answers operational questions such as:

- Which places are active according to multiple public and digital sources?
- Which new places appeared in the latest sync?
- Which previously active places are no longer observed?
- How confident is the system in each place record?
- Which signals contributed to an active, uncertain, or likely closed decision?
- How did the latest synchronization run behave across sources?

The system is intentionally explainable. Rather than hiding decisions behind opaque models, each stage produces inspectable data: raw source counts, normalized records, matched groups, confidence signals, decision signals, and sampled change records.

## Features

### Backend Systems

- FastAPI application in `api/main.py`.
- Background sync orchestration with `BackgroundTasks`.
- Parallel source fetching with `ThreadPoolExecutor`.
- Shop listing, search, proximity filtering, confidence filtering, stats, detail, and health endpoints.
- Sync trigger, progress, status, history, and change-feed endpoints.
- Pipeline inspection endpoint for debugging source counts, normalization, matching, and final scoring samples.
- MongoDB CRUD layer with active/inactive lifecycle management.
- Sync-log persistence with run ids, source counts, change summaries, sampled changes, timings, and status.

### Data Pipeline

- Source ingestion from OSM, data.gov.sg, OneMap, optional local snapshots, and optional JSON-LD listing pages.
- Retry, backoff, endpoint failover, pagination, record caps, and cache controls in source fetchers.
- Canonical normalization of heterogeneous upstream records.
- Domain-specific category classification and filtering.
- Cross-source entity resolution based on distance and fuzzy text similarity.
- Merge strategy that selects stronger names, addresses, coordinates, and contact/activity fields.
- Confidence scoring across source diversity, completeness, coordinate validity, and text quality.
- Digital-footprint scoring across official presence, map presence, contact/activity fields, vertical platform signals, and source reliability.
- New/update/closure detection through synchronization against the active shop set.

### Frontend Command Center

- Vite React dashboard.
- 5-second polling loop for operational visibility.
- Sync and real-time update controls.
- Live source counters and stage progress.
- Stat cards with animated values.
- Recharts trend visualization for openings, updates, closures, and net movement.
- Leaflet Singapore map with status-specific markers.
- Change feed showing reason, confidence, sources, coordinates, category, and contact fields.
- Persistent light/dark theme.

### Operations And Tooling

- `main.py` CLI pipeline runner with live and mock-data modes.
- `run_api.py` API server launcher.
- `scheduler/jobs.py` recurring pipeline runner.
- `test_mongodb.py` MongoDB connection diagnostic.
- Frontend build workflow through npm.
- GitHub Actions CI for active Python module imports and frontend production build.
- `.env.example` for safe configuration onboarding.

## Architecture Overview

```mermaid
flowchart LR
    OSM[OpenStreetMap Overpass] --> Fetch[data_fetchers]
    DG[data.gov.sg] --> Fetch
    OM[OneMap] --> Fetch
    DS[Digital snapshots / JSON-LD sources] --> Fetch
    Fetch --> Normalize[Normalization + category filtering]
    Normalize --> Match[Geospatial fuzzy matching]
    Match --> Merge[Canonical place merge]
    Merge --> Score[Confidence + vitality scoring]
    Score --> Sync[New / updated / closure detection]
    Sync --> Mongo[(MongoDB shops + sync_logs)]
    Mongo --> API[FastAPI operational API]
    API --> UI[React command center]
```

### Synchronization Flow

```mermaid
sequenceDiagram
    participant UI as React Dashboard
    participant API as FastAPI
    participant Worker as Background Sync
    participant Sources as Public + Digital Sources
    participant DB as MongoDB

    UI->>API: POST /api/sync/trigger
    API->>DB: create sync log
    API->>Worker: enqueue run_id
    API-->>UI: sync accepted
    Worker->>Sources: fetch sources in parallel
    Worker->>Worker: normalize, match, merge, score
    Worker->>DB: write shops and sync summary
    UI->>API: poll progress/history/changes
    API->>DB: read operational state
    API-->>UI: live dashboard data
```

## Engineering Design

### Ingestion Architecture

Each source fetcher owns provider-specific behavior, including pagination, retries, rate-limit handling, endpoint failover, token support, and response parsing. This keeps upstream integration complexity isolated from matching and scoring logic.

### Matching Architecture

The matching engine uses a deterministic, explainable approach:

- records from the same source are kept separate during cross-source matching;
- coordinates must pass a spatial gate;
- text similarity compares normalized name and address values;
- postal-code agreement acts as a strong tie breaker;
- merged records preserve raw source evidence for later inspection.

### Scoring Architecture

The system separates record confidence from operational decisioning:

- `confidence_score` measures data quality and source agreement;
- `digital_footprint_score` measures activity/vitality signals;
- `decision_score` blends the two into an operational signal;
- `decision_status` summarizes active, uncertain, or likely closed state.

This split makes the scoring model easier to tune and easier to explain.

### Operational Visibility

Sync state is visible through API endpoints and the dashboard:

- active run id;
- pipeline stage;
- stage message;
- source counts;
- matched groups;
- scored records;
- new/updated/closed counters;
- sync history;
- sampled change records;
- database health.

## Tech Stack

| Area | Technology |
| --- | --- |
| Frontend | React 18, Vite 5, Tailwind CSS, Leaflet, React Leaflet, Recharts, GSAP, Lucide React |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Database | MongoDB, PyMongo |
| Data Sources | OpenStreetMap Overpass, data.gov.sg, OneMap, configurable JSON-LD/snapshot sources |
| Synchronization | FastAPI background tasks, scheduler module, CLI workflows |
| Observability | Health endpoints, sync progress endpoint, sync history, database diagnostics, dashboard telemetry |
| Tooling | python-dotenv, requests, schedule, npm, Vite, GitHub Actions |
| Deployment Model | Python ASGI service, static frontend build, MongoDB/MongoDB Atlas |

## Folder Structure

```text
geoshop_engine/
├── api/
│   └── main.py                  # FastAPI routes, sync orchestration, progress tracking
├── config/
│   └── settings.py              # shared API configuration constants
├── data_fetchers/
│   ├── datagov_fetcher.py       # data.gov.sg metadata lookup, datastore paging, retry/cache
│   ├── digital_sources_fetcher.py # local snapshot and JSON-LD ingestion adapter
│   ├── onemap_fetcher.py        # OneMap category search and pagination
│   └── osm_fetcher.py           # Overpass API query and endpoint failover
├── db/
│   ├── crud.py                  # MongoDB shop and sync-log operations
│   ├── database.py              # connection setup and index initialization
│   └── models.py                # Pydantic document and API response models
├── docs/                        # architecture and engineering documentation
├── frontend/
│   ├── src/components/          # reusable dashboard UI components
│   ├── src/hooks/               # polling utility
│   ├── src/lib/api.js           # dashboard API client
│   ├── src/sections/            # sync, trend, map, and change-feed panels
│   └── src/App.jsx              # dashboard state orchestration
├── processors/
│   ├── category_filter.py       # domain category mapping and text classification
│   ├── matcher.py               # Haversine and fuzzy matching engine
│   ├── normalizer.py            # data.gov.sg normalization
│   └── result_formatter.py      # extension point for output shaping
├── scheduler/
│   └── jobs.py                  # recurring full-pipeline workflow
├── signal_engine/
│   ├── digital_footprint.py     # digital activity and source-reliability scoring
│   └── signal_calculator.py     # confidence and decision scoring
├── main.py                      # CLI pipeline runner
├── run_api.py                   # API server launcher
├── test_e2e.py                  # end-to-end diagnostics
├── test_mongodb.py              # MongoDB connectivity diagnostic
└── requirements.txt
```

## Installation

### Prerequisites

- Python 3.10 or newer.
- Node.js 18 or newer.
- MongoDB local instance or MongoDB Atlas cluster.
- Network access to public source APIs for live ingestion.

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

The API defaults to `http://localhost:8000`; OpenAPI docs are available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd geoshop_engine/frontend
npm install
npm run dev
```

Set `VITE_API_BASE=http://localhost:8000/api` when pointing the dashboard at a deployed API.

### CLI Pipeline

```bash
cd geoshop_engine
python main.py demo       # mock-data walkthrough
python main.py run        # live-source pipeline run
python -m scheduler.jobs  # recurring scheduler workflow
```

## Environment Variables

| Variable | Purpose | Example | Required |
| --- | --- | --- | --- |
| `APP_ENV` | Runtime environment label. | `development` | Optional |
| `APP_HOST` | API bind host. | `0.0.0.0` | Optional |
| `APP_PORT` | API port. | `8000` | Optional |
| `MONGODB_URL` | MongoDB connection string. | `mongodb+srv://user:pass@cluster/db` | Required for persistence |
| `DATABASE_NAME` | MongoDB database name. | `geoshop_engine` | Optional |
| `DATA_GOV_COLLECTION_ID` | data.gov.sg collection id. | `2` | Optional |
| `DATA_GOV_MAX_RECORDS` | Per-sync data.gov.sg record cap. | `1000` | Optional |
| `DATA_GOV_CACHE_TTL_SECONDS` | data.gov.sg cache TTL. | `3600` | Optional |
| `ONEMAP_ACCESS_TOKEN` | OneMap bearer token. | `eyJ...` | Optional |
| `ONEMAP_MAX_PAGES` | OneMap page cap per query. | `8` | Optional |
| `DIGITAL_SOURCE_FETCH_ENABLED` | Enables external digital-source ingestion. | `false` | Optional |
| `DIGITAL_SOURCE_SNAPSHOT_PATH` | Local JSON snapshot path. | `data/digital.json` | Optional |
| `DIGITAL_INFER_FROM_PRIMARY` | Derives digital-like records from primary source metadata. | `true` | Optional |
| `CHOPE_LISTING_URL` | JSON-LD listing source. | `https://...` | Optional |
| `BURPPLE_LISTING_URL` | JSON-LD listing source. | `https://...` | Optional |
| `WHYQ_LISTING_URL` | JSON-LD listing source. | `https://...` | Optional |
| `SHA_LISTING_URL` | JSON-LD listing source. | `https://...` | Optional |
| `MALL_DIRECTORY_URL` | JSON-LD listing source. | `https://...` | Optional |
| `MIN_CONFIDENCE_UPDATE` | Decision threshold for updating matched records. | `50.0` | Optional |
| `NEW_SHOP_CONF_THRESHOLD` | Decision threshold for new records. | `30` | Optional |
| `CLOSE_SHOP_CONF_THRESHOLD` | Decision threshold for closure candidates. | `30` | Optional |
| `SCHEDULER_INTERVAL_DAYS` | Scheduler interval configuration. | `3` | Optional |
| `LOG_LEVEL` | Runtime logging level configuration. | `info` | Optional |
| `VITE_API_BASE` | Frontend API base URL. | `http://localhost:8000/api` | Optional for frontend |

## API Documentation

Full endpoint details are in [docs/api-reference.md](docs/api-reference.md).

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | API health status. |
| `GET` | `/api/health/database` | MongoDB connectivity and collection counts. |
| `GET` | `/api/shops` | List/search active shops by pagination, name, location, or confidence. |
| `GET` | `/api/shops/stats` | Active and high-confidence shop counts. |
| `GET` | `/api/shops/{shop_id}` | Fetch one shop record. |
| `GET` | `/api/sync/status` | Latest sync status and shop lifecycle counts. |
| `GET` | `/api/sync/progress` | Live sync progress state. |
| `GET` | `/api/sync/history` | Recent sync runs. |
| `GET` | `/api/sync/changes` | Latest or selected run change summary. |
| `POST` | `/api/sync/trigger` | Start the standard sync workflow. |
| `POST` | `/api/update/realtime` | Start the real-time update workflow with threshold tuning. |
| `GET` | `/api/debug/pipeline-data` | Inspect pipeline source, normalization, matching, and scoring stages. |

## Database Design

MongoDB stores operational and analytical state in two primary collections:

- `shops`: canonical place records with source metadata, coordinates, confidence fields, decision signals, lifecycle flags, raw evidence, and timestamps.
- `sync_logs`: synchronization history with run ids, status, source counts, change summaries, sampled changes, and completion metadata.

Indexes are initialized for name, address, coordinates, sources, confidence, active state, update time, sync run id, and sync start time. See [docs/database-design.md](docs/database-design.md).

## Observability And Operations

GeoShop Engine includes operational visibility at both API and dashboard levels:

- service health through `/api/health`;
- database health through `/api/health/database`;
- aggregate sync status through `/api/sync/status`;
- live stage progress through `/api/sync/progress`;
- durable run history through `sync_logs`;
- source-level counts and sampled changes in the dashboard;
- MongoDB diagnostic script for connection validation.

The observability roadmap expands this foundation with structured logs, metrics export, dashboards, and alerting. See [docs/monitoring-observability.md](docs/monitoring-observability.md).

## Performance Engineering

Implemented performance-oriented decisions:

- parallel source fetches during real-time sync;
- in-memory TTL cache for data.gov.sg responses;
- cached pipeline inspection payloads;
- MongoDB indexes for common read paths;
- concurrent dashboard API requests;
- map marker cap for smooth Leaflet rendering;
- source record caps and pagination controls.

Architecture evolution areas include spatial bucketing, geospatial indexes, durable worker queues, incremental diffs, and frontend marker clustering. See [docs/performance-optimization.md](docs/performance-optimization.md).

## Deployment

GeoShop Engine can be deployed as:

- FastAPI ASGI backend;
- static Vite frontend build;
- MongoDB or MongoDB Atlas persistence layer.

Recommended production-inspired topology:

```text
Browser -> static frontend host/CDN -> FastAPI API -> MongoDB
                                      -> source APIs
```

The deployment roadmap includes containerization, managed worker execution, environment-specific configuration, reverse proxying, and metrics-aware release workflows. See [docs/deployment.md](docs/deployment.md).

## Screenshots And Demo


Demo flow:

1. Start MongoDB and the FastAPI server.
2. Start the Vite dashboard.
3. Trigger a sync from the command center.
4. Watch stage progress, source counts, map markers, trends, and change records update.

## Engineering Decisions

### Flexible Document Storage

MongoDB supports heterogeneous upstream payloads and evolving scoring metadata while preserving raw source evidence for later inspection.

### Explainable Entity Resolution

The matcher uses deterministic geospatial and text rules so sync behavior can be reasoned about, tested, tuned, and communicated.

### Separation Of Confidence And Decisioning

Record quality and operational status are scored separately, allowing the system to evolve each dimension independently.

### Operational Dashboard First

The React command center is built around operator visibility: live counters, status, trends, maps, and explanations for detected changes.

### Evolutionary Architecture

The codebase is structured so ingestion, normalization, matching, scoring, persistence, API routes, and UI panels can evolve independently.

## Architecture Evolution Roadmap

- Add role-aware access control for operational endpoints.
- Move sync execution into a durable worker/job architecture.
- Introduce spatial bucketing and MongoDB geospatial queries for larger datasets.
- Add canonical place identifiers and idempotent upsert workflows.
- Expand structured logging, metrics, dashboards, and alerting.
- Add Docker and compose-based local infrastructure.
- Strengthen automated tests around matching, scoring, API contracts, and dashboard flows.
- Add OpenAPI examples and generated client types.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contributing.md](docs/contributing.md).

Contributor workflow:

1. Create a focused branch such as `feature/geospatial-indexing` or `docs/api-examples`.
2. Install backend and frontend dependencies.
3. Make scoped changes with documentation updates.
4. Run relevant verification, including frontend build for UI changes.
5. Use Conventional Commits such as `feat: add source fetch metrics`.
6. Open a PR with context, verification notes, and screenshots where helpful.

## License

MIT License. See [LICENSE](LICENSE).

## Reviewer Notes

This repository is designed to demonstrate practical systems engineering:

- backend service design with FastAPI;
- multi-source data ingestion;
- geospatial entity resolution;
- deterministic scoring and explainability;
- operational sync workflows;
- MongoDB data modeling;
- frontend observability dashboards;
- scalability and production-hardening awareness;
- professional open-source repository structure.
