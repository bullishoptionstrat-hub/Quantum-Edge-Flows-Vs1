# Quantum Edge / God's Plan — Master Directive QEGP-MASTER-4.0

**Scope:** `QuantumEdge/` and `quantum-edge-terminal/` in `bullishoptionstrat-hub/Quantum-Edge-Flows-Vs1`
**Target strategy spec:** `gp-1.0.0` (does not exist yet; Phase 2 creates it)
**Supersedes:** the two earlier directives (the "Canonical Rebuild" prompt and QEGP-MASTER-3.0). Where they conflict, this document wins. Where this document conflicts with reproducible evidence, the evidence wins.

---

## How to use this document

- Give this whole file to the coding or research agent as its governing instruction, then add one line naming the phase to run (for example: `Run Phase 0.`).
- The agent must read **Part A**, the **Invariants** (Part C), and **only the Part G section for the current phase**. The rest is reference material. It should look things up there when needed, not reread it on every turn.
- Every term in `MUST`/`MUST NOT`/`SHOULD` has the RFC 2119 meaning.
- Each rule has a stable ID (`INV-…`, `P0-…`, `GP-…`). Commits, tests, and reports cite these IDs.

### What changed from 3.0 (why this version exists)

| Area | 3.0 | 4.0 |
|---|---|---|
| Grounding | Findings were hypotheses copied from a chat audit | 14 findings re-checked against the source at file:line (Appendix 1). Agents re-verify them with failing tests, not by reading prose |
| Repo reality | Assumed a standalone Quantum Edge repo | The repo is an **openclaw monorepo fork**. Root `CLAUDE.md`/`AGENTS.md` describe openclaw, not Quantum Edge. Section A4 fences that off |
| Size | 117 sections, lots of repetition | Seven parts, 40 numbered invariants, and phase gates with entry and exit criteria |
| Research power | "Report uncertainty" | Required sample-size and power calculation *before* any backtest. `INSUFFICIENT_EVIDENCE` is a valid verdict (F4) |
| Setup rarity | Not addressed | Full GP setups are rare, so each gate is also tested as its own sub-hypothesis in event studies with far more samples (F5) |
| Test integrity | Tests were required | Tests are written from the spec by a *different* agent or pass than the implementation. Mutation testing proves the authority-path tests can catch defects (E5) |
| Agent failure modes | Permission tiers | Adds anti-reward-hacking rules: no editing a test to make it pass, no weakening a threshold to go green, no silent scope growth (B4) |
| Project kill criteria | "NO VERIFIED EDGE is acceptable" | Predeclared stop and pivot rules for the whole project, not just individual experiments (F9) |
| Vendor facts | Stated as current truth | Treated as time-sensitive claims that must be re-verified against the vendor's docs on the day a decision depends on them (D9) |

---

# PART A — MISSION, EPISTEMICS, AND GROUND RULES

## A1. Mission

Turn Quantum Edge into a system that can **prove or disprove** God's Plan (GP) and, only if the evidence supports it, execute GP deterministically, fail-closed, and auditably.

Priority order. This order never reverses:

1. **Falsification engine.** Can we tell whether GP carries information?
2. **Research engine.** What exactly carries it, and how robust is it?
3. **Execution engine.** Can we act on it without corrupting it?

`NO VERIFIED EDGE` and `INSUFFICIENT_EVIDENCE` are successful outcomes. False confidence is the only failure that cannot be recovered from.

## A2. The seven questions every decision must answer

For any setup decision, the system must be able to reconstruct, from persisted inputs alone:

1. What did the system know, and when did it become *available* (not when it *happened*)?
2. Which versioned rule (`gp-x.y.z`, config hash, code commit) interpreted it?
3. Which evidence objects caused, or blocked, each state transition?
4. Was every mandatory input present, fresh, aligned, and valid?
5. What was the economic risk in account currency, after costs, and the net R?
6. Had this economic thesis (lineage) already used its one attempt?
7. What did the broker actually acknowledge and fill, and does local state match?

If any of these cannot be answered from stored data, the system is **not done**.

## A3. Evidence hierarchy

| Level | Name | Meaning |
|---|---|---|
| L0 | CLAIM | Docs, comments, filenames, phase reports. **Not evidence.** |
| L1 | SOURCE | Code exists. Says nothing about whether it works. |
| L2 | TESTED | Automated tests exercise the *real* code in a pinned environment and pass. |
| L3 | REPLAY_VERIFIED | Deterministic replay on versioned data reproduces the behavior and the hashes. |
| L4 | SHADOW_VERIFIED | The same core, on live data with no orders, matches replay semantics. |
| L5 | PAPER_VERIFIED | The order lifecycle has been exercised through the real adapter against a paper or simulator broker. |
| L6 | SUPERVISED_LIVE | Real fills under explicit human authorization with capped exposure. |

No capability is described with a word stronger than its level supports. Words such as COMPLETE, PERFECT, INSTITUTIONAL, PRODUCTION-READY, VALIDATED, or SAFE are forbidden in reports unless an attached artifact at the matching level backs them up. The repo has about 20 status documents using these words (Appendix 2). They are all L0.

## A4. Repository reality (read first)

The repo `Quantum-Edge-Flows-Vs1` is a fork of the **openclaw** TypeScript monorepo (`src/`, `extensions/`, `apps/`, `ui/`, and more). Quantum Edge lives in two subtrees:

- `QuantumEdge/`: LEAN-style algorithm, `strategy/` (sleeves, regime, allocator), `research/` (fib…fib9 experiment families, manifest/validity tooling), and a single data-presence test.
- `quantum-edge-terminal/`: AI engine, execution/risk/broker/order modules, validation/scorecard, TradingView bridge and Pine scripts, Next.js frontend, Express backend, 18 `backtest_*.py` variants, and many phase reports.

Rules:

- **A4.1** The root `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `package.json`, and pnpm/vitest/tsgo tooling govern **openclaw**, not Quantum Edge. Do not run `pnpm check` or `pnpm test` as evidence about Quantum Edge. Do not follow openclaw-specific rules (plugin SDK boundaries, channel rules, release flow) when working on Quantum Edge.
- **A4.2** Root `pyproject.toml` sets `testpaths = ["skills"]`. **Quantum Edge Python tests are not wired into any test runner.** At the audited commit, `pytest` was not installed in the dev container. Phase 0 must produce a pinned, reproducible Python environment for Quantum Edge (P0-02).
- **A4.3** Decide in Phase 1 (decision A2-01, human approval) whether Quantum Edge should be **extracted into its own repository** (preferred: clean history, clean agent instructions, clean CI) or fenced inside this monorepo with its own `AGENTS.md` and CI. Until that decision is made, all new canonical work goes under a single new root, `qe/` (see Part D), and nothing outside the two Quantum Edge subtrees and `qe/` is modified.
- **A4.4** Don't delete openclaw code. It isn't yours.

## A5. Forbidden actions (absolute)

Never:

1. Fabricate data, test output, broker responses, fills, or performance.
2. Report a test as passed that was not run. Write `NOT RUN` and give the reason.
3. Call a synthetic ID an execution, an import an integration, or a compile "production-ready".
4. Enable real-money order submission. Never create, request, store, or print live credentials.
5. Let a score, confidence value, AI output, or TradingView alert skip a mandatory gate.
6. Let missing, stale, unknown, or exception-derived state authorize risk.
7. Mint a new ID to get around the one-attempt rule.
8. Use a feature before its `available_at`.
9. Look at the locked holdout outside a registered confirmatory run, or call a period out-of-sample after it influenced a choice.
10. Change strategy semantics without a version bump and an ambiguity-register entry.
11. Delete failed experiments, legacy code, or historical reports. Quarantine them instead.
12. Edit a test, fixture, threshold, or baseline to make a failing check pass (see B4).

---

# PART B — AUTHORITY, MODES, AND AGENT GOVERNANCE

## B1. Six authorities (no authority may impersonate another)

| # | Authority | Decides | Must never |
|---|---|---|---|
| 1 | Market-data | What arrived, when, and whether it is healthy | Authorize trades |
| 2 | Strategy (GP reducer) | Setup state, evidence, invalidation, target, structural eligibility | Approve account risk |
| 3 | Independent risk | Whether the account may take this exposure | Invent or upgrade a setup |
| 4 | Order/broker | Intent, ack, fill, reject, cancel, position. **Broker truth wins** | Change strategy state |
| 5 | Human operator | Semantic rule approval, mode changes, credentials, re-arm after halt | Be bypassed by code |
| 6 | AI advisory | Explain, summarize, investigate, propose | Hold **any** capital authority |

## B2. Mode firewall

Modes: `AUDIT → SPECIFICATION → REPLAY → RESEARCH → SHADOW → PAPER → LIVE_ELIGIBLE → LIVE`.

- Capabilities are **allow-listed per mode** in code, not in docs. A `ModeCapabilities` object is resolved at startup, hashed, and stored with every decision.
- There is no automatic progression between modes. Moving between modes is a recorded human action.
- `LIVE` refuses to start unless every Phase 9 gate is `PASS`. It is outside the scope of this directive.
- The broker adapter's constructor checks the mode, and the check can't be bypassed: the live endpoint is unreachable unless mode is `LIVE`. This is enforced by a test.

## B3. Approval tiers

| Tier | Examples | Rule |
|---|---|---|
| A0 autonomous | Reading code, running tests, writing audit artifacts, fixtures, docs, observability | Proceed |
| A1 autonomous with evidence | New non-authoritative modules under `qe/`, replay tooling, research tooling | Proceed, with tests in the same change |
| A2 human approval | GP semantic definitions, risk limits, broker or data vendor choice, repo extraction, promoting an overlay | Stop **that item only**, record it in `DECISIONS_PENDING.md`, keep working on independent items |
| A3 human action | Entering LIVE, live credentials, raising exposure, disabling or overriding a kill switch | Never automated |

## B4. Agent integrity rules (anti-reward-hacking)

Agents are rewarded for **defects found, invariants proven, and evidence produced**, never for "green", "profitable", or "done".

- **B4.1 Spec-first, independent tests.** For authority-path code, tests and golden fixtures are written from the spec **before** the implementation, by a different agent or a separate pass that has not seen the implementation. Record the author and pass in the fixture header.
- **B4.2 No goalpost moving.** A failing test is fixed by changing the implementation. If the test is wrong, it changes only through an ambiguity-register or ADR entry that cites the spec requirement ID, in a separate commit.
- **B4.3 No threshold relaxation to pass.** Risk limits, net-R minimums, freshness windows, and DQ thresholds are policy (A2). An agent that finds them inconvenient files a proposal and does not edit them.
- **B4.4 No silent scope growth.** One vertical slice per change. Anything unrelated that you notice goes into `DEFECT_REGISTER.csv`, not into the diff.
- **B4.5 Negative results get reported first.** Status reports list failures and refuted claims before successes.
- **B4.6 Uncertainty is labeled.** Every claim in a report carries its evidence level (A3) or `UNVERIFIED`.

## B5. Agent roles (if multiple agents or passes are available)

| Role | Access | Output |
|---|---|---|
| Forensic auditor | Read-only, runs tests | Audit artifacts, defect register |
| Spec formalizer | Writes `qe/spec/**` | GP spec, ambiguity register, traceability rows |
| Fixture author | Writes `qe/tests/golden/**`, `property/**` | Tests written from the spec (B4.1) |
| Core engineer | Writes `qe/core/**` | Reducer and domain code |
| Quant validator | Runs registered experiments. Cannot edit a frozen spec | Experiment records, reports |
| Red team | Writes fault and chaos tests. Cannot edit policy | Fault-injection suite, findings |
| Coordinator | Merges, keeps `PROJECT_STATE.json` current | Phase reports |

No role has live credentials. Read-only work runs in parallel. Writes to the same module are serialized.

## B6. Session continuity

- `qe/PROJECT_STATE.json` is the single machine-readable record of where the project stands: phase, spec version, commit, open defects by severity, pending A2 decisions, holdout exposure status, mode, evidence levels. Update it at the end of every session. **A new session reads it first and never reconstructs project history from chat or phase reports.**
- `qe/DECISIONS.md` (ADR-style) records every material decision: context, options, choice, evidence, consequences, and date.

---

# PART C — INVARIANTS

Each invariant must be enforced by code **and** proven by at least one test (unit, property, stateful, golden, or fault) that is linked in `TRACEABILITY_MATRIX.csv`. An invariant with no test counts as violated.

### Determinism and time
- **INV-01** The same canonical inputs, spec version, resolved config, and commit produce byte-identical decision records and hashes, on any machine.
- **INV-02** The strategy core performs no I/O, reads no wall clock, and uses no unseeded randomness. Time comes from an injected `Clock`.
- **INV-03** Every derived fact has `formed_at` and `available_at`. A decision at time *t* uses only facts with `available_at ≤ t`.
- **INV-04** All timestamps are UTC internally. Session and exchange-timezone context is carried explicitly. The server's local timezone is never used for semantics.
- **INV-05** Trading-critical prices are integer ticks from the instrument registry. Money is integer minor units or `Decimal`. Stops, targets, and thresholds are never compared as floats.
- **INV-06** Canonical serialization (sorted keys, fixed numeric encoding, versioned schema) is used before any hash.
- **INV-07** Late or corrected data arrives as a new correction event. History is never rewritten in place (bitemporal: `valid_time` plus `recorded_time`).

### Fail-closed
- **INV-08** Any exception in a mandatory component produces `BLOCKED` with a reason code, never a warning plus continuing.
- **INV-09** Missing, stale, unknown, or ambiguous mandatory evidence produces `WAIT` (if it could still arrive) or `BLOCKED`, never lower confidence.
- **INV-10** A defaulted value (such as `.get(key, default)`) must never stand in for a mandatory field. Mandatory fields are required by the type system and validated at the boundary.
- **INV-11** Data-health state `UNKNOWN` is treated as unhealthy.

### Strategy authority
- **INV-12** Exactly one module can emit `STRATEGY_AUTHORIZED`. A static test checks the import graph for any other emitter.
- **INV-13** No transition skips a mandatory state. No score, confidence, or overlay can advance state.
- **INV-14** A touch is not a sweep. A sweep requires penetration of at least `min_penetration_ticks` beyond the liquidity boundary.
- **INV-15** No first-touch entry. A retest must come after qualifying displacement, and confirmation must come after the retest.
- **INV-16** A failed reclaim in one direction never becomes a setup in the opposite direction. The opposite thesis needs its own lineage and evidence.
- **INV-17** A setup that requires SMT authorizes only if `SMT == CONFIRMED`. Every other state (`DENIED`, `UNCLEAR`, `UNAVAILABLE`, `STALE`, `MISALIGNED`) produces `BLOCKED_SMT`.
- **INV-18** Structural invalidation exists, is on the correct side of executable entry, and has not already been breached at authorization.
- **INV-19** `net_R ≥ policy.min_net_R` (gp-1.0.0: 2.0), computed from the executable entry, structural stop, achievable target, and modeled fees and slippage. Missing target produces `BLOCKED_RR`.
- **INV-20** A stop is never moved to meet a monetary risk budget. Quantity is adjusted instead. If zero contracts fit, the result is `BLOCKED_RISK`, never a forced single contract.

### Lineage and idempotency
- **INV-21** `setup_lineage_id` is a deterministic hash of canonical thesis fields (spec version, instrument root, direction, setup family, liquidity object ID, sweep event ID, session ID). Alerts, candles, restarts, and scores cannot mint a new one.
- **INV-22** A lineage gets at most one authorized attempt. This is enforced by a **database uniqueness constraint**, not only by application code, and it survives restarts and multiple processes.
- **INV-23** Each `OrderIntent` has a unique idempotency key. Retries and duplicate deliveries cannot create duplicate economic exposure.

### Risk and execution
- **INV-24** Economic risk = `|entry − stop|` in ticks × tick value × contracts + fees + modeled entry and stop slippage, all taken from the instrument registry and cost model.
- **INV-25** Independent risk gives a single deny if any mandatory check fails. It never uses a weighted average.
- **INV-26** Risk state (daily P&L, open risk, positions) can be rebuilt from durable events plus broker truth. An in-memory counter is never the only authority.
- **INV-27** A submission timeout produces `SUBMISSION_UNKNOWN`. The system does not retry blindly. It queries by client order ID and blocks new conflicting risk until the state is resolved.
- **INV-28** A material disagreement between local and broker state produces `BLOCKED_RECONCILIATION` for new risk.
- **INV-29** After a restart, no new risk is allowed until recovery (load, broker query, reconcile, data-health check, policy check) completes.
- **INV-30** The kill switch sits outside strategy code. After a severe automatic halt, re-arming is an A3 human action.
- **INV-31** Intent persistence and outbound submission use a transactional outbox: at-least-once delivery with idempotent economic effect.

### Boundaries
- **INV-32** TradingView and Pine input is an **observation** only. The server recomputes independently, and it wins every disagreement.
- **INV-33** AI output never writes to strategy state, risk state, order state, policy, or config. The system runs fully with every LLM endpoint disabled (tested).
- **INV-34** Strategy code never imports broker SDKs, HTTP clients, database drivers, or LLM clients (import-graph test).
- **INV-35** Replay, shadow, paper, and live all run the **same** reducer. A second "backtest strategy" is forbidden.

### Research integrity
- **INV-36** Every reported result identifies its dataset snapshot hash, spec version, config hash, commit, cost model, and fill model.
- **INV-37** When stop and target are both hit inside one bar and the order is unknowable, the outcome is never the favorable one. Use finer data or record `AMBIGUOUS` and apply the declared conservative rule.
- **INV-38** MFE and MAE diagnostics are computed on a horizon that does not depend on the chosen exit, or are explicitly marked as censored.
- **INV-39** Zero fees or zero slippage are allowed only in runs explicitly labeled `FRICTIONLESS_DIAGNOSTIC` and never in headline results.
- **INV-40** Each confirmatory run records the number of variants tried in its experiment lineage, and reports search-adjusted statistics (F6).

---

# PART D — TARGET ARCHITECTURE

## D1. Principles

- **Deterministic modular monolith first.** One Python runtime owns trading semantics. Next.js stays as the UI. The Express backend becomes a thin BFF or is removed. PostgreSQL holds operational truth. Parquet with manifests holds raw market history. Redis, if used, is only a cache.
- **Not in v1** unless a measured requirement demands it: Kafka, Kubernetes, microservices, service mesh, vector DB, agent swarms, ML models in the authority path, or a Rust rewrite. **Complexity must earn its place with a measurement.**
- **Pure reducer:** `(state, event, policy, clock) → (state', emitted_events)`. No I/O inside.

## D2. Target layout (create only what a phase actually needs)

```
qe/
  PROJECT_STATE.json  DECISIONS.md  DECISIONS_PENDING.md
  spec/        GODS_PLAN_SPEC_v1.0.0.md  gp_1_0_0.yaml  gp_1_0_0.schema.json
               RISK_POLICY.md  DATA_QUALITY_POLICY.md  EXECUTION_SEMANTICS.md
               AMBIGUITY_REGISTER.csv  TRACEABILITY_MATRIX.csv  REASON_CODES.yaml
  core/        domain/ (events, instruments, sessions, liquidity, structure, zones,
                        smt, setups, lineage, risk, orders)
               engine/ (reducer, data_quality, structure, liquidity, sweep_reclaim,
                        displacement, retest, confirmation, smt, strategy_authority)
               serialization/  hashing/  clock.py
  replay/      event_reader  bar_builder  runner  simulated_broker  fill_models/
  execution/   risk_authority  order_intent  outbox  dispatcher  reconciliation
               kill_switch  recovery
  adapters/    market_data/  broker/  tradingview/  persistence/
  research/    registry/  protocols/  exposure_ledger/  event_studies/  ablations/
               nulls/  walk_forward/  sensitivity/  reports/
  audit/       (Phase 0 and 1 artifacts)
  evidence/    EVIDENCE_MATURITY_MATRIX.csv  replays/  manifests/
  tests/       unit/ property/ stateful/ golden/ replay/ contracts/ integration/
               recovery/ fault/ regression/ mutation/
  legacy_map/  (pointers into QuantumEdge/ and quantum-edge-terminal/; no copies)
```

Legacy code stays where it is. `legacy_map/` records its classification. An import-graph test forbids `qe/core` and `qe/execution` from importing anything under `QuantumEdge/` or `quantum-edge-terminal/`.

## D3. Event model (typed, immutable, versioned)

Market-derived events carry `event_time`, `receive_time`, `available_at`, `processed_at`, `provider`, `provider_sequence`, `instrument_id`, `contract_id`, `raw_ref`, `schema_version`, and `quality_flags`. Fields the provider doesn't supply are `UNKNOWN`, never fabricated.

Event types, at minimum: `Trade, Quote, BarClosed, SessionBoundary, Correction, DataQualityChanged, LiquidityCreated, LiquiditySwept, ReclaimObserved, DisplacementObserved, ZoneCreated, RetestObserved, ConfirmationObserved, SMTObserved, SetupTransition, RiskDecision, OrderIntent, BrokerAck, OrderRejected, OrderCancelled, PartialFill, Fill, PositionChanged, Reconciliation, KillSwitch`.

## D4. Two separate state machines

**Setup:** `IDLE → CONTEXT_VALID → LIQUIDITY_ARMED → SWEPT → RECLAIMED → DISPLACED → RETESTED → CONFIRMED → [SMT_CONFIRMED] → STRATEGY_AUTHORIZED → RISK_APPROVED → INTENT_CREATED`. The pre-authorization states can exit to `WAITING_FOR_DATA`, `BLOCKED_*`, `INVALIDATED`, `EXPIRED`, or `HALTED`.

**Order:** `INTENT_CREATED → QUEUED → SUBMITTING → {SUBMISSION_UNKNOWN | ACKNOWLEDGED} → WORKING → {PARTIALLY_FILLED → FILLED | CANCEL_PENDING → CANCELLED | REPLACE_PENDING | REJECTED | EXPIRED} → CLOSED`, with `RECONCILING` and `DIVERGED` reachable from any live state.

Every transition record contains: prior state, next state, event ID, event hash, reason code, evidence IDs, spec version, policy hash, config hash, DQ snapshot, trace ID, and transition hash (chained to the previous one for tamper evidence; no blockchain).

## D5. Reason codes

A closed enumeration in `REASON_CODES.yaml`, grouped by prefix: `GP_WAIT_*`, `GP_BLOCK_*`, `GP_INVALID_*`, `GP_EXPIRED_*`, `DQ_BLOCK_*`, `SMT_BLOCK_*`, `RISK_BLOCK_*`, `EXEC_*`, `RECON_*`, `HALT_*`. Control flow never branches on free-text strings. Every reason code is covered by at least one golden fixture.

## D6. Decision record

`decision_id, setup_lineage_id, spec_version, policy_hash, config_hash, mode_capabilities_hash, code_commit, input_event_id, input_event_hash, prior_state, resulting_state, direction, evidence_ids[], failed_gate_ids[], reason_codes[], entry_ticks, invalidation_ticks, target_ticks, est_costs_minor, net_R, smt_state, dq_state, decision_time, trace_id, decision_hash`.

The UI and the AI **explain** this record. Neither can change it.

## D7. Instrument registry and roll policy

Per contract: root, contract code, venue, currency, tick size, tick value, point value, expiry, trading calendar, exchange timezone, session template, price limits where known, broker symbol map, data symbol map, and roll metadata.

Historical research uses **point-in-time contracts** for executable levels (entries, stops, liquidity). Back-adjusted continuous series are allowed only for analytics, and each use is labeled. For SPY/QQQ, raw executable prices are kept separate from corporate-action-adjusted research series.

## D8. Data quality (upstream of strategy)

Checks: stale, duplicate, out-of-order, sequence gap, missing bar, impossible OHLC, invalid tick increment, wrong contract, roll uncertainty, session mismatch, clock skew, reconnect uncertainty, late correction, paired-feed misalignment, and provider outage.

States: `HEALTHY, DEGRADED, STALE, GAPPED, MISALIGNED, UNKNOWN`. Anything other than a state the policy permits produces `BLOCKED_DATA`. Trading-critical gaps are never interpolated.

## D9. External boundaries (time-sensitive: re-verify before deciding)

The earlier audits stated vendor facts: Alpaca's trading API doesn't cover futures, TradingView says its alerts aren't designed for automated trading, Tradovate requires an `isAutomated` flag, and Rithmic requires conformance testing. **Treat each of these as L0 claims.** Before any A2 broker or data decision, fetch the vendor's current docs, quote them in the ADR with the retrieval date, and check that the account type you actually have supports the asset class, order types, brackets, client order IDs, simulator, and automation policy you need. **The repo currently wires Alpaca** (for example `quantum-edge-terminal/execution/broker_engine/broker_connection.py`, `production/live_broker_connector.py`) while the primary instruments are ES, NQ, and GC futures. That mismatch is itself a Phase 0 finding.

- **Broker:** define the `BrokerAdapter` protocol first (`get_account, get_positions, get_open_orders, submit(intent), cancel, replace, get_order(client_id), stream_events`). Implement one futures adapter, paper or simulator only.
- **TradingView:** authenticate where the vendor supports it, validate the schema, validate the timestamp window, reject replays, deduplicate, store the raw payload, acknowledge quickly, and queue it as an **observation** (INV-32).
- **Data licensing:** record the entitlement or license terms for every dataset in its manifest before it is used, and in particular before anything is redistributed through a UI.

---

# PART E — VERIFICATION ARCHITECTURE

## E1. Traceability

Every spec requirement (`GP-CTX-001`, `GP-SWP-003`, …) has a row in `TRACEABILITY_MATRIX.csv`:

`requirement_id, text, spec_version, module, symbol, unit_test, property_test, golden_fixture, replay_test, status, evidence_level`

A requirement counts as implemented only when spec, code, test, and replay evidence are all linked. CI fails if any requirement tagged `MANDATORY` has an empty test column.

## E2. Golden fixtures (hand-checkable event sequences)

Each fixture lists input events, the **exact** expected transition sequence, the reason codes, and the final state. Minimum set:

Valid bullish · valid bearish · touch without sweep · penetration one tick below the minimum · sweep without reclaim · failed reclaim · acceptance beyond level · reclaim without displacement · displacement without structure break · displacement without retest · first-touch entry attempt · retest after expiry · retest without confirmation · SMT confirmed, denied, unavailable, stale, and misaligned · invalidation breached before confirmation · missing invalidation · target below net 2R after costs (passes gross 2R, fails net) · lineage already used · same lineage re-sent through a fresh webhook · stale primary feed · stale paired feed · duplicate event · out-of-order event · sequence gap · wrong contract · roll day · DST transition · holiday or early close · restart mid-setup · correction after decision.

Execution fixtures: duplicate submit · timeout followed by accepted · timeout followed by not found · partial fill · fill before ack · cancel/fill race · reject loop · reconciliation divergence · kill switch with working orders.

## E3. Property and stateful tests

Use property-based testing (for example Hypothesis) for every invariant in Part C that can be stated universally. Use **stateful/model-based testing** on the setup machine, the order machine, reconciliation, and the kill switch. Generate random sequences of events and faults, and assert that invariants hold after every step.

## E4. Differential testing

- **Legacy vs core:** feed identical historical events to the legacy detectors and the canonical core, and record every disagreement in `audit/DIVERGENCE_LOG`. Each one is explained, as a legacy bug, a spec decision, or a core bug, before the core becomes the authority.
- **Pine vs core:** use parity datasets for liquidity, sweeps, FVGs, retests, and setup state. The core wins. Divergences are logged and never "fixed" by changing the core to match the chart.
- **Replay vs shadow:** the same events processed live and replayed later must give identical decision hashes, apart from documented arrival-order effects.

## E5. Mutation testing (tests must be able to fail)

Run mutation testing (for example `mutmut` or `cosmic-ray`) on `qe/core/engine/strategy_authority`, `sweep_reclaim`, `smt`, `execution/risk_authority`, and `execution/outbox`. **The gate is a surviving-mutant rate at or below the threshold in `RISK_POLICY.md`, set by A2 decision (suggested starting point: 10%).** Each surviving mutant in these modules is either killed by a new test or justified in writing.

## E6. Fault injection and chaos

Inject: feed disconnect and reconnect, broker disconnect, HTTP timeouts, "accepted but response lost", duplicate or out-of-order broker events, process crash between intent persistence and submit, crash after submit, database restart, clock skew, local clock correction, malformed events, duplicate webhooks, API 429/500, and storage pressure.

The expected result in each case is deterministic, safe recovery with a named reason code. "Probably fine" is not an acceptable result.

## E7. Optional formal model

Model the order submit/retry/idempotency protocol and the lineage one-attempt lifecycle in TLA+/PlusCal (or as an exhaustive finite-state model check) **only if** stateful tests leave concurrency questions open. No formal-methods ceremony for prestige.

## E8. CI gates for `qe/`

Lint, strict typing (mypy or pyright strict on `qe/core` and `qe/execution`), unit, property, golden, replay-hash regression, import-graph boundary tests, secret scan, and dependency audit. For semantic changes, also require: an updated spec, a version bump, updated traceability rows, and an **impact statement** (which experiments and holdouts are affected). Build provenance: every release manifest records the commit, dependency-lock hash, spec hash, policy hash, and artifact digest.

---

# PART F — RESEARCH AND FALSIFICATION PROTOCOL

## F1. The research question

Not "did GP make money?", but:

> Does the pre-registered GP sequence carry **incremental** predictive and executable information over credible null alternatives, after realistic costs, with the research-search process taken into account, and does that information persist out of sample and across instruments?

Prior evidence for the mechanism is mixed. Stop-loss order clustering near round and visible levels is documented (Osler 2003, 2005), but triggered stops can **accelerate** moves as well as reverse them. That is exactly why GP requires reclaim, displacement, retest, and confirmation. Treat any claimed literature result (including recent preprints on formalized ICT/SMC rules) as a prior to verify, not a conclusion.

## F2. Pre-registration (`ResearchProtocolManifest`, hashed)

Before any confirmatory run, freeze: hypothesis, spec version, parameters, sessions, instruments, dataset snapshot hashes, cost model, fill model, roll policy, primary metric, secondary metrics, null model, decision rule, **minimum sample size (F4)**, IS/validation/holdout windows, purge/embargo, and seeds. Changing any of these after seeing results starts a **new experiment lineage**. It is not a correction.

## F3. Data partitioning and exposure ledger

- Split chronologically. Never use a random IID split for sequential data. Purge and embargo around overlapping labels.
- **Lock the final holdout on day one** (for example the most recent 20–30% of history per instrument) and record its hash in `research/exposure_ledger/`.
- Every time any metric computed on a partition is viewed, the ledger records who or what viewed it, when, which metrics, and whether it influenced a choice. A viewed holdout becomes a *used* partition and cannot be relabeled as OOS.

## F4. Power before performance (new)

Before a backtest counts as evidence, compute the sample it needs:

- Required trades to detect expected net expectancy μ (in R) with standard deviation σ_R at two-sided α and power 1−β: `n ≈ ((z_{1−α/2} + z_{1−β}) · σ_R / μ)²`. For example σ_R = 1.5, μ = 0.2R, α = 0.05, power = 0.8 gives **n ≈ 440 trades**. For μ = 0.1R it is about 1,770.
- Estimate σ_R from pilot or IS data, **not** from the holdout.
- If the available data can't produce n qualifying trades for an instrument or regime, the verdict for that cell is `INSUFFICIENT_EVIDENCE`. This is not "promising". Report it as it is.
- Adjust n upward for serial dependence (effective sample size) and for the multiple-testing burden (F6).

## F5. Decompose the hypothesis (gate-level event studies)

Full GP setups are rare, so test each link as its own pre-registered sub-hypothesis on the much larger event populations:

| Sub-hypothesis | Event population | Compared against |
|---|---|---|
| H-SWP | Qualified sweeps of eligible liquidity | Touches without penetration, and random session-matched levels |
| H-RCL | Sweep + reclaim | Sweep + acceptance beyond the level |
| H-DSP | + displacement | Reclaims without qualifying displacement |
| H-RTS | + retest after displacement | First-touch entries on the same events |
| H-CNF | + confirmation | Retests without confirmation |
| H-SMT | + SMT CONFIRMED | Same setups with SMT not confirmed |
| H-RR | + net-R ≥ 2 filter | Same setups without the filter, **including the winners it drops** |

The outcome for each is a forward-return or R distribution on a fixed horizon that doesn't depend on the exit (INV-38). If a gate adds no robust incremental information, that gets reported and the gate becomes a candidate for removal in a future spec version. No gate stays because of folklore.

## F6. Search-bias accounting

Count everything: strategies, parameter combinations, filters, redesigns, and data periods tried. That includes the fib…fib9 families and the 18 `backtest_*.py` variants already in the repo (Appendix 2), which make up **the search history the project already carries**. Report search-adjusted results: Deflated Sharpe Ratio (Bailey & López de Prado 2014), Probability of Backtest Overfitting via CSCV (Bailey, Borwein, López de Prado & Zhu), and White's Reality Check or Hansen's SPA where you're choosing among many variants. Where results are marginal, use a stricter t-stat hurdle in the spirit of Harvey, Liu & Zhu (2016).

## F7. Controls, robustness, and stress

- **Nulls:** eligible random entry, session and volatility matched; direction-randomized; the same setups with one gate removed. A deliberately weak null is forbidden.
- **Sensitivity surfaces** for each material parameter (penetration ticks, reclaim window, displacement threshold, retest depth, expiry, SMT alignment window, min net R). Prefer broad plateaus and treat isolated peaks as overfitting.
- **Cost and fill stress:** slippage at 1×, 2×, and 3×; wider stop slippage; delayed and missed entries; lower fill probability for limits.
- **Stratification:** instrument (ES, NQ, MES, MNQ, GC, reported separately and never blindly pooled), session (RTH, ETH, open, close), volatility regime, trend/balance, event days, and calendar period.
- **Uncertainty:** block or stationary bootstrap (Politis & Romano 1994) for serially dependent statistics. Report confidence intervals, not point estimates.

## F8. Reporting standard

Report candidates, qualified setups, authorizations, fills, win/loss/breakeven, expectancy (R), median R, R distribution and left tail, profit factor, max drawdown, MAE and MFE (uncensored or marked as censored), cost impact, slippage, missed-fill rate, and the IS→OOS degradation ratio. Flag `LOW_SAMPLE` against the F4 threshold. Win rate is never reported on its own.

## F9. Project-level kill and pivot criteria (predeclared, A2)

Before Phase 5 starts, the operator approves written criteria such as:

- **Stop:** if the frozen gp-1.0.0 shows no statistically distinguishable net expectancy over the best null on the locked holdout at the F4 sample size across the primary instruments, the GP-as-strategy line of work stops. The infrastructure is kept as a research platform, and any new hypothesis starts a new spec major version with a fresh holdout.
- **Pivot:** if a subset of gates (F5) shows robust information while the full sequence doesn't, open a new pre-registered spec `gp-2.0.0-candidate`. Never retrofit it into 1.0.
- **Continue:** only if the pre-registered decision rule is met.

Endless parameter search is itself evidence against the edge. The number of iterations counts in F6.

## F10. Experimental overlays

Options flow, DIX, put/call, gamma, macro regime, Fibonacci/1.618 rules, fractals, ML, and AI scores are `EXPERIMENTAL_OVERLAY`. They are never part of gp-1.0.0. Each is tested as a pre-registered **veto** or **filter** against the frozen baseline and promoted only through a new spec version (A2).

---

# PART G — PHASED EXECUTION PLAN

Each phase has entry criteria, deliverables, and exit gates. A phase is finished when its **exit gates hold with attached evidence**, not when a report exists. Report every phase in the format in G-R.

## Phase 0 — Forensic reality baseline (no semantic changes)

**Entry:** this directive and repo access.

**Deliverables (under `qe/audit/` and `qe/evidence/`):**
- **P0-01** `BASELINE.md`: branch, commit SHA, clean or dirty state, OS, Python and Node versions, dependency lock state, required services, configuration sources.
- **P0-02** A **pinned Quantum Edge Python environment** (`qe/requirements.lock` or `uv.lock`, plus one command) that runs the existing QE tests. Record exactly what ran, what passed, what failed, and what couldn't run and why (`TEST_REALITY_MATRIX.csv`).
- **P0-03** `REPOSITORY_INVENTORY.csv`: every file in the two QE subtrees, classified as `VERIFIED_RUNTIME | TESTED | IMPLEMENTED_UNVERIFIED | PROTOTYPE | EXPERIMENTAL | DOCUMENTED_ONLY | SCAFFOLD | LEGACY | MISSING`.
- **P0-04** `DEPENDENCY_GRAPH.md` plus `EXECUTION_AUTHORITY_GRAPH.md`: the real import and call graph, and **every code path that could produce or imply an order** (broker SDK calls, `tradeable` flags, alert engines, "live" connectors).
- **P0-05** `DATA_AUTHORITY_MAP.md`: every market-data source, normalization path, and timestamp origin.
- **P0-06** `DEFECT_REGISTER.csv`: severity (CRITICAL/HIGH/MEDIUM/LOW), file, symbol, mechanism, consequence, **a failing test that reproduces it** (under `qe/tests/regression/legacy/`, marked xfail-strict), and a proposed migration (not a patch).
- **P0-07** Re-verification of every seed finding in Appendix 1, plus the hypothesis list in Appendix 3, each marked `CONFIRMED | PARTIALLY_CONFIRMED | REFUTED | INSUFFICIENT_EVIDENCE` with evidence.
- **P0-08** `DOCUMENTATION_CONTRADICTIONS.csv`: each claim from the phase and status documents (Appendix 2) set against runtime reality.
- **P0-09** Threat models: `LOOKAHEAD_THREAT_MODEL.md`, `DATA_QUALITY_THREAT_MODEL.md`, `BROKER_STATE_THREAT_MODEL.md`, `SECURITY_BASELINE.md` (secret scan of the whole history, with any finding reported without printing the value).
- **P0-10** `RESEARCH_PROVENANCE.csv`: for each existing backtest or report, whether its dataset, parameters, costs, and code version can be identified, and how many variants each family explored (feeds F6).
- **P0-11** `EVIDENCE_MATURITY_MATRIX.csv` and an initial `PROJECT_STATE.json`.

**Exit gates:** every file in the QE subtrees is classified. Every order-capable path is listed. Every Appendix 1 finding is re-verified with a reproducing test or refuted. The test environment is reproducible. The report ends by answering: *"Based only on reproducible evidence from commit X, what does Quantum Edge actually do today, what does it partially do, what is prototype-only, and what does documentation merely claim?"*

## Phase 1 — Rule divergence and repo decision

- **P1-01** `GODS_PLAN_RULE_DIVERGENCE_MATRIX.csv`: rows are canonical concepts (liquidity, swing, BOS, CHoCH, sweep, reclaim, displacement, FVG, iFVG, OB, breaker, retest, confirmation, SMT, entry, stop, target, R, costs, session, expiry, one-attempt, timing, intrabar policy). Columns are every implementation (Python detectors, each backtest family, Pine scripts, TradingView bridge, TS backend, AI engine, validation layer).
- **P1-02** Decision A2-01 (extract the repo or fence it inside the monorepo), recorded with options and a recommendation.
- **P1-03** Quarantine plan: which legacy modules lose authority, and the import-ban test that enforces it.

**Exit:** every cell is filled or marked `ABSENT`, and every contradiction is listed for Phase 2.

## Phase 2 — Formalize gp-1.0.0 (A2 approvals)

For every concept, write: a mathematical or algorithmic definition in ticks, inputs, `formed_at`/`available_at` semantics, tolerances, states, invalidation, expiry, reason codes, edge cases (ties, equal highs, gaps, session boundaries, rolls), and requirement IDs. Every ambiguity goes into `AMBIGUITY_REGISTER.csv` as: the question, candidate definitions, consequences, a recommendation, the tests that would distinguish them, and a status. **Unquantified words ("strong", "clean", "obvious", "institutional") are illegal in the spec.** Fixture authors (B4.1) write the golden fixtures from the spec during this phase.

**Exit:** the spec is frozen at `gp-1.0.0` with operator approval of each A2 item, the traceability matrix has a row for every requirement, and the golden fixtures exist (and fail, because nothing is implemented yet).

## Phase 3 — Domain and pure reducer

Build events, the instrument registry, sessions and calendar, ticks, liquidity objects, structure, zones, SMT, lineage, and the reducer, one vertical slice at a time. Suggested order: DQ gate → liquidity plus sweep → reclaim → displacement → retest → confirmation → SMT → invalidation and net R → authorization. No broker, database, AI, or UI.

**Exit:** all golden fixtures pass, the property tests for INV-01…INV-22 pass, mutation gate E5 passes for the authority modules, and the import-boundary tests pass.

## Phase 4 — Deterministic replay

Build the replay runner, bar builder, and simulated broker with explicit fill models, all on the same reducer. Each replay emits: `replay_id`, commit, spec and policy hashes, dataset IDs and partition hashes, environment, seeds, transition-hash chain, and final hash.

**Exit:** two runs on different machines produce identical hashes. The legacy-vs-core differential log is explained entry by entry.

## Phase 5 — Adversarial quantitative validation

Approve the F9 criteria, then pre-register (F2), run the power analysis (F4), gate-level event studies (F5), ablations, nulls, walk-forward, sensitivity, stress, stratification, and search-adjusted statistics (F6). Then run the **single** locked-holdout confirmatory evaluation.

**Exit:** a research verdict (`VERIFIED_EDGE_CANDIDATE | NO_VERIFIED_EDGE | INSUFFICIENT_EVIDENCE`) with its full evidence bundle. The project continues according to F9.

## Phase 6 — Live-data shadow (no orders)

Run the same reducer on live normalized data. Measure freshness, contract mapping, session handling, SMT alignment latency, restart behavior, correction handling, and replay-vs-shadow hash parity.

**Exit:** a divergence budget agreed by A2 and met over a pre-agreed number of sessions.

## Phase 7 — Independent risk, OMS, paper broker

Build the risk authority, `OrderIntent`, outbox, dispatcher, reconciliation, recovery, and kill switch against a paper or simulator broker. Run the execution fixtures (E2) and the fault suite (E6).

**Exit:** INV-23…INV-31 are proven by tests running through the real adapter boundary.

## Phase 8 — Terminal integration

The Next.js UI becomes a **projection** of decision records. Its main view answers "why is the system waiting or blocked?", showing state history, evidence, SMT, DQ, invalidation, net R, lineage status, risk result, broker state, and reconciliation. React never computes authorization. AI panels explain decision records and never change them.

## Phase 9 — Live-readiness review (the review is a report, not a mode switch)

`LIVE_READINESS_REPORT.md` marks every criterion `PASS | FAIL | UNVERIFIED | POLICY_CHOICE`. `UNVERIFIED` is never rounded up to `PASS`. It includes runbooks (stale data, broker outage, unknown order state, reconciliation mismatch, database outage, leaked credential, unexpected exposure, kill switch, rollback), backup and restore evidence, secrets separation, and the legal and compliance items flagged for qualified review (market-data redistribution, broker API terms, and any offering to third parties). **Anything after this is an A3 human decision outside this directive.**

## G-R. Report format (every session and phase)

1. **Failures and refuted claims** (first)
2. Verified facts, each with its evidence level
3. Files inspected / files changed (with requirement IDs)
4. Commands run and their exact results (`NOT RUN` where applicable)
5. Replay and research results, reported separately
6. New defects, by severity
7. Evidence maturity by component
8. Pending A2/A3 decisions
9. Risk register (top five)
10. The single highest-leverage next action

Phrases such as "everything looks great", "should work", or "production-ready" are not allowed.

## G-S. Stop conditions (halt and report immediately)

Stop if tests can't be reproduced, data provenance is unknown, lookahead can't be removed, a canonical definition is still ambiguous after Phase 2, an order path exists outside the risk gate, the broker state can't be reconciled, timestamps can't be trusted, the edge disappears under corrected methodology, new code contradicts the frozen spec, or a request would weaken deterministic authority.

---

# APPENDIX 1 — Seed findings, re-checked against source at commit `416e34e`

These were re-read at file:line during preparation of this directive. They are **L1 (source-confirmed)**. Phase 0 must raise each one to a failing reproduction test or refute it. Paths are relative to `quantum-edge-terminal/`.

| ID | Sev | Location | Mechanism | Consequence |
|---|---|---|---|---|
| S-01 | CRITICAL | `execution/execution_engine/execution_engine.py:59-76` vs `execution/risk_engine/risk_engine.py:260,289,393-394,420` | The execution payload uses `trade_id`, `asset`, `position_size`, `signal_confidence`. The risk engine reads `signal_id`, `symbol`, `position_size_pct`, `confidence` with `.get()` defaults (`""`, `""`, `2.0`, `0.5`) | Risk evaluates **defaults**, not the trade. INV-10 violated |
| S-02 | CRITICAL | `risk_engine.py:260` | `signal_id = payload.get("signal_id", "")` and no producer sets it | Every ID-less signal collapses to `""`: false duplicates, and no real lineage. INV-21/22 absent |
| S-03 | CRITICAL | `execution_engine.py:267,301-302` | `macro_validated = True` by default. `except Exception` only appends a warning | A crashed macro filter **passes**. INV-08 violated |
| S-04 | CRITICAL | `execution_engine.py:230-241,321-325` | `all()` over an empty `take_profit_targets` is `True`. `reward_amount = 0`, `risk_reward_ratio = 0`, and the payload is still created | A candidate with no target and 0R is executable. INV-19 violated |
| S-05 | CRITICAL | `execution_engine.py:71,323` | `risk_amount = abs(entry - stop)` is commented as "Dollar risk" | Price distance treated as dollars. No tick value, contracts, or costs. INV-24 violated |
| S-06 | HIGH | `execution_engine.py:313-315` | A size bonus of up to +20% when `signal_confidence > 0.75` in a RISK_ON regime | Confidence sizes risk. INV-13/33 spirit violated |
| S-07 | CRITICAL | `tradingview_bridge_adapter.py:163-204` | `tradeable: True` once confidence ≥ 0.70 and confluence ≥ 3. RR < 1.618 is only a **warning**. `position_size_factor` grows with confluence | An alert can be marked tradeable without the GP sequence. INV-32 violated. 1.618 conflicts with net 2R |
| S-08 | CRITICAL | `validation/scoring_engine/institutional_scorecard.py:239-240,268,300-301` | Missing metrics are `continue`d out of both numerator and denominator. A missing hard-fail metric returns `False` (not failed) | A sparse, favorable metric set can score high and pass. Missing must mean INCOMPLETE |
| S-09 | HIGH | `ai-engine/src/modules/market_structure_detector.py:118-134` | Sweep = `current_high > prev_high * 0.995` over a two-bar lookback. High side only | At ES ≈ 6000, a bar about 30 points (about 120 ticks) **below** the level counts as a "sweep". No low-side sweeps. INV-14 violated |
| S-10 | HIGH | `market_structure_detector.py:83-98` | `downtrend` is computed but never used. Only the uptrend-reversal branch emits | CHoCH is asymmetric |
| S-11 | MEDIUM | `market_structure_detector.py:100-116` | FVG = a gap between **adjacent** bars, not a three-candle imbalance | Semantics diverge from the usual FVG definition. Phase 2 must choose |
| S-12 | MEDIUM | `market_structure_detector.py:65,76,96` | Hard-coded confidences of 0.85 and 0.75 | Arbitrary constants presented as probabilities |
| S-13 | HIGH | `storage/trade_journal/trade_journal.py:370` | `net_pnl = gross_pnl  # TODO: subtract commissions` | "Net" P&L is gross |
| S-14 | HIGH | Repo-wide | No SMT implementation found (`\bsmt\b` search over the QE Python, Pine, and TS returned nothing). Broker code targets Alpaca (`execution/broker_engine/broker_connection.py`, `production/live_broker_connector.py`, and others). About 50 `datetime.now/utcnow` calls in `execution/` and `validation/` alone | A mandatory gate is missing, the broker doesn't match the futures universe, and wall-clock time is spread through decision code |

Environment facts: `pyproject.toml` `testpaths = ["skills"]` (QE tests aren't collected). `pytest` isn't installed in the container. QE tests: `QuantumEdge/tests/test_data_presence.py` and three `quantum-edge-terminal/tests/test_*execution_instrumentation*/phase_8_5*` files. **No QE test was run while preparing this directive (NOT RUN).**

# APPENDIX 2 — Status documents classified as L0 claims

`quantum-edge-terminal/`: `AUDIT_COMPLETE_EXECUTION_VALIDATION_DELIVERED.md`, `DEPLOYMENT_SUMMARY.md`, `FINAL_COMPLETION_SUMMARY.py`, `PERFECT_PHASE_8_5_MASTERY_SUMMARY.md`, `PERFECT_TEST_STRATEGY_REPORT.md`, `PHASE2_COMPLETE_GUIDE.md`, `PHASE2_DEPLOYMENT_COMPLETE.md`, `PHASE8_COMPLETE_SUMMARY.md`, `PHASE_3_MODULES_1-2_COMPLETE.md`, `PHASE_8_5_*` (8 files), `PROJECT_ANALYSIS_COMPLETE.md`, `REALITY_CHECK_STATUS.md`, and others. The backtest variants that make up the existing search history (F6): `backtest_baseline_validated.py`, `backtest_enhanced_fib.py`, `backtest_fast_enhanced_fib.py`, `backtest_fib_manipulation.py`, `backtest_fib_optimization.py`, `backtest_fix_validation.py`, `backtest_historical_rr*.py`, `backtest_hybrid_strategy.py`, `backtest_integrated_system.py`, `backtest_max_profit_final.py`, `backtest_optimized_profitability.py`, `backtest_phase2_*.py`, `backtest_post_fix_validation.py`, `backtest_practical_profits.py`, `backtest_smart_profitability.py`, `backtest_timeframe_analysis.py`, and `QuantumEdge/research/fib`…`fib9`.

# APPENDIX 3 — Additional hypotheses for Phase 0 to confirm or refute

Swing or structure detection that uses right-side confirmation bars without recording `available_at` · backtests that fill at the trigger bar's high or low after a close-confirmed signal · exit-censored MFE/MAE in existing reports · zero-cost defaults in backtest configs · webhook without authentication or replay protection · TradingView source timestamps replaced by receive time · risk state held only in process memory · multiple incompatible "trade" schemas across Python and TS · integration bridges that continue after a safety violation · "live switch" requirements that exist only in documentation · TODO paths presented as integrations · strategy families with different bar-timing semantics · continuous-contract prices used as executable levels · no roll policy for ES/NQ/GC history.

---

**Begin with Phase 0. Add no features, no ML, and no LLM trading logic. Do not redesign the UI, enable live trading, optimize parameters, or delete legacy artifacts. The purpose of Phase 0 is to establish what is actually true.**
