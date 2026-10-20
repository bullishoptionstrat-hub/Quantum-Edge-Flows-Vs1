#!/usr/bin/env bash
# Rebuild every machine-generated Phase 0 artifact from the working tree.
# Usage (repo root): bash qe/tools/run_phase0.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export PYTHONDONTWRITEBYTECODE=1

if [ ! -x qe/.venv/bin/python ]; then
  python3 -m venv qe/.venv
  qe/.venv/bin/pip install -q -r qe/requirements-audit.lock
fi

python3 qe/tools/scan_repo.py            # inventory, import edges, static flags
qe/.venv/bin/python qe/tools/import_sweep.py   # runtime importability, network disabled
python3 qe/tools/build_inventory.py      # merge runtime evidence into inventory
python3 qe/tools/defects.py              # defect register
python3 qe/tools/divergence_matrix.py    # P1-01 rule divergence matrix
qe/.venv/bin/python -m pytest -c qe/pytest.ini --rootdir=. -q   # legacy defects must xfail; boundary tests must pass
