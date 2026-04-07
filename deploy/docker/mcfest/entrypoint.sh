#!/usr/bin/env sh
set -eu
ROOT="${1:-/github/workspace}"
echo "mcfest (MC): placeholder — extend to run project-specific checks on ${ROOT}"
ls -la "${ROOT}" 2>/dev/null || true
