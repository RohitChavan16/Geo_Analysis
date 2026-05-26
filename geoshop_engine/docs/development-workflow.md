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

## Verification Workflow

`test_mongodb.py` validates MongoDB configuration. `test_e2e.py` exercises the project structure, imports, API availability, frontend files, and demo pipeline flow. The next test evolution is to consolidate component checks into a MongoDB-backed `pytest` suite.

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

