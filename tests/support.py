"""Sandbox-compatible test workspace; avoids Windows tempfile mode=0700 ACLs."""
import shutil
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

@contextmanager
def scratch_directory():
    parent=(Path(__file__).resolve().parents[1]/'var'/'test-workspaces').resolve()
    parent.mkdir(parents=True,exist_ok=True)
    path=parent/str(uuid4());path.mkdir()
    try:
        yield str(path)
    finally:
        # Recursive deletion applies only to this newly-created exact test workspace.
        if path.resolve().parent!=parent:raise RuntimeError('Invalid cleanup boundary')
        shutil.rmtree(path)
