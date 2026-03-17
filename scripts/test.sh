#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

.venv/bin/python -m pip install -e ".[test]" >/dev/null
.venv/bin/pytest -q
