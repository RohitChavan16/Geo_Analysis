# Development Workflow

## Backend

```bash
cd geoshop_engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_api.py
```

## Frontend

```bash
cd geoshop_engine/frontend
npm install
npm run dev
```

## Useful Commands

```bash
python main.py demo
python test_mongodb.py
python -m scheduler.jobs
cd frontend && npm run build
```

## Testing Reality

`test_mongodb.py` is current for MongoDB diagnostics. `test_e2e.py` partially reflects the current API but assumes a running server and hard-coded local paths.

`test_pipeline.py` and `verify.py` reference removed SQLAlchemy symbols such as `init_db`, `SessionLocal`, `Shop`, and `SyncLog`. These should be rewritten before being used as quality gates.

## Branch Naming

- `feature/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`
- `chore/<short-name>`

## Commit Convention

Use Conventional Commits:

- `feat: add source fetch metrics`
- `fix: escape shop search regex`
- `docs: document deployment topology`
- `chore: add ci workflow`

