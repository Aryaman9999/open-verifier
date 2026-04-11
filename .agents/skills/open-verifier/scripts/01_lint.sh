#!/bin/bash
DUT_FILE=$1
if [ -z "$DUT_FILE" ]; then 
    echo "Error: No DUT file provided."
    exit 1
fi

echo "Running Verilator Lint on $DUT_FILE..."

# Find the absolute path to the waiver file relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
WAIVER_FILE="$SCRIPT_DIR/../resources/waiver.vlt"

# -Wall enables strict linting. 
# --timing allows SystemVerilog delay syntax.
# --lint-only prevents compilation to C++, just checks syntax.
verilator --lint-only -Wall --timing "$WAIVER_FILE" "$DUT_FILE" 2>&1

if [ $? -eq 0 ]; then 
    echo "Linting passed. No syntax errors detected by Verilator."
    exit 0
else 
    echo "Linting failed. See Verilator output above for exact line numbers and warnings."
    exit 1
fi
