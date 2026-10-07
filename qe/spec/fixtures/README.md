# Golden fixtures for `gp-1.0.0-draft.1`

These are hand-checkable event sequences (directive E2) written from `qe/spec/GP_SPEC.md`, before any implementation exists. They are the acceptance test for the Phase 3 reducer. They also depend on PROPOSED parameter values, so **they are only binding once the operator freezes the spec**.

- `build_fixtures.py` is the fixture author's tool. It writes `GF-*.json`, `MANIFEST.sha256`, and `../GP_REQUIREMENTS_TRACE.csv`. Every expected value in it was derived by hand from the spec. The test suite re-derives the arithmetic (ATR, displacement measurements, zone, net R, mirror symmetry) with `qe/core` primitives as an independent check.
- **Implementers never edit fixtures to make the reducer pass** (directive B4). `MANIFEST.sha256` is checked by `qe/tests/spec/test_gp_spec_artifacts.py`. A changed fixture needs a spec change, a new hash, and a `qe/DECISIONS.md` entry.

## Conventions

- Prices are integer ticks. Bar `i` starts at `time_base.bar0_start_utc + i × timeframe_s` (plus an optional `start_offset_s`). It closes `timeframe_s` later, and `available_at = close + delay_s` (default `default_delay_s`).
- Bars are listed in arrival order. A bar index listed twice is a redelivery, written `"dup:<i>"`. Clock ticks are written `"tick:<k>"`.
- Setup fixtures take liquidity objects as **given inputs**. Deriving liquidity is tested separately by the `GF-L*` fixtures. A setup reducer under test must not derive extra objects.
- Expected `lineages` and `rejections` are **exhaustive**. `evidence` is a **subset** check: every listed key must match exactly. Ratios are `"n/d"` strings, compared as exact fractions.
- `zone.bottom < zone.top` is price order in both directions. For SHORT setups the retest touches `zone.bottom`.
- Base scenario: ES, contract ESU6, session date 2026-07-14, 5-minute bars from 08:20 ET. The sweep is on bar 15 (09:35 ET) of the prior RTH low 19980; the pair is NQ (NQU6). `GF-001` is the full path; most other fixtures change one or two bars of it.
