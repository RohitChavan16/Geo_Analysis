# Contributing

GeoShop Engine welcomes focused, well-documented contributions.

## Local Setup

```bash
cd geoshop_engine
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python test_mongodb.py
python run_api.py
```

```bash
cd geoshop_engine/frontend
npm install
npm run dev
```

## Branches

- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`

## Commits

Use Conventional Commits:

- `feat: add worker-backed sync queue`
- `fix: prevent duplicate shop inserts`
- `docs: expand api reference`
- `chore: update ci workflow`

## Pull Requests

- Explain the problem and solution.
- Link related issues.
- Include test/verification notes.
- Add screenshots for UI changes.
- Update `/docs` and `README.md` when behavior changes.

## Current Test Caveat

Some legacy scripts still reference removed SQLAlchemy symbols. Prefer targeted import/build checks until those tests are rewritten around MongoDB.
