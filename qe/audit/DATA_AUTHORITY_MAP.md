# Data Authority Map (P0-05)

Every place market data enters Quantum Edge, where its timestamps come from, and whether the data can be identified.

| # | Source | Consumer | Timestamp origin | Dataset identity | Status |
|---|---|---|---|---|---|
| 1 | LEAN zip files at `lean/Data/equity/usa/{daily,hour}/<ticker>.zip` (repo root) | `QuantumEdge/research/fib*/data.py`, `QuantumEdge/main.py` (LEAN) | Rows in LEAN CSV format inside each zip | None: no hashes. `lean/` is empty in the repository | **Absent.** 3 of 4 data-presence tests fail |
| 2 | yfinance downloads (`auto_adjust=True`, split and dividend adjusted) | `QuantumEdge/generate_lean_data.py` (writes source 1), `QuantumEdge/backtest_standalone.py`, `quantum-edge-terminal/backtest_historical_rr.py` | yfinance index (exchange local date for daily data) | None. Downloads aren't pinned or hashed, and adjusted prices change as history is revised | Network-dependent and not reproducible |
| 3 | Python `random.gauss` random walks (seeded) | 17 of 18 `quantum-edge-terminal/backtest_*.py` | Synthetic bar index | Seed only | **Synthetic, not market data** (D-030) |
| 4 | Alpaca market-data WebSocket | `production/market_data_streamer.py` | Would be the provider's | - | `TODO`: connection is simulated and the module can't import |
| 5 | TradingView alerts | `tradingview_bridge_adapter.py` | **Replaced by local `datetime.now()`** (D-014) | None | Format incompatible with the Pine output (D-026) |
| 6 | Candles POSTed to AI engine endpoints | `ai-engine/main.py` → detectors | Whatever the caller sends; not validated | None | No data-quality checks |
| 7 | Postgres `candles` / `signals` tables | Express backend → UI | `created_at` DB default (receive time) | None | No provenance columns (`database/schema.sql`) |

## Instruments actually present

- Research and LEAN: US **equity ETFs** (sector SPDRs, SPY, QQQ, SHY, SPXU, country ETFs such as EWJ/EWZ, and others). Daily and 1-hour bars.
- **No futures data (ES, NQ, GC, micros) exists anywhere in the repository.** Pine scripts are titled "(ES 1h)" but only run inside TradingView. No contract metadata, tick sizes, point values, or roll logic exist.

## Gaps against directive Part D

- No `event_time` / `receive_time` / `available_at` separation at any ingress point.
- No data-quality authority: no stale, gap, duplicate, or out-of-order detection.
- No dataset manifests with hashes. The QuantumEdge run manifests record `git_commit` and `git_dirty`, but not the data.
- Adjusted and raw prices aren't kept separate (source 2 uses `auto_adjust=True` for everything).
