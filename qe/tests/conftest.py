import sys

# Never write .pyc files into the legacy subtrees while loading them for audit.
sys.dont_write_bytecode = True

import tempfile

from hypothesis import settings
from hypothesis.configuration import set_hypothesis_home_dir

# Hypothesis caches unicode tables under ./.hypothesis by default; keep the repo clean.
set_hypothesis_home_dir(tempfile.mkdtemp(prefix="qe-hypothesis-"))

# Keep runs hermetic and deterministic: no example database on disk, derandomized search.
settings.register_profile("qe", database=None, derandomize=True)
settings.load_profile("qe")
