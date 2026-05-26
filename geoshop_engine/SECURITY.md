# Security Policy

## Supported Versions

This repository is pre-1.0 from a production-hardening perspective. Security fixes should target the default branch unless a release branch exists.

## Reporting A Vulnerability

Please do not open a public issue for suspected vulnerabilities. Contact the maintainers privately with:

- affected endpoint or file;
- reproduction steps;
- impact;
- suggested fix, if known.

## Known Security Gaps

- API authentication is not implemented.
- CORS is permissive.
- Rate limiting is not implemented.
- Debug and sync-triggering endpoints are unauthenticated.

Do not expose this service to the public internet until these gaps are addressed.
