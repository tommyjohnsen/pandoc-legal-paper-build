# PROVENANCE: written-by codex/gpt-6; 2026-11-13; commit in Git and .provenance/ledger.jsonl.
# Source this file from bash after tools/setup.py.
LEGAL_BUILD_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$LEGAL_BUILD_ROOT/.tools/bin:$LEGAL_BUILD_ROOT/.tools/node-v22.14.0-linux-x64/bin:$PATH"
export PYTHONPATH="$LEGAL_BUILD_ROOT/.tools/python${PYTHONPATH:+:$PYTHONPATH}"
export FONTCONFIG_FILE="$LEGAL_BUILD_ROOT/.tools/fonts.conf"
export XDG_CACHE_HOME="$LEGAL_BUILD_ROOT/build/.cache"
export SOURCE_DATE_EPOCH=1794528000
