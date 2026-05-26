# Contributing

Thanks for improving GeoShop Engine.

## Before Opening A PR

- Keep changes scoped.
- Update docs when behavior changes.
- Include screenshots for dashboard UI changes.
- Include sample request/response payloads for API changes.
- Run frontend build and relevant Python import checks.

## Pull Request Process

1. Create a focused branch.
2. Make implementation and documentation changes.
3. Run local verification.
4. Open a PR using the template.
5. Respond to review comments with follow-up commits.

## Coding Standards

- Prefer explicit, readable Python over clever abstractions.
- Keep source fetchers isolated by provider.
- Keep scoring rules explainable and deterministic.
- Do not commit secrets or real `.env` values.
- Use environment variables for deploy-time configuration.

## Issue Reports

Include:

- environment;
- command or endpoint;
- expected behavior;
- actual behavior;
- logs or response body;
- reproduction steps.

