# Execution Authority Graph (P0-04)

**Question:** which code paths in the repository could produce an order, or claim that an order was produced?

**Answer at commit `361e92ac`:** no path in the repository can send an order to any broker. Several components **claim or imply** execution without performing it.

## Every order-capable or order-implying component

| Component | What it does | Can it run? | Real network call? | Risk |
|---|---|---|---|---|
| `execution/broker_engine/broker_connection.py` `BrokerConnection.submit_order` | Builds a mock Alpaca-style response. Order id = `ORD_{symbol}_{hash(str(qty)) % 10000}`, `submitted_at` hard-coded to `2026-04-03T14:32:15Z`, status `accepted` in LIVE mode | Loads standalone, but **always raises TypeError** (D-040). Its package cannot import (D-001) | No. The Alpaca SDK calls are commented out (:149-151, :287-297) | If "fixed" naively, it returns fake `accepted` orders in LIVE mode |
| `production/live_broker_connector.py` `LiveBrokerConnector.submit_order` | `TODO: Actual order submission to Alpaca`. Marks the order SUBMITTED with a timestamp id and logs `REAL EXECUTION` | No (package import fails via D-001) | No | Logs claim real execution (D-029) |
| `execution/order_manager/order_manager.py`, `services/order_manager/order_manager.py` | Wrap `broker.submit_order` | No (D-001; the services copy has a broken import path) | No | Two divergent copies of the same module |
| `tradingview_bridge_adapter.py` `generate_trade_instruction` / `get_pending_trades` / `_to_alpaca_format` | Sets `tradeable: True` from confidence and confluence, and formats an Alpaca-style order dict | Yes, as a library | No | Implies authority (D-012..D-016). Real Pine alerts can't reach it (D-026) |
| `execution/execution_engine/execution_engine.py` `create_execution` | Produces `ExecutionPayload` marked PENDING/valid | No (D-001) | No | Fail-open validation (D-004..D-009) |
| `execution/risk_engine/risk_engine.py` `RiskEngine.validate` | Gatekeeper "called BEFORE any order is submitted" | Loads standalone, **never called by any runnable code** | No | Unenforced limits (D-010, D-011) |
| `execution/execution_kill_switch.py`, `staged_capital_deployment.py`, `shadow_execution_comparator.py` | Kill switch and capital staging | No (D-001) | No | A kill switch that can't be imported protects nothing |
| `backend/src/api/signals.ts` `POST /api/signals` | Inserts an `ACTIVE` signal row. No auth, wildcard CORS | Would, if the stack starts (the schema has Postgres syntax errors, D-042) | DB only | Anyone who can reach the host can create "active" signals shown in the UI (D-034) |
| Pine `strategy()` scripts | TradingView strategy tester orders (simulated in TradingView) | Only inside TradingView | TradingView alerts only | Visual and simulated only |

## The claimed pipeline vs. the real one

Claimed across the phase documents: `AI signal → execution engine → risk engine → order manager → broker (Alpaca paper/live) → journal → monitoring`.

Real: none of these components calls the next one. `ExecutionEngine`, `RiskEngine`, `TradeJournal`, and `TradingViewWebhookReceiver` are never instantiated by any runnable entry point. They are only used in example scripts and tests, and those can't import either (D-038). The only Python service, `ai-engine/main.py`, would return analysis JSON over HTTP and place nothing. It also crashes at startup with its own pinned requirements (D-044).

## Implication for the directive

- No live-trading exposure exists today. That is **accidental**: it comes from broken imports and mocks, not from a designed safety boundary. Repairing a single import (D-001) would expose a mock broker that returns `accepted` in LIVE mode.
- Recommendation for Phase 1 (quarantine plan P1-03): add an import-ban test so `qe/` never imports `execution/`, `production/`, or `services/order_manager`. Do not repair those modules in place.
