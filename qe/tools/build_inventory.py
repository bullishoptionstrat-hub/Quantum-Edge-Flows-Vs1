#!/usr/bin/env python3
"""Merge runtime evidence into the static inventory (P0-03, P0-11).

Reads  qe/audit/REPOSITORY_INVENTORY.csv (from scan_repo.py)
       qe/audit/import_sweep.csv          (from import_sweep.py)
Writes qe/audit/REPOSITORY_INVENTORY.csv  (adds import_result/import_error, refines classification)

Refinement rules (each recorded in classification_basis):
  - Non-research Python that fails to import or parse   -> PROTOTYPE
  - Test files that fail to collect                      -> PROTOTYPE
  - quantum-edge-terminal/backtest_* using random price generators -> EXPERIMENTAL (synthetic data)
  - Nothing is promoted to TESTED or VERIFIED_RUNTIME here: at this commit no
    behavior-level test passes against any module (see TEST_REALITY_MATRIX.csv).

Usage: python3 qe/tools/build_inventory.py   (after scan_repo.py and import_sweep.py)
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

AUDIT = Path("qe/audit")
SYNTH = re.compile(r"random\.gauss\(|random\.seed\(|np\.random")


def main() -> None:
    inv = list(csv.DictReader((AUDIT / "REPOSITORY_INVENTORY.csv").open()))
    sweep = {r["path"]: r for r in csv.DictReader((AUDIT / "import_sweep.csv").open())}
    # Idempotent: drop previous merge columns before re-adding.
    for row in inv:
        row.pop("import_result", None)
        row.pop("import_error", None)
    for row in inv:
        s = sweep.get(row["path"])
        row["import_result"] = s["result"] if s else ""
        row["import_error"] = s["error"] if s else ""
        path = row["path"]
        research = row["classification"] == "EXPERIMENTAL"
        if s and s["result"] in {"IMPORT_ERROR", "SYNTAX_ERROR"} and not research:
            row["classification"] = "PROTOTYPE"
            row["classification_basis"] = f"does not import in pinned env: {s['error'][:120]}"
        if path.startswith("quantum-edge-terminal/backtest_"):
            text = Path(path).read_text(errors="replace")
            if SYNTH.search(text):
                row["classification_basis"] = "backtest on synthetic random-walk data (random.gauss/seed); not market evidence"
            elif "yf.download" in text or "yfinance" in text:
                row["classification_basis"] = "backtest on yfinance downloads; no dataset snapshot/hash recorded"
    fields = list(inv[0].keys())
    with (AUDIT / "REPOSITORY_INVENTORY.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(inv)
    from collections import Counter
    print(Counter((r["subtree"], r["classification"]) for r in inv))


if __name__ == "__main__":
    main()
