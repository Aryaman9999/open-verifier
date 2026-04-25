#!/usr/bin/env bash
# 07_run_formal.sh — Runs SymbiYosys, parses output, feeds error taxonomy.
#
# Usage:
#   bash -l -c "source ~/oss-cad-suite/environment && bash .agents/skills/open-verifier/scripts/07_run_formal.sh"

set -e

# Resolve repo root from script location (scripts/ -> open-verifier/ -> skills/ -> .agents/ -> root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
FORMAL_DIR="$REPO_ROOT/uvm_tb/formal"
OUT_DIR="$REPO_ROOT/out"

# Pre-flight: ensure oss-cad-suite environment is active
if ! command -v sby &>/dev/null; then
  echo "[WARN] sby not found. Attempting to source ~/oss-cad-suite/environment..."
  if [ -f "$HOME/oss-cad-suite/environment" ]; then
    source "$HOME/oss-cad-suite/environment"
  fi
fi

if ! command -v sby &>/dev/null; then
  echo '{"formal_status": "SKIPPED", "reason": "sby not found even after sourcing environment"}' > "$OUT_DIR/formal_result.json"
  echo "[WARN] Formal verification SKIPPED — sby not available."
  exit 0
fi

cd "$FORMAL_DIR"

sby -f verify.sby 2>&1 | tee formal_run.log

if grep -q "DONE (PASS" formal_run.log; then
  STATUS="PROVED"
elif grep -q "DONE (FAIL" formal_run.log; then
  STATUS="FAILED"
else
  STATUS="ERROR"
fi

# Extract per-property results for report
export STATUS
export OUT_DIR
python3 - <<'PYEOF'
import re, json, os
status = os.environ["STATUS"]
out_dir = os.environ["OUT_DIR"]
with open("formal_run.log") as f:
    log = f.read()
results = []
for m in re.finditer(r'\[(PROVED|FAILED)\].*?(\w+)', log):
    results.append({"status": m.group(1), "property": m.group(2)})
with open(os.path.join(out_dir, "formal_result.json"), "w") as f:
    json.dump({"formal_status": status, "properties": results}, f, indent=2)
PYEOF
