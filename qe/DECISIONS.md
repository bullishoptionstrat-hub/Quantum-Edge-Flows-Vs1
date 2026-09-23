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
