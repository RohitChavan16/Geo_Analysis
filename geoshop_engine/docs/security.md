# Security Review

## Current Security Posture

GeoShop Engine is currently a development/internal-demo service. It should not be exposed publicly without hardening.

## Implemented Controls

- Secrets are environment-driven.
- `.env` is ignored by git.
- MongoDB connection uses configured URI.
- User/data tokens in `find_similar_shops` are escaped before regex use.

## Gaps

- No authentication.
- No authorization.
- No rate limiting.
- CORS allows all origins.
- Debug endpoint can trigger external fetches.
- Raw exception strings can be returned to clients.
- No request body validation for write operations because trigger routes have no body.
- No dependency scanning or secret scanning workflow yet.

## Recommended Controls

- Add JWT/API-key auth.
- Protect `/api/sync/*`, `/api/update/*`, `/api/debug/*`, and database health.
- Restrict CORS by environment.
- Add reverse-proxy or app-level rate limiting.
- Add safe error responses in production.
- Rotate MongoDB credentials and restrict network access.
- Add GitHub secret scanning, Dependabot, and CodeQL.

## Data Classification

The system stores public place data and operational metadata. It can also store phone numbers, websites, and raw source records. Treat database exports as internal data because raw payloads may contain unexpected fields from upstream APIs.

