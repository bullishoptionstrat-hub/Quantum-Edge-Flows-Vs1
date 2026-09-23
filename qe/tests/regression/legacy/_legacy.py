"""Load legacy Quantum Edge modules by file path for defect reproduction (P0-06).

Legacy packages under quantum-edge-terminal/ mostly cannot be imported through
their package __init__ files (syntax errors, a dataclass TypeError, removed
OpenTelemetry symbols; see qe/audit/import_sweep.csv). These helpers load a
single source file in isolation so the defect under test is the one exercised.

`load_patched` applies an explicit, minimal text substitution before loading.
It exists only for the execution engine, whose module cannot be defined at all
(D-001). Every substitution is asserted to match exactly once, so if the legacy
source changes the harness fails loudly instead of silently testing something
else.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TERMINAL = REPO / "quantum-edge-terminal"


def load(rel_path: str, name: str | None = None) -> types.ModuleType:
    path = TERMINAL / rel_path
    name = name or "legacy_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_patched(rel_path: str, substitutions: list[tuple[str, str]], name: str) -> types.ModuleType:
    path = TERMINAL / rel_path
    src = path.read_text()
    for old, new in substitutions:
        n = src.count(old)
        assert n == 1, f"harness substitution matched {n} times in {rel_path}: {old!r}"
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile(src, f"{path} (patched harness)", "exec"), mod.__dict__)
    return mod


# The one-line repair that lets execution_engine.py define its classes. Moving
# the default off take_profit_targets is the smallest change that makes the
# dataclass legal; create_execution() always passes take_profit_targets, so the
# downstream logic under test is unchanged.
EXEC_ENGINE_IMPORT_REPAIR = [(
    "take_profit_targets: List[float] = field(default_factory=list)  # Multiple TP levels",
    "take_profit_targets: List[float]  # Multiple TP levels (harness: default removed)",
)]


def execution_engine() -> types.ModuleType:
    return load_patched(
        "execution/execution_engine/execution_engine.py",
        EXEC_ENGINE_IMPORT_REPAIR,
        "legacy_execution_engine_patched",
    )
