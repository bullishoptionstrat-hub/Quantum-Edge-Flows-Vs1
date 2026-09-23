# Broker-State and Retry Threat Model (P0-09)

No real broker integration exists (see `EXECUTION_AUTHORITY_GRAPH.md`). This model records what the legacy design would do in each failure case, so the canonical OMS (Phase 7) is built against the right failures.

| Scenario | Legacy behavior (from source) | Consequence if wired to a real broker | Canonical requirement |
|---|---|---|---|
| Submit times out, but the broker accepted the order | Not handled. The retry count is kept in process (`retry_count`), with no client order id (`client_order_id: None`) | A blind retry creates duplicate exposure | `SUBMISSION_UNKNOWN`, then query by client id and reconcile (INV-27) |
| Duplicate signal delivered twice | Duplicate check keyed on `signal_id` that is always `''` (D-003) | Both over-blocks unrelated signals and fails to identify real duplicates | Idempotency key per `OrderIntent` with a DB unique constraint (INV-23) |
| Process restart with open positions | All risk state (`daily_pnl`, `open_positions`, `recent_signals`) lives in memory only | Daily loss limit resets to zero, and open exposure is forgotten | Rebuild from durable events plus broker truth before any new risk (INV-26, INV-29) |
| Broker reports a fill that local state doesn't know about | No reconciliation code exists | Silent divergence | `BLOCKED_RECONCILIATION` (INV-28) |
| Partial fill | `OrderStatus` has `filled_qty`, but nothing consumes partials | Wrong size in the journal and risk | Order state machine with `PARTIALLY_FILLED` |
| Cancel/fill race | Not modeled | Double exit or orphaned position | Stateful test in the fault suite (E6) |
| Mock order ids | `hash(str(qty)) % 10000`, which varies per process (hash randomization) and collides for equal quantities (D-040) | Ids can't be used to reconcile | Deterministic client order ids derived from the intent |
| LIVE mode without a real client | Mock returns status `accepted` in LIVE mode (broker_connection.py:308) | A false record of a live order | No mock may return an accepted state. The mode firewall (B2) makes the live endpoint unreachable except in LIVE |
| Kill switch | Module can't be imported (D-001) | No protection | Kill switch outside strategy code, tested through the real integration path (INV-30) |
| Wrong asset class for the broker | Alpaca endpoints (equities and crypto per the earlier audit; re-verify under D9) with ES/NQ/GC labels in code comments | Orders for unsupported products | Choose the adapter by verified capability (A2 decision) |
