#!/usr/bin/env bash
# 00_check_env.sh — Validates binaries + Python packages + versions
# Open Verifier v2 environment check
#
# After cloning, make this file executable:
#   chmod +x .agents/skills/open-verifier/scripts/00_check_env.sh
#
# Usage:
#   bash .agents/skills/open-verifier/scripts/00_check_env.sh

set -e
ERRORS=0
FORMAL_AVAILABLE=true

check_binary() {
  local name=$1 min_ver=$2 cmd=$3 required=$4
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
  local ver
  ver=$(eval "$cmd" 2>&1 | grep -oP '\d+\.\d+' | head -1)
  echo "[OK]    $name $ver"
}

check_binary "verilator" "4.0" "verilator --version" "yes"
check_binary "iverilog"  "11.0" "iverilog -V"         "yes"
check_binary "gtkwave"   "3.3"  "gtkwave --version"   "yes"
check_binary "sby"       "0.9"  "sby --version"       "no"
check_binary "yosys"     "0.20" "yosys --version"     "no"
check_binary "z3"        "4.8"  "z3 --version"        "no"

# Python package checks against requirements.txt
echo "--- Python packages ---"
python3 - <<'EOF'
import importlib, sys
required = ["cocotb", "pyuvm", "cocotb_coverage", "fitz", "yaml", "constraint"]
optional = []
for pkg in required:
    try:
        importlib.import_module(pkg)
        print(f"[OK]    {pkg}")
    except ImportError:
        print(f"[ERROR] {pkg} not installed")
        sys.exit(1)
EOF

# Write formal availability flag for downstream scripts
echo "$FORMAL_AVAILABLE" > "$(dirname "$0")/../../../../out/.formal_available"

if [ "$ERRORS" -gt 0 ]; then
  echo ""
  echo "Environment check FAILED. Install missing required tools before proceeding."
  exit 1
fi

echo ""
echo "Environment check PASSED."
[ "$FORMAL_AVAILABLE" = "false" ] && echo "Note: Formal verification tools not found. Install sby + yosys + z3 to enable."
exit 0
