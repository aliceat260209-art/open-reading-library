#!/usr/bin/env python3
"""Fail if a candidate public repository tracks private reading-library assets."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BLOCKED_DIRS = {"books", "covers", "database", "imports", "exports", "uploads", "user-data"}
BLOCKED_SUFFIXES = {".epub", ".mobi", ".azw3", ".pdf", ".sqlite", ".sqlite-shm", ".sqlite-wal"}
BLOCKED_FILES = {".env"}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "ls-files"], cwd=root, text=True, capture_output=True, check=True)
    tracked = [Path(line) for line in result.stdout.splitlines() if line]
    violations = [str(path) for path in tracked if path.parts[0] in BLOCKED_DIRS or path.name in BLOCKED_FILES or path.suffix.lower() in BLOCKED_SUFFIXES]
    if violations:
        print("FAIL: private library assets are tracked:\n" + "\n".join(violations), file=sys.stderr)
        raise SystemExit(1)
    print("PASS: no private library assets tracked")

if __name__ == "__main__":
    main()
