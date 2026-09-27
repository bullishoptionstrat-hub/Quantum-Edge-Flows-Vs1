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
