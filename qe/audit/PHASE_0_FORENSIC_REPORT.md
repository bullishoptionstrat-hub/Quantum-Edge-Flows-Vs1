# Phase 0 Forensic Report

**Directive:** QEGP-MASTER-4.0 · **Audited commit:** `361e92ac` · **Date:** 2026-09-23 · **Mode:** AUDIT
**Regenerate the machine artifacts:** `bash qe/tools/run_phase0.sh`

---

## 1. Failures and refuted claims (first, per B4.5)

1. **None of the terminal's test files can run.** 0 of 3 `quantum-edge-terminal/tests/*.py` files collect. Two fail on OpenTelemetry symbols that no longer exist (D-028), and one fails on a `TypeError` in the execution engine's dataclass (D-001). The documents claiming "43 tests, 95% coverage" and "99.5% production ready" are contradicted (`DOCUMENTATION_CONTRADICTIONS.csv`).
2. **Most of the terminal can't be imported.** The `execution`, `production`, `validation`, `interface`, and `observability` packages all fail to import. That's 53 of 186 Python modules failing or not parsing (`import_sweep.csv`).
3. **No order can reach any broker.** Both broker modules are mocks. One always crashes (D-040). The other logs "REAL EXECUTION" without sending anything (D-029).
4. **The claimed pipeline doesn't exist.** `ExecutionEngine`, `RiskEngine`, `TradeJournal`, and the TradingView receiver are never instantiated by any runnable code (D-038).
5. **The headline performance numbers come from synthetic data.** "43.1% WR, 1.99 PF" and similar come from backtests on `random.gauss` random walks. One backtest draws wins with `random.random() > 0.55` (D-030).
6. **The QuantumEdge research can't be reproduced from this repo.** The data (`lean/Data`) is absent, and the run manifests cite commit `77509024b8`, which isn't in this repo, with a dirty tree (D-035). 3 of 4 data-presence tests fail.
7. **God's Plan isn't implemented anywhere, and there is no SMT** (D-037, D-036).
8. **Refuted:** lookahead in the sampled research detectors. `fib`, `fib2`, and `fib3` wait for pivot confirmation and enter at the next bar's open (`LOOKAHEAD_THREAT_MODEL.md` L1, L3). This is the strongest code in the repository.

## 2. Verified facts, with evidence level

| Fact | Level | Evidence |
|---|---|---|
| All 14 seed findings from directive Appendix 1 hold. 12 have executable reproductions, and 2 (S-12 hard-coded confidences, S-14 absence of SMT) are source/grep facts | L2 (test) / L1 | `SEED_FINDING_VERIFICATION.csv`, `test_legacy_defects.py` |
| S-01 (field mismatch) is real but not reachable today, because the two engines are never connected | L1 | D-002, D-038 |
| 30 legacy defects reproduce under strict xfail | L2 | `30 xfailed` |
| Instruments in the repo are US equity ETFs. There is no futures data, contract metadata, or roll logic | L1 | `DATA_AUTHORITY_MAP.md` |
| The only Python service (the `ai-engine` FastAPI app) crashes at startup with its own pinned requirements, so no Python service in the repo runs. Its sweep/CHoCH/FVG detector is defective as a library | L2 (command run) | D-044, D-019..D-022 |
| The AI engine's pinned dependencies carry 51 known vulnerabilities | L2 (tool run) | `pip_audit_ai_engine.json` |
| No credentials are committed, apart from a dev Postgres password in docker-compose | L1 | `SECURITY_BASELINE.md` |
| Phase 0 generated artifacts are deterministic (two runs, identical sha256) | L2 | `BASELINE.md` |

## 3. Files

- **Inspected:** all 538 files in `QuantumEdge/` and `quantum-edge-terminal/` were statically scanned. All 186 Python modules were import-tested. Line-level reading covered execution, risk, broker, live connector, TradingView bridge, scorecard, journal, market-structure detector, telemetry config, backend server and routes, schema, docker-compose, the Pine alert calls, `fib`/`fib2`/`fib3`/`fib4` detectors and backtesters, the fib5/fib7 cost handling, and the status documents cited in `DOCUMENTATION_CONTRADICTIONS.csv`.
- **Changed:** none in the legacy subtrees. Created: `qe/` (audit artifacts, tools, tests, pinned environment spec, project state, decisions).

## 4. Commands and results

| Command | Result |
|---|---|
| `qe/.venv/bin/python -m pytest -q tests/test_data_presence.py` (in `QuantumEdge/`) | 1 passed, 3 failed (data absent) |
| `qe/.venv/bin/python -m pytest -q tests/<each>.py` (in `quantum-edge-terminal/`) | 3 of 3 collection errors |
| Same, with OpenTelemetry 1.21.0 plus the jaeger exporter | Still fails (`ProbabilitySampler`) |
| `qe/.venv/bin/python qe/tools/import_sweep.py` | OK 127, IMPORT_ERROR 51, SYNTAX_ERROR 2, SKIPPED 6 |
| `qe/.venv/bin/python -m pytest -c qe/pytest.ini --rootdir=.` | 30 xfailed |
| `bash qe/tools/run_phase0.sh`, run twice, then sha256 comparison | identical |
| `pip-audit -r quantum-edge-terminal/ai-engine/requirements.txt` | 51 vulnerabilities in 7 packages |
| Secret-pattern scan of the working tree and full git history | 0 real secrets. 1 committed dev password |
| TypeScript backend/frontend build or tests | **NOT RUN** (no tests exist and there's no lockfile in the subtree) |
| LEAN algorithm (`QuantumEdge/main.py`) | **NOT RUN** (needs the LEAN runtime and data) |
| Postgres schema load | **NOT RUN** (D-042 is from reading the source) |

## 5. Research results (separate from engineering)

- There is **no market evidence for or against God's Plan in this repository**, because no GP implementation or futures data exists.
- **Existing search history, for directive F6:** 18 terminal backtests (17 synthetic, 1 on unpinned yfinance data), and 184 committed result files covering 143 distinct configuration names across `output/experiments` and `fib`–`fib4`, plus 11 LEAN runs and 17 logged LEAN configurations. fib5–fib9 define further variants but have no committed outputs. `RESEARCH_PROVENANCE.csv` has the details.
- Every research result in the repo is `NOT_EVIDENCE` (synthetic) or `NOT_REPRODUCIBLE` (data and commit absent).

## 6. New defects (beyond the 14 seeds)

43 register entries in total: 15 CRITICAL, 22 HIGH, 6 MEDIUM (`DEFECT_REGISTER.csv`). The most consequential new ones:

- **D-001:** the execution engine can't be imported, which takes down every package that depends on it.
- **D-010:** the risk engine never enforces its per-trade risk or drawdown limits.
- **D-027:** the validation and interface packages aren't valid Python.
- **D-030:** the performance claims come from synthetic data.
- **D-037:** God's Plan doesn't exist in code.
- **D-040:** the mock broker crashes on every call. Its code would return `accepted` in LIVE mode without contacting a broker.
- **D-024/D-025:** the journal reports losses as +R, and records P&L in points instead of dollars.
- **D-026:** Pine alerts can't be parsed by the bridge.
- **D-034:** the API is unauthenticated and the DB and Redis ports are exposed.
- **D-042:** the schema uses MySQL syntax, which Postgres rejects.
- **D-043:** the AI engine's dependencies carry 51 known vulnerabilities.
- **D-044:** the AI engine crashes at startup with its own pinned requirements.

## 7. Evidence maturity by component

See `qe/evidence/EVIDENCE_MATURITY_MATRIX.csv`. The highest level any component reaches is **L1 (source exists)**. No component reaches L2 behavior-tested status. GP state machine, SMT, data quality, instrument registry, and replay are **MISSING**.

## 8. Pending A2 decisions

See `qe/DECISIONS_PENDING.md`.

- **A2-00:** the source of the GP specification. Blocks Phase 1 and 2.
- **A2-01:** repository layout (extract into its own repo, or fence inside the monorepo).
- **A2-02:** scope of the LEAN sector strategy.
- **A2-03:** the committed Postgres password.

## 9. Risk register (top five)

1. **Narrative risk.** About 20 status documents claim production readiness that the code contradicts. Anyone reading the docs instead of running the code would believe a working system exists. Mitigation: `DOCUMENTATION_CONTRADICTIONS.csv`, and treat every status document as L0.
2. **Accidental safety.** There is no live exposure today only because imports are broken. A naive "fix" of D-001 would re-enable a mock broker that returns `accepted` in LIVE mode. Mitigation: quarantine plus an import-ban test (Phase 1). Never repair legacy execution modules in place.
3. **No data.** GP research needs licensed intraday futures data, and none exists here. This is the long pole for Phases 4 and 5.
4. **Spec absence.** The strategy the directive governs has no in-repo definition (A2-00).
5. **Exposed services.** If the Docker Compose stack runs anywhere reachable, the API and DB are open (D-034, D-043).

## 10. Next highest-leverage action

Decide **A2-00**: commit the God's Plan source document into `qe/spec/source/`. Phase 1's rule-divergence matrix and Phase 2's formalization both need it. Everything else in Phase 1 (divergence of the existing detectors, the quarantine test) can start as soon as it's in place.

---

## Final question

> *Based only on reproducible evidence from commit `361e92ac`, what does Quantum Edge actually do today, what does it partially do, what is prototype-only, and what does documentation merely claim it does?*

**What it actually does:**
- No Python service runs. The `ai-engine` FastAPI app crashes at startup with its own requirements (D-044). Its detector modules work as a library, and their sweep, CHoCH, and FVG logic is demonstrably wrong (D-019..D-022).
- Contains a careful, well-documented ETF Fibonacci "manipulation leg" research framework (`QuantumEdge/research/fib`–`fib9`). It imports cleanly and avoids lookahead in the parts audited. It can't produce results from this repo because its data is absent.
- Contains a LEAN ETF sector-rotation algorithm that needs the LEAN runtime and data, neither of which is present.
- Ships an Express/Next.js dashboard over Postgres tables that anything on the network could write to. It was **not run** in Phase 0, and its schema uses MySQL-only syntax that Postgres rejects (D-042), so the stack as committed probably doesn't start cleanly.

**What it partially does:**
- The risk engine, trade journal, scorecard, and TradingView bridge load on their own and compute something. Each gives wrong or fail-open answers on basic cases (30 reproduced defects), and none is connected to anything that runs.

**What is prototype-only:**
- The execution engine, broker connection, order managers, kill switch, staged capital deployment, shadow comparator, validation orchestrator, safety controls, alert engine, observability, and production runner. None of them can be imported, and the broker paths are mocks that never contact a broker.

**What documentation merely claims:**
- A production-ready, tested (43 tests, 95% coverage), Alpaca-integrated trading system with validated performance (for example 43.1% WR / 1.99 PF). The tests don't run, there is no broker integration, and the performance figures come from random-walk simulations.
- Everything God's Plan-specific (the sequence, SMT, one-attempt lineage, net 2R) exists only in documents outside this repository.
