#!/bin/bash

echo "Running Verilator Lint on all src files..."

# Find the absolute path to the waiver file relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
WAIVER_FILE="$SCRIPT_DIR/../resources/waiver.vlt"

# Create an array of all Verilog files in src directory
shopt -s nullglob
SRC_FILES=(src/*.v src/*.sv)

if [ ${#SRC_FILES[@]} -eq 0 ]; then
    echo "Error: No .v or .sv files found in src/"
    exit 1
fi

# -Wall enables strict linting. 
# --timing allows SystemVerilog delay syntax.
# --lint-only prevents compilation to C++, just checks syntax.
verilator --lint-only -Wall --timing "$WAIVER_FILE" "${SRC_FILES[@]}" 2>&1

if [ $? -eq 0 ]; then 
    echo "Linting passed. No syntax errors detected by Verilator."
    exit 0
else 
    echo "Linting failed. See Verilator output above for exact line numbers and warnings."
    exit 1
fi
