# Root conftest to ensure project package is importable when running pytest.
# Adds the repository root to sys.path so `import app` works from tests.
import os
import sys
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
