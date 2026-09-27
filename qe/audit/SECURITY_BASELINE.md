# Security Baseline (P0-09)

## Secret scan

- **Working tree, both subtrees:** pattern scan for provider key shapes (`PK…` Alpaca-style, `AKIA…`, `sk-…`, `ghp_…`) and generic `key/secret/password/token = "<12+ chars>"` assignments (`static_flags.csv`, `secret_like`).
  - Two hits, `production/PHASE8_PRODUCTION_EXAMPLE.py:66-67`. Both values contain placeholder wording (checked without printing the values). **Not secrets.**
- **Full git history** (`git log --all -p` over both subtrees, all refs): 0 matches for the provider key shapes.
- **Hard-coded credential:** `quantum-edge-terminal/docker-compose.yml:9` sets `POSTGRES_PASSWORD` to an 11-character literal, and the same value is embedded in `DATABASE_URL` (lines 40 and 72). This is a dev default, but it is committed. **If this value is used on any reachable host, rotate it** (D-034). The value is deliberately not reproduced in any audit artifact.
- `.env.example` files contain placeholders only.

Limitations: pattern-based scanning, not an entropy scanner such as gitleaks or trufflehog, which weren't installed. Directive E8 requires a real secret-scanning step in CI.

## Exposed surfaces (Docker Compose)

| Surface | Finding |
|---|---|
| Postgres `5432:5432`, Redis `6379:6379` | Published on all host interfaces. Redis has no password configured |
| Backend `3001` | Wildcard CORS (`Access-Control-Allow-Origin: *`), no auth middleware, unauthenticated `POST`/`PUT` on `/api/signals` and `POST` on `/api/alerts` |
| AI engine | FastAPI endpoints without auth. It accepts arbitrary candle payloads |
| TradingView webhook | No receiver is hosted. The library has no auth or replay protection (D-016) |

## Dependencies

- `ai-engine/requirements.txt` (2023-era pins): `pip-audit 2.7.3` found **51 known vulnerabilities in 7 packages**: aiohttp 3.9.1 (38), starlette 0.27.0 (7), anyio 3.7.1 (2), and one each in fastapi 0.104.1, scikit-learn 1.3.2, python-dotenv 1.0.0, and pytest 7.4.3. Full report: `qe/audit/pip_audit_ai_engine.json`. Command: `pip-audit -r quantum-edge-terminal/ai-engine/requirements.txt -f json`. Run 2026-09-23 against the PyPI/OSV advisory data available that day.
- The backend and frontend `package.json` have no lockfile in the subtree. **NOT RUN.**

## Credentials policy status (directive 81)

- No live credentials exist in the repository, and none were requested or used during Phase 0.
- There is no paper/live key separation yet, because no broker integration exists.
