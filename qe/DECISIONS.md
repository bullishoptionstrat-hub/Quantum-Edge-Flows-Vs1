# Decision Log

## ADR-0001: Phase 0 audit tooling lives under `qe/`, legacy code is untouched (2026-09-23)

- **Context:** Directive A4.3 says new canonical work goes under `qe/` until the repo-layout decision (A2-01) is made. Phase 0 must not change legacy semantics.
- **Decision:** All Phase 0 artifacts, tools, tests, and the pinned audit environment live under `qe/`. No file in `QuantumEdge/` or `quantum-edge-terminal/` was modified.
- **Consequence:** Legacy defects are reproduced by loading legacy files by path (`qe/tests/regression/legacy/_legacy.py`). The one exception is the execution engine, which can't be defined at all (D-001). It is loaded with a single, asserted text substitution that moves one dataclass default, so its downstream logic can be exercised. The substitution is documented next to the code.

## ADR-0002: Defect reproductions are strict xfails that must fail by assertion (2026-09-23)

- **Decision:** Each reproduction asserts the directive's invariant and is marked `xfail(strict=True, raises=AssertionError)`. A fixed or refuted defect shows up as XPASS and fails the run. A broken harness raises a non-assertion error and also fails the run.
- **Consequence:** The suite goes red when legacy code changes in a way the register doesn't reflect.

## ADR-0003: Audit environment pins (2026-09-23)

- **Decision:** `qe/requirements-audit.in` holds the top-level pins and `qe/requirements-audit.lock` holds the full freeze, on Python 3.11.
- **Why not the legacy pins:** `ai-engine/requirements.txt` has 51 known vulnerabilities (D-043) and lacks packages the code imports. Legacy imports that fail only because of legacy pins would be misattributed. The OpenTelemetry failure (D-028) was reproduced on both SDK 1.21.0 and 1.27.0.

## ADR-0004: Spec-independent core primitives built before gp-1.0.0 (2026-09-27)

- **Context:** Phase 1 is blocked on A2-00 (God's Plan spec source) and A2-01 (repo layout). Directive tier A1 allows new canonical modules that are not production authority, provided they come with tests.
- **Decision:** Build only the pieces every version of God's Plan needs, with no strategy semantics:
  - `qe/core/ticks.py`: integer ticks; floats and off-grid prices rejected.
  - `instruments.py`: registry parsing, economic risk in cents, exact net R, and floor sizing that returns 0 rather than forcing one contract.
  - `clock.py`: a forward-only replay clock.
  - `serialization.py`: canonical bytes, sha256, and a hash chain.
  - `events.py`: a validated `BarClosed` with `available_at`.
  - `mode.py`: the capability firewall; LIVE is refused.
- **Registry values:** `qe/config/instruments.json` holds ES/MES/NQ/MNQ/GC entered from commonly published CME specs, every row marked `verified: false` until checked against the current CME pages (D9).
- **Mutation check (E5, by hand):** seven planted mutations, all killed:
  - forced one contract;
  - allowed stop == entry;
  - dropped costs from risk;
  - dropped entry slippage from reward;
  - removed the lookahead check;
  - removed the receive-time check;
  - allowed floats.

  Two of these first survived, and the tests were strengthened until they were killed: costs dropped from risk (fixed with an exact net-R test) and the lookahead check removed (the test case now isolates it). A tool-based mutation run (mutmut) is still to do.
- **Consequence:** `qe/spec/INVARIANT_TRACEABILITY.csv` maps each invariant to its code and tests. Nothing here is wired to data or orders.

## ADR-0005: Data-quality gate for closed-bar feeds (2026-09-28)

- **Context:** Directive D8 puts data quality upstream of strategy logic. It doesn't depend on God's Plan semantics, so it can be built before gp-1.0.0.
- **Decision:** `qe/core/data_quality.py` is a pure `step(state, bar, policy) -> (state, verdict)` with a closed `DQReason` set. It fails closed:
  - no data yet is UNKNOWN;
  - a duplicate bar is rejected idempotently;
  - the same bar with different content is rejected and sets the feed to UNKNOWN;
  - an older bar is rejected as out of order;
  - missing bars make the feed GAPPED, unless an injected session-break rule says the hole is a known closure;
  - a contract change makes the feed UNKNOWN;
  - silence past `max_staleness_ns` makes it STALE.

  Leaving GAPPED or UNKNOWN takes `recovery_bars` consecutive clean bars.
- **Policy, not code:** `timeframe_s`, `max_staleness_ns`, `recovery_bars` and the session-break rule have no defaults. They are A2 choices per instrument, and tests pick illustrative values.
- **Mutation check (by hand):** nine planted mutations, all killed:
  - accept out-of-order bars;
  - ignore gaps;
  - recover instantly;
  - staleness off by one;
  - ignore contract changes;
  - treat no data as healthy;
  - accept the wrong feed;
  - report the old health on a conflict (survived at first; fixed by asserting verdict health);
  - leave the state healthy on a conflict.
- **Not done:** a Correction event type (INV-07), a real session calendar, and multi-feed alignment for SMT (needs the spec).

## ADR-0006: A2-00, spec source: formalize the God's Plan document; draft built without it (2026-10-07)

- **Operator decision:** option 1, commit the God's Plan source document to `qe/spec/source/` and formalize it into `gp-1.0.0` ("go with your best recommendations", 2026-10-07).
- **Finding:** the document is not in the repository and was never given to the agent. The operator-supplied material in the session (a design review and two master prompts) describes the sequence and its qualitative rules but contains no numbers (`qe/spec/source/README.md`).
- **Decision:** write `gp-1.0.0-draft.1` (`qe/spec/GP_SPEC.md`) from the quoted sequence (`qe/spec/source/GP_SOURCE_EXCERPTS.md`) and the directive. Every threshold is PROPOSED and logged in `qe/spec/AMBIGUITY_REGISTER.csv` (37 entries). Prior-art definitions from the divergence matrix appear only as candidates.
- **Artifacts:**
  - 66 requirements;
  - `REASON_CODES.yaml` (32 codes);
  - a parameter file;
  - 41 golden fixtures with a hash manifest and a requirement trace;
  - `qe/gp` stubs, so the fixtures xfail with `NotImplementedError` until Phase 3.
- **Verification:**
  - `qe/tests/spec/test_gp_spec_artifacts.py` cross-checks every artifact against the others.
  - It also re-derives each fixture's arithmetic with `qe/core`. That re-derivation caught one hand-calculation error (GF-022's net R was 144/71 ≈ 2.03, not below 2). The fixture was corrected to 283/142 before commit.
- **Not frozen:** the spec becomes `gp-1.0.0` only after (1) the source document is committed and each `AMB-*` entry is re-checked against it, and (2) the operator approves each entry. Phase 3 must not start before then.

## ADR-0007: A2-01, repository layout: fence Quantum Edge inside this monorepo (2026-10-07)

- **Operator decision:** first, option 1 (extract to a dedicated repository). Creating the repository failed: the GitHub integration returned "403 Resource not accessible by integration". The copy step was then stopped by the session's safety check as a data-sharing upload. The operator then chose option 2: "fence it inside the repo instead".
- **Decision:**
  - `qe/AGENTS.md` (with a `CLAUDE.md` symlink) is the instruction file for all four Quantum Edge paths. Each of `QuantumEdge/`, `quantum-edge-terminal/`, and `quantum-edge-governance/` gets a short `AGENTS.md` pointing to it. Root openclaw instructions and tooling do not apply (directive A4.1).
  - `.github/workflows/quantum-edge.yml` is a Quantum Edge-only CI. It is path-filtered, runs on GitHub-hosted runners, uses read-only permissions, installs the pinned audit environment, runs the qe suite, and checks that the spec artifacts reproduce byte for byte.
  - No openclaw file is modified. The workflow is the one new file outside the Quantum Edge paths.
- **Consequence:** the PR's first real CI signal will come from this workflow, if Actions are enabled on the fork. The openclaw Blacksmith jobs remain unrunnable here (PR comment 5855943109).

## ADR-0008: A2-02, the LEAN sector-rotation / IBS strategy stays read-only legacy research (2026-10-07)

- **Decision:** `QuantumEdge/main.py` and `QuantumEdge/strategy/*` are kept unchanged as legacy research. They are unrelated to God's Plan, are not a governed track, and are not archived.
  - Their behavior is never changed.
  - Defects are documented in the register.
  - Canonical code cannot import them (quarantine test).
- **Only addition:** the pointer `AGENTS.md`/`CLAUDE.md` files from ADR-0007. They change no code or behavior.

## ADR-0009: A2-03, the committed Postgres password is treated as compromised (2026-10-07)

- **Finding (D-034):** `quantum-edge-terminal/docker-compose.yml` commits a literal Postgres password, at line 9 and inside `DATABASE_URL` at lines 40 and 72. It is in the git history, so editing the file now would not remove it.
- **Decision:**
  - Treat the value as public. Rotating it on any host that uses it is a human action (tier A3). The agent cannot verify or perform it.
  - The legacy file stays unchanged (ADR-0008).
  - Any canonical Quantum Edge service reads credentials from the environment and fails to start when they are missing.
  - A real secret scanner in CI (directive E8) remains open.
- **Process note:** while locating the value on 2026-10-07, one agent shell command printed it in the session's tool output. It was not written to any file, commit, or comment.
