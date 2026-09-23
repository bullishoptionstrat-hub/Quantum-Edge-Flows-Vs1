#!/usr/bin/env python3
"""Phase 0 static scanner for the Quantum Edge subtrees (P0-03, P0-04, P0-09).

Deterministic: output depends only on the working tree contents. Writes:
  qe/audit/REPOSITORY_INVENTORY.csv   one row per file, static facts + classification
  qe/audit/python_imports.json         internal import edges per Python module
  qe/audit/static_flags.csv            per-file risk-pattern hit lines

Classification is rule-based (see classify()). Every row records the rule that
fired in `classification_basis` so a human can challenge it. Runtime facts
(importability, test results) come from qe/tools/import_sweep.py and are merged
in by qe/tools/build_inventory.py; this script never executes project code.

Usage: python3 qe/tools/scan_repo.py   (run from repo root)
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path

ROOTS = ["QuantumEdge", "quantum-edge-terminal"]
OUT = Path("qe/audit")

# Risk patterns scanned in source text. Keys become column names.
PATTERNS: dict[str, re.Pattern[str]] = {
    "wall_clock": re.compile(r"datetime\.(now|utcnow|today)\(|time\.time\(\)|Date\.now\(\)|new Date\(\)"),
    "broad_except": re.compile(r"except\s*(Exception)?\s*(as\s+\w+)?\s*:|catch\s*\("),
    "dict_get_default": re.compile(r"\.get\(\s*[\"'][^\"']+[\"']\s*,"),
    "todo": re.compile(r"\b(TODO|FIXME|XXX|HACK)\b"),
    "random_call": re.compile(r"\brandom\.(random|uniform|choice|randint|gauss|shuffle)\(|np\.random\.(rand|randn|normal|uniform|choice)\(|Math\.random\("),
    "broker_or_order": re.compile(r"alpaca|submit_order|place_order|create_order|/v2/orders|paper-api|live[_-]?trading|broker", re.I),
    "tradeable_flag": re.compile(r"[\"']tradeable[\"']|tradeable\s*=", re.I),
    "confidence_sizing": re.compile(r"confidence.{0,40}(size|multiplier|bonus)|(size|multiplier|bonus).{0,40}confidence", re.I),
    "secret_like": re.compile(r"(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_\-]{12,}[\"']", re.I),
    "float_price_eq": re.compile(r"(entry|stop|target|price)\w*\s*==\s*\w", re.I),
    "golden_ratio": re.compile(r"1\.618|0\.618|PHI\b"),
    "network_call": re.compile(r"requests\.(get|post)|aiohttp|urlopen|yfinance|yf\.download|fetch\(|websocket", re.I),
}

STATUS_WORDS = re.compile(r"\b(COMPLETE|PERFECT|PRODUCTION[- ]READY|INSTITUTIONAL|VERIFIED|VALIDATED|FINAL|DEPLOYED|MASTERY)\b")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def module_name(p: Path) -> str | None:
    """Dotted module name relative to its subtree's import root, or None."""
    if p.suffix != ".py":
        return None
    parts = list(p.parts)
    # Import roots actually used by the code: QuantumEdge/ (sys.path hack in main.py)
    # and quantum-edge-terminal/ (tests insert it) and ai-engine/ (src.*).
    if parts[0] == "quantum-edge-terminal" and len(parts) > 2 and parts[1] == "ai-engine":
        rel = parts[2:]
    else:
        rel = parts[1:]
    rel[-1] = rel[-1][:-3]
    if rel[-1] == "__init__":
        rel = rel[:-1]
    return ".".join(rel) if rel else None


def classify(p: Path, text: str, flags: dict[str, int], parse_ok: bool) -> tuple[str, str]:
    s = str(p)
    name = p.name
    if p.suffix in {".log"} or "/output/" in s or name == "log.txt":
        return "EXPERIMENTAL", "research run output/log artifact (evidence of past runs, not code)"
    if p.suffix == ".json" and "/output/" not in s:
        return "SCAFFOLD", "config/editor json"
    if p.suffix == ".md" or name.endswith(".txt") or name.endswith("_SUMMARY.py") or re.search(r"(COMPLETE|PERFECT|STATUS|REPORT|GUIDE|AUDIT)\w*\.py$", name):
        if STATUS_WORDS.search(text) or STATUS_WORDS.search(name):
            return "DOCUMENTED_ONLY", "status/claim document using completion vocabulary (L0 claim)"
        return "DOCUMENTED_ONLY", "documentation (L0)"
    if p.suffix == ".pine":
        return "PROTOTYPE", "TradingView Pine script: not executable in repo, no parity tests"
    if p.suffix == ".py" and not parse_ok:
        return "PROTOTYPE", "python file does not parse"
    if name.startswith("backtest_") or "/research/" in s or name in {"research.ipynb", "backtest_standalone.py", "generate_lean_data.py"}:
        return "EXPERIMENTAL", "research/backtest code; no reproducible manifest verified yet"
    if re.search(r"EXAMPLE|DEMO|example", name):
        return "SCAFFOLD", "example/demo script"
    if "/tests/" in s or name.startswith("test_"):
        return "IMPLEMENTED_UNVERIFIED", "test file; see TEST_REALITY_MATRIX for whether it runs"
    if p.suffix in {".ts", ".tsx", ".css"}:
        return "IMPLEMENTED_UNVERIFIED", "TS/UI source; no tests in subtree"
    if name in {"__init__.py"} and len(text.strip()) < 400:
        return "SCAFFOLD", "package marker"
    if p.suffix == ".py":
        return "IMPLEMENTED_UNVERIFIED", "python source; runtime status merged from import sweep"
    return "SCAFFOLD", "infra/config file"


def scan_python(p: Path, text: str) -> tuple[bool, list[str], list[str]]:
    try:
        tree = ast.parse(text, filename=str(p))
    except SyntaxError:
        return False, [], []
    imports: list[str] = []
    symbols: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            imports.append(base)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
    return True, sorted(set(imports)), symbols


def resolve(mod: str, imp: str, known: set[str]) -> str | None:
    if imp.startswith("."):
        level = len(imp) - len(imp.lstrip("."))
        base = mod.split(".")
        # a package's own name counts as a level
        base = base[: len(base) - level + (1 if mod in pkg_names else 0)]
        tail = imp.lstrip(".")
        cand = ".".join([*base, tail] if tail else base)
    else:
        cand = imp
    while cand:
        if cand in known:
            return cand
        cand = cand.rpartition(".")[0]
    return None


pkg_names: set[str] = set()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(f for r in ROOTS for f in Path(r).rglob("*") if f.is_file() and "__pycache__" not in f.parts)
    rows = []
    flag_rows = []
    py_meta: dict[str, dict] = {}
    for f in files:
        raw = f.read_bytes()
        text = raw.decode("utf-8", errors="replace") if f.suffix != ".png" else ""
        loc = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        flags = {}
        for k, pat in PATTERNS.items():
            hits = [i + 1 for i, line in enumerate(text.splitlines()) if pat.search(line)]
            flags[k] = len(hits)
            if hits and f.suffix in {".py", ".ts", ".tsx", ".pine"}:
                flag_rows.append({"file": str(f), "pattern": k, "count": len(hits), "lines": " ".join(map(str, hits[:40]))})
        parse_ok, imports, symbols = (True, [], [])
        mod = module_name(f)
        if f.suffix == ".py":
            parse_ok, imports, symbols = scan_python(f, text)
            if f.name == "__init__.py" and mod:
                pkg_names.add(mod)
            py_meta[str(f)] = {"module": mod, "imports": imports, "symbols": symbols, "parse_ok": parse_ok}
        cls, basis = classify(f, text, flags, parse_ok)
        rows.append({
            "path": str(f), "subtree": f.parts[0], "ext": f.suffix or f.name, "bytes": len(raw), "loc": loc,
            "sha256": sha256(f), "module": mod or "", "parse_ok": parse_ok if f.suffix == ".py" else "",
            "top_level_symbols": len(symbols),
            **{f"n_{k}": v for k, v in flags.items()},
            "classification": cls, "classification_basis": basis,
        })

    # Internal import edges. Two namespaces: QuantumEdge modules and terminal modules.
    edges: dict[str, list[str]] = {}
    for sub in ROOTS:
        known = {m["module"] for p, m in py_meta.items() if p.startswith(sub) and m["module"]}
        for p, m in py_meta.items():
            if not p.startswith(sub) or not m["module"]:
                continue
            tgt = set()
            for imp in m["imports"]:
                r = resolve(m["module"], imp, known)
                if r and r != m["module"]:
                    tgt.add(r)
            edges[p] = sorted(tgt)
    (OUT / "python_imports.json").write_text(json.dumps({"modules": py_meta, "internal_edges": edges}, indent=1, sort_keys=True))

    with (OUT / "REPOSITORY_INVENTORY.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (OUT / "static_flags.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "pattern", "count", "lines"])
        w.writeheader()
        w.writerows(flag_rows)
    print(f"files={len(rows)} python={len(py_meta)} flag_rows={len(flag_rows)}")


if __name__ == "__main__":
    main()
