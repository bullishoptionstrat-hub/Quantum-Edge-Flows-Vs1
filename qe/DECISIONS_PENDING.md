# Decisions Pending (human approval or action required)

A2-00 through A2-03 were decided on 2026-10-07 (ADR-0006 to ADR-0009). This list is what still needs a human.

## H-01: Commit the God's Plan source document (blocks the spec freeze)

ADR-0006 chose to formalize the original God's Plan document, but that document is not in the repository. Add it unchanged to `qe/spec/source/` and record its sha256 in `qe/DECISIONS.md`. Each `AMB-*` entry is then re-checked against it.

## H-02: Approve or amend each ambiguity entry (A2; blocks Phase 3)

`qe/spec/AMBIGUITY_REGISTER.csv` has 37 PROPOSED choices. Each has candidates, consequences, a recommendation, and the fixtures that distinguish the options. Freezing `gp-1.0.0` needs a status of APPROVED or REJECTED (with the chosen alternative) on every row. A changed parameter regenerates the affected fixtures through `qe/spec/fixtures/build_fixtures.py`, with a manifest update.

## H-03: Rotate the committed Postgres password (A3, human action)

ADR-0009: rotate the password on any host that uses the value in `quantum-edge-terminal/docker-compose.yml`. The agent cannot do this.

## H-04: Verify the instrument registry against CME (A2)

Every row in `qe/config/instruments.json` is `verified: false` (directive D9). The proposed commission values (`P-COST-COMMISSION-RT-MINOR`) are placeholders until a broker is chosen.

## Needed before Phase 5 (not blocking now)

- **Market data for ES/NQ (and any other instrument that gets authorized):** choose the vendor and license, point-in-time contracts, and intraday resolution, plus the news calendar and roll-date sources that the spec requires (GP-REQ-013, GP-REQ-014).
- **Broker for paper trading:** re-verify futures support against current vendor documentation (D9) before choosing.
