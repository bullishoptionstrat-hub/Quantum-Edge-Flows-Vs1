# Phase 0 Baseline (P0-01)

| Item | Value |
|---|---|
| Repository | `bullishoptionstrat-hub/Quantum-Edge-Flows-Vs1` |
| Audited commit | `361e92ac` on `claude/quantum-edge-review-8lxi0f` (= `416e34ec` on `main` + the QEGP-MASTER-4.0 directive, which touches no code) |
| Working tree at audit start | clean |
| Git history | not shallow; 3 commits on `main` (`6d34d9e` initial commit, then a Dependabot bump and its merge). No earlier Quantum Edge history exists in this repo. |
| OS | Linux 6.18 x86_64 (cloud container) |
| Python | 3.11.15 |
| Node | 22.22.2 (not used by Phase 0; no Quantum Edge JS tests exist) |
| Audit environment | `qe/.venv`, created from `qe/requirements-audit.lock` (73 pinned packages; top-level pins in `qe/requirements-audit.in`) |
| External services required by Phase 0 | none. The import sweep runs with outbound network pointed at a dead proxy. |

## Scope

The two Quantum Edge subtrees: **538 tracked files**.

| Subtree | Files | Python | Notes |
|---|---|---|---|
| `QuantumEdge/` | 383 | 97 | LEAN sector-rotation/IBS algorithm, fib..fib9 research, 231 JSON files (almost all run results), 52 logs (93 MB of output) |
| `quantum-edge-terminal/` | 155 | 89 | AI engine, execution, validation, production, TradingView bridge, 3 Pine scripts, Express backend, Next.js frontend, 18 backtests, 38 documentation and status files |

The rest of the repository is the openclaw monorepo and is out of scope (directive A4).

## Configuration sources found

- `quantum-edge-terminal/.env.example`, `backend/.env.example`, `frontend/.env.example`: placeholders.
- `quantum-edge-terminal/docker-compose.yml`: Postgres, Redis, backend, frontend, ai-engine. It contains a literal Postgres password (D-034; value not reproduced here).
- `QuantumEdge/config.json`: an empty LEAN parameters block. `QuantumEdge/algorithm/config.py` holds the algorithm constants.
- `quantum-edge-terminal/ai-engine/requirements.txt`: pins for the AI engine (pandas 2.1.3, numpy 1.26.2, and others). The audit environment uses newer compatible pins. See `requirements-audit.in`.

## How to reproduce every generated artifact

```bash
bash qe/tools/run_phase0.sh
```

This rebuilds `REPOSITORY_INVENTORY.csv`, `python_imports.json`, `static_flags.csv`, `import_sweep.csv`, and `DEFECT_REGISTER.csv`, then runs the 30 legacy defect reproductions. Two consecutive runs produced byte-identical artifacts (checked with sha256).

Hand-written artifacts (markdown, `TEST_REALITY_MATRIX.csv`, `SEED_FINDING_VERIFICATION.csv`, `DOCUMENTATION_CONTRADICTIONS.csv`, `RESEARCH_PROVENANCE.csv`, `EVIDENCE_MATURITY_MATRIX.csv`) cite the file:line or test that supports each row.
