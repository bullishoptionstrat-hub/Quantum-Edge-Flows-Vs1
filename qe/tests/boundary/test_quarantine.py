"""P1-03 quarantine: canonical code must never depend on legacy Quantum Edge code.

Enforces directive D2 / INV-34 at the import level. Canonical roots are listed
in CANONICAL_ROOTS; they may not exist yet, in which case they are vacuously
clean. The checker itself is exercised against synthetic violations so a broken
checker cannot pass silently.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CANONICAL_ROOTS = ["qe/core", "qe/gp", "qe/spec", "qe/execution", "qe/replay", "qe/adapters", "qe/research", "qe/api"]

# Top-level module names that exist only in the legacy subtrees (qe/audit/python_imports.json).
LEGACY_MODULES = {
    "execution", "production", "validation", "interface", "observability", "services",
    "storage", "monitoring", "learning", "src", "strategy", "research", "algorithm", "data",
    "tradingview_bridge_adapter", "AlgorithmImports", "broker_connection",
}
# Anything under these may never be imported by canonical code either.
FORBIDDEN_THIRD_PARTY = {"alpaca_trade_api", "alpaca", "openai", "anthropic"}
LEGACY_PATH_MARKERS = ("quantum-edge-terminal", "QuantumEdge")


def violations(source: str, filename: str = "<src>") -> list[str]:
    out = []
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for n in names:
            top = n.split(".")[0]
            if top in LEGACY_MODULES:
                out.append(f"{filename}:{node.lineno}: imports legacy module {n}")
            if top in FORBIDDEN_THIRD_PARTY:
                out.append(f"{filename}:{node.lineno}: imports forbidden package {n}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(m in node.value for m in LEGACY_PATH_MARKERS):
                out.append(f"{filename}:{node.lineno}: references legacy path {node.value!r}")
    return out


def test_checker_catches_violations():
    bad = (
        "import execution.execution_engine\n"
        "from production.live_broker_connector import LiveBrokerConnector\n"
        "import alpaca_trade_api\n"
        "P = 'quantum-edge-terminal/execution'\n"
    )
    assert len(violations(bad)) == 4
    assert violations("import dataclasses\nfrom decimal import Decimal\n") == []


def test_canonical_code_does_not_touch_legacy():
    found = []
    for root in CANONICAL_ROOTS:
        for f in sorted((REPO / root).rglob("*.py")):
            found += violations(f.read_text(), str(f.relative_to(REPO)))
    assert found == [], "\n".join(found)


# INV-02: the core reads no wall clock, uses no randomness, and does no I/O.
IMPURE = re.compile(
    r"\bdatetime\.(now|utcnow|today)\(|\btime\.(time|monotonic|perf_counter)\(|\bimport random\b|\bfrom random\b"
    r"|\bopen\(|\.read_text\(|\.write_text\(|\brequests\b|\burllib\b|\bsocket\b|\bsubprocess\b|\bos\.environ\b"
)


PURE_ROOTS = ["qe/core", "qe/gp"]  # the strategy reducer must be as pure as the core


def test_core_is_pure():
    bad = []
    for f in sorted(p for root in PURE_ROOTS for p in (REPO / root).rglob("*.py")):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if IMPURE.search(line):
                bad.append(f"{f.relative_to(REPO)}:{i}: {line.strip()}")
    assert bad == [], "\n".join(bad)


def test_purity_checker_catches_violations():
    for line in ["t = datetime.now()", "import random", "x = Path(p).read_text()", "v = os.environ['K']"]:
        assert IMPURE.search(line), line
