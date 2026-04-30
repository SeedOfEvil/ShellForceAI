#!/usr/bin/env bash
set -euo pipefail
[ -d .venv ] || python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
