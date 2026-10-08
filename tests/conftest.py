"""
Sets DATABASE_URL before any app module is imported by any test file, and
seeds it once per test run. Without this, test files that each try to set
their own DATABASE_URL race against Python's module import cache - whichever
test file imports app.database first "wins", and every other test file
silently shares that same database instead of the one it thinks it's using.
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_platform.db"

import pytest  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def seed_test_database():
    subprocess.run(
        [sys.executable, "seed_data.py"],
        check=True,
        env=os.environ,
        cwd=str(BACKEND_DIR),
    )
    yield
