#!/usr/bin/env python3
"""Phase 0 runtime import sweep (P0-02 / P0-03 evidence).

Tries to import every Python module in the Quantum Edge subtrees, one fresh
subprocess per module, with outbound network pointed at a dead proxy so no
module can reach a broker or data vendor during the sweep. Top-level scripts
without an `if __name__ == "__main__"` guard are NOT imported (importing them
would execute them); they are recorded as SKIPPED_UNGUARDED_SCRIPT.

Writes qe/audit/import_sweep.csv. Run with the pinned venv interpreter:
  qe/.venv/bin/python qe/tools/import_sweep.py
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMPORTS = REPO / "qe/audit/python_imports.json"
OUT = REPO / "qe/audit/import_sweep.csv"

DEAD_NET = {
    "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
    "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9",
    "NO_PROXY": "", "no_proxy": "",
}


def import_root(path: str) -> Path:
    p = Path(path)
    if p.parts[0] == "quantum-edge-terminal" and len(p.parts) > 2 and p.parts[1] == "ai-engine":
        return REPO / "quantum-edge-terminal/ai-engine"
    return REPO / p.parts[0]


def main() -> None:
    meta = json.loads(IMPORTS.read_text())["modules"]
    env = {k: v for k, v in os.environ.items() if not k.lower().endswith("_proxy")}
    env.update(DEAD_NET)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    rows = []
    for path in sorted(meta):
        mod = meta[path]["module"]
        text = (REPO / path).read_text(errors="replace")
        is_top_script = "/" not in path.split("/", 1)[1]
        if is_top_script and "__name__" not in text:
            rows.append({"path": path, "module": mod, "result": "SKIPPED_UNGUARDED_SCRIPT", "error_type": "", "error": ""})
            continue
        if not meta[path]["parse_ok"]:
            rows.append({"path": path, "module": mod, "result": "SYNTAX_ERROR", "error_type": "SyntaxError", "error": "ast.parse failed"})
            continue
        code = (
            "import importlib,sys,traceback\n"
            f"sys.path.insert(0, {str(import_root(path))!r})\n"
            f"importlib.import_module({mod!r})\n"
        )
        try:
            r = subprocess.run([sys.executable, "-c", code], cwd=import_root(path), env=env,
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                rows.append({"path": path, "module": mod, "result": "OK", "error_type": "", "error": ""})
            else:
                last = [l for l in r.stderr.strip().splitlines() if l.strip()][-1] if r.stderr.strip() else "nonzero exit"
                etype = last.split(":", 1)[0] if ":" in last else "Error"
                rows.append({"path": path, "module": mod, "result": "IMPORT_ERROR", "error_type": etype, "error": last[:300]})
        except subprocess.TimeoutExpired:
            rows.append({"path": path, "module": mod, "result": "TIMEOUT", "error_type": "Timeout", "error": ">60s"})
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "module", "result", "error_type", "error"])
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(Counter(r["result"] for r in rows))


if __name__ == "__main__":
    main()
