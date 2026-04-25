#!/usr/bin/env bash
# 00_check_env.sh — Validates binaries + Python packages + versions
# Open Verifier v2 environment check
#
# Usage:
#   bash -l -c "bash .agents/skills/open-verifier/scripts/00_check_env.sh"
#
# NOTE: Do NOT source oss-cad-suite/environment before running this.
# Python packages are checked against the system Python (where cocotb/pyuvm live).
# Formal tool availability is checked separately.

set -e
mkdir -p out/

ERRORS=0
FORMAL_AVAILABLE=true

# state.json defensive initialization
STATE_FILE="out/state.json"
if [ ! -f "$STATE_FILE" ]; then
  echo '{"schema_version": "1.0", "steps": {}}' > "$STATE_FILE"
fi

update_state() {
  local step=$1 status=$2
  python3 -c "import json, pathlib; p=pathlib.Path('$STATE_FILE'); d=json.loads(p.read_text()); d['steps']['$step']={'status': '$status'}; p.write_text(json.dumps(d, indent=2))"
}

check_binary() {
  local name=$1 required=$2
  if ! command -v "$name" &>/dev/null; then
    if [ "$required" = "yes" ]; then
      echo "[ERROR] $name not found (required)"
      ERRORS=$((ERRORS + 1))
    else
      echo "[WARN]  $name not found — formal verification will be skipped"
      FORMAL_AVAILABLE=false
    fi
    return
  fi
  echo "[OK]    $name found"
}

echo "--- Toolchain Binaries (Simulation) ---"
check_binary "verilator" "yes"
check_binary "iverilog"  "yes"
check_binary "gtkwave"   "no"

# Formal tools: try sourcing oss-cad-suite if sby not already on PATH
echo "--- Toolchain Binaries (Formal) ---"
if ! command -v sby &>/dev/null; then
  if [ -f "$HOME/oss-cad-suite/environment" ]; then
    source "$HOME/oss-cad-suite/environment" 2>/dev/null
  fi
fi
check_binary "sby"   "no"
check_binary "yosys" "no"

# Deactivate oss-cad-suite environment if it was sourced (restore system Python)
if type deactivate &>/dev/null; then
  deactivate 2>/dev/null || true
fi

# Python package checks — uses system Python where cocotb/pyuvm are installed
echo "--- Python packages ---"
python3 - <<'PYEOF'
import importlib, sys

def check_version_gte(pkg_name, import_name, min_ver):
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"[ERROR] {pkg_name} not installed (pip install {pkg_name})")
        return False

    if min_ver is None:
        print(f"[OK]    {pkg_name}")
        return True

    try:
        from importlib.metadata import version as get_version
        actual = get_version(pkg_name)
    except Exception:
        print(f"[OK]    {pkg_name} (version check skipped)")
        return True

    def base_ver(v):
        return tuple(int(x) for x in v.split('+')[0].split('.dev')[0].split('.'))

    if base_ver(actual) >= base_ver(min_ver):
        print(f"[OK]    {pkg_name} {actual} (>= {min_ver})")
        return True
    else:
        print(f"[ERROR] {pkg_name} version too old: found {actual}, need >= {min_ver}")
        return False

all_ok = True
packages = [
    ("cocotb",          "cocotb",          "1.8.1"),
    ("pyuvm",           "pyuvm",           "2.8.0"),
    ("cocotb-coverage", "cocotb_coverage", "1.1.0"),
    ("PyYAML",          "yaml",            None),
    ("PyMuPDF",         "fitz",            None),
]

for pip_name, import_name, min_ver in packages:
    if not check_version_gte(pip_name, import_name, min_ver):
        all_ok = False

if not all_ok:
    sys.exit(1)
PYEOF

# Write formal availability flag
echo "$FORMAL_AVAILABLE" > "out/.formal_available"

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "Environment check FAILED. Install missing required tools before proceeding."
  exit 1
fi

echo ""
echo "Environment check PASSED."
update_state "env_check" "complete"
[ "$FORMAL_AVAILABLE" = "false" ] && echo "Note: Formal tools not found. Install oss-cad-suite to enable (see SKILL.md C12)."
exit 0
