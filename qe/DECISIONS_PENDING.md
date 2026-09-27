# Decisions Pending (A2: human approval required)

Phase 1 can't finish, and Phase 2 can't start, until A2-00 and A2-01 are decided. Everything else in Phase 0 is done.

## A2-00: Where does the God's Plan specification come from? (blocking)

**Finding:** "God's Plan" appears nowhere in this repository (D-037). No code implements the sweep → reclaim → displacement → retest → confirmation → SMT sequence. The GP rules exist only in material outside the repo: the uploaded markdown document the two earlier master prompts were written from.

The closest prior art in the repo is `QuantumEdge/research/fib2`–`fib9`: daily and 1-hour ETF "manipulation leg" detectors with sweep confirmation, displacement metrics, Fibonacci retracement zones, and OOS splits. They run on equity ETFs, not futures, and the data they read is not in the repo (D-035).

**Options:**
1. Commit the GP source document to `qe/spec/source/` as-is. Phase 2 formalizes it into `gp-1.0.0` and records each ambiguity. *(Recommended.)*
2. Dictate or approve the GP rules section by section during Phase 2.
3. Treat the fib-family research as the starting definition and extend it toward GP.

## A2-01: Repository layout (directive A4.3)

**Finding:** Quantum Edge is 538 files inside a roughly 15,000-file openclaw monorepo. The root agent instructions, CI, and tooling all target openclaw. Every CI job on PR #36 was skipped as not applicable.

**Options:**
1. Extract `QuantumEdge/`, `quantum-edge-terminal/`, `qe/`, and `quantum-edge-governance/` into a dedicated repository with its own CI. *(Recommended: clean agent instructions and CI that actually tests Quantum Edge.)*
2. Keep it in this repo, add `qe/AGENTS.md` and a Quantum Edge-only CI workflow, and fence openclaw off.

## A2-02: Scope of the existing LEAN sector-rotation / IBS strategy

**Finding:** `QuantumEdge/main.py` and `strategy/*` implement an ETF sector-momentum, IBS mean-reversion, and Greenblatt allocation strategy. It is unrelated to God's Plan.

**Options:** (1) keep it as legacy research, read-only (*recommended*); (2) run it as a separate governed track; (3) archive it.

## A2-03: Committed Postgres password

**Finding:** `quantum-edge-terminal/docker-compose.yml:9` commits a literal Postgres password (D-034). The value is not reproduced in the audit.

**Action needed:** confirm whether that value is used on any reachable host. If it is, rotate it. Either way, the canonical stack reads secrets from the environment.

## Also needed before Phase 5 (not blocking now)

- **Market data for ES/NQ/GC:** no futures data exists in the repo. Choose a vendor and license, point-in-time contracts, and intraday resolution.
- **Broker for paper trading:** re-verify futures support against current vendor docs (D9) before choosing.
