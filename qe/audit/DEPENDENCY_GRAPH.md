# Dependency Graph (P0-04)

Generated data: `qe/audit/python_imports.json` (AST imports and resolved internal edges for all 186 Python files) and `qe/audit/import_sweep.csv` (whether each module actually imports in the pinned environment).

## Import sweep result

| Result | Modules |
|---|---|
| OK | 127 |
| IMPORT_ERROR | 51 |
| SYNTAX_ERROR | 2 |
| SKIPPED (unguarded top-level script; importing would run it) | 6 |

Root causes of the 53 failures:

| Cause | Modules affected | Defect |
|---|---|---|
| `ExecutionPayload` dataclass `TypeError` | all of `execution/*`, all of `production/*`, 1 test | D-001 |
| `validation_orchestrator.py` does not parse, so `validation/__init__` fails | all of `validation/*` | D-027 |
| `alert_engine.py` does not parse | `interface/*` | D-027 |
| OpenTelemetry symbols removed from the SDK | `observability/*`, 2 tests | D-028 |
| LEAN `AlgorithmImports` not available outside LEAN | `QuantumEdge/strategy/*`, `QuantumEdge/data/*` | expected; needs the LEAN runtime |
| `services/order_manager` imports a bare `broker_connection` module that does not exist on its path | 1 | - |
| `ai-engine/main.py` needs `python-multipart` (not in `ai-engine/requirements.txt`). Reproduced with the engine's own pins, so the container crashes at start | 1 | D-044 |

## Internal import graph: `quantum-edge-terminal`

```
tests/test_execution_instrumentation*.py ─┬─> observability ──X (D-028)
                                          ├─> execution ──────X (D-001)
                                          └─> validation ─────X (D-027)
tests/test_phase_8_5_integration.py ──────> execution ──────X (D-001)

production/__init__ ─> production.{deployment_gate_controller, live_broker_connector,
                                   market_data_streamer, performance_monitor, production_runner}
production/production_runner ─> execution ──X
execution/__init__ ─> execution.{broker_engine, execution_audit_log, execution_engine ──X,
                                 execution_kill_switch, order_manager, risk_engine,
                                 shadow_execution_comparator, staged_capital_deployment}
execution/order_manager ─> execution.broker_engine.broker_connection
validation/__init__ ─> validation.{forward_test_engine, integration_bridge, live_validation_runner,
                                   safety_controls, scoring_engine, validation_orchestrator ──X}
validation/integration_bridge ─> execution, observability
services/order_manager ─> execution.execution_audit_log, observability

ai-engine/main.py (FastAPI) ─> src.modules.{algo_detection, fractal_validator, market_structure_detector}

standalone, imported by nothing: tradingview_bridge_adapter.py, storage/trade_journal,
                                 services/ai_engine/modules/options_flow.py, all backtest_*.py
```

`X` marks an import that fails. Because the `execution`, `validation`, `observability`, and `production` package initializers all fail, **no terminal code path above the AI engine can run as a package**.

## Internal import graph: `QuantumEdge`

- `main.py` (LEAN entry) imports `algorithm.config`, `strategy.{regime, sleeve_a, sleeve_b, sleeve_c, allocator}`, and `data.{validator, universe}`. It needs the LEAN runtime.
- `research/runner.py`, `experiments.py`, `manifest.py`, `results.py`, `validity.py`, and `analytics.py` are the LEAN experiment harness.
- `research/fibN/*` are self-contained families. Later families import earlier ones. For example `fib9.canonical` imports `fib7.robustness` and `fib7.analysis`. `fib*/data.py` reads `lean/Data/equity/usa/{daily,hour}/*.zip`, **which is not in the repository**.

## Cross-language edges

- Frontend (Next.js) calls backend REST and WebSocket (`frontend/src/services/api.ts`, `hooks/useWebSocket.ts`).
- The backend (Express) reads and writes Postgres tables (`candles`, `signals`, `alerts`). **The backend does not call the AI engine or any Python service.** There is no code path from Python signal generation into the backend.
- Pine scripts emit plain-text `alert()` messages. The only Python consumer (`tradingview_bridge_adapter.py`) expects JSON and is not hosted by any service (D-026).
