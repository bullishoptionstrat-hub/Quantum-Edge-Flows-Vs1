# Quantum Edge agent instructions

These rules govern every Quantum Edge path in this repository:
- `qe/` (canonical work);
- `QuantumEdge/` and `quantum-edge-terminal/` (legacy, quarantined);
- `quantum-edge-governance/` (the directive).

Quantum Edge is fenced inside the openclaw monorepo by decision A2-01 (ADR-0007). **The root `AGENTS.md`/`CLAUDE.md`, `pnpm check`, `pnpm test`, and the openclaw contribution rules do not apply here** (directive A4.1). Passing openclaw checks is no evidence about Quantum Edge.

## Authority

1. `quantum-edge-governance/QEGP_MASTER_PROMPT_v4.md` (QEGP-MASTER-4.0) is the governing directive. Read Parts A–C before changing anything.
2. `qe/DECISIONS.md` holds the decisions taken. `qe/DECISIONS_PENDING.md` lists what still needs a human.
3. `qe/PROJECT_STATE.json` gives the current phase and status.

## Hard rules (directive A5, B2)

- Never enable live trading, create or handle live credentials, or print secret values.
- Never report a test as passed if it was not run. Write `NOT RUN` and the reason.
- Never edit a test, fixture, threshold, or baseline to make a failing check pass. Golden fixtures are protected by `qe/spec/fixtures/MANIFEST.sha256`.
- Changing God's Plan semantics needs a spec version bump and an `AMBIGUITY_REGISTER.csv` entry. `qe/spec/GP_SPEC.md` is a PROPOSED draft until the operator freezes it.
- `QuantumEdge/` and `quantum-edge-terminal/` are read-only legacy (ADR-0008). Don't change their behavior. Reproduce their defects from `qe/tests/regression/legacy/` instead. Canonical code under `qe/` may never import them (`qe/tests/boundary/test_quarantine.py`).
- `qe/core` and `qe/gp` stay pure: no wall clock, randomness, I/O, broker, HTTP, database, or LLM imports.
- Don't modify openclaw paths (everything outside the four Quantum Edge paths) except `.github/workflows/quantum-edge.yml`.

## Commands

```bash
python3 -m venv qe/.venv && qe/.venv/bin/pip install -r qe/requirements-audit.lock   # once
PYTHONDONTWRITEBYTECODE=1 qe/.venv/bin/python -m pytest -c qe/pytest.ini --rootdir=.  # the gate
qe/.venv/bin/python qe/spec/fixtures/build_fixtures.py && git diff --exit-code qe/spec  # spec artifacts reproduce
bash qe/tools/run_phase0.sh                                                           # rebuild the Phase 0 audit
```

CI: `.github/workflows/quantum-edge.yml` runs the same gate on GitHub-hosted runners whenever a Quantum Edge path changes.

## Reporting

Use the directive's report format (G-R): what was done, the evidence level reached, what was not run, and what needs a human.
