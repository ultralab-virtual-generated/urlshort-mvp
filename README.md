# Simple URL Shortener (MVP)

A minimal FastAPI service to create short URLs, redirect, collect per-visit analytics, and generate QR codes. Container-first, deterministic dependencies, and deployable to Fly.io.

Features
- Create short URLs via HTTP API
- Redirect by short code
- Track click count and last access timestamp per short URL (plus per-visit timestamp, user-agent, IP)
- Generate QR codes for short URLs

Quick Start (Local)
- Requirements: Docker
- Build: docker build -t urlshort-mvp .
- Run: docker run -p 8080:8080 urlshort-mvp
- API: http://localhost:8080/docs

API
- POST /api/shorten {"url": "https://example.com"}
- GET /{code}
- GET /api/{code}/stats -> { code, long_url, total_clicks, last_access, recent: [...] }
- GET /api/{code}/qr
- GET /healthz

Testing
- Build image: docker build -t run-6-mvp:latest .
- Run tests in container (mount project to include tests):
  docker run --rm \
    -e TMPDIR=/app/logs/tmp \
    -e PYTHONPATH=/app \
    -v "$PWD":/app -w /app \
    run-6-mvp:latest pytest -q
- Logs are written to logs/test.log when run via the provided automation.

Deployment (Fly.io)
- Configure app name in fly.toml
- Set secrets (if any) and deploy via GitHub Actions workflow dispatch or flyctl

Notes
- City resolution is intentionally omitted (no external API). IP is recorded.
- Storage is lightweight file-based SQLite; override DB_PATH to use a different path.

Repo conventions
- Code: src/
- Tests: tests/
- Workflows: .github/workflows/
- Logs: logs/