# Data-Quality Threat Model (P0-09)

Today there are **no data-quality checks** at any market-data ingress (see `DATA_AUTHORITY_MAP.md`). This table lists each failure mode, what would happen in the current code, and what the canonical data-quality authority (directive D8) must do instead.

| Failure mode | Today | Required (D8) |
|---|---|---|
| Missing data files | `fib*/data.py` raises `FileNotFoundError`. LEAN-side behavior (`QuantumEdge/data/validator.py`) not exercised: needs the LEAN runtime | `BLOCKED_DATA` with the dataset id |
| Stale feed | Not detected anywhere | Freshness window per instrument. `STALE` blocks |
| Duplicate bar or event | Not detected | Deduplicate on `(provider, provider_sequence)` or `(instrument, bar_start)` |
| Out-of-order event | Not detected | Reject, or buffer with a watermark. Record `DQ_BLOCK_OUT_OF_ORDER` |
| Gap (missing bars) | Not detected. Research loops index arrays directly | `GAPPED` state, and no interpolation of trading-critical data |
| Impossible OHLC (high < low, close outside the range) | Not detected. The synthetic generators can't produce it, and real data is unchecked | Reject the event |
| Invalid tick increment | No instrument registry exists | Registry-driven check |
| Wrong contract / roll | No futures data or roll logic exists | Point-in-time contract map, plus `ROLL_TRANSITION_UNCERTAIN` |
| Session or timezone mismatch | yfinance daily index uses local dates. No session templates | Session calendar per instrument (UTC internally) |
| Adjusted vs raw price confusion | `auto_adjust=True` everywhere | Separate raw (executable) and adjusted (analytic) series |
| Provider revision of history | yfinance re-adjusts silently. Nothing pinned | Immutable snapshots with hashes. Corrections become events |
| Paired-feed misalignment (SMT) | No SMT exists | `MISALIGNED` blocks SMT (INV-17) |
| TradingView alert clock | Replaced by receive time (D-014) | Keep the source time. Enforce a skew window |
| Clock skew on the host | Wall clock used in logic | Injected clock, plus a monotonic clock for durations (INV-02) |
