#!/bin/bash
MISSING_TOOLS=0
echo "--- Checking Open-Verifier Environment ---"

check_tool() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "[OK] $1 is installed. Path: $(command -v $1)"
    else
        echo "[ERROR] $1 is NOT installed."
        MISSING_TOOLS=1
    fi
}

check_tool "verilator"
check_tool "iverilog"
check_tool "vvp"
check_tool "gtkwave"

if [ $MISSING_TOOLS -ne 0 ]; then
    echo "STATUS: FAIL - Missing Dependencies."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "INSTRUCTION_FOR_AGENT: Tell the user to run: sudo apt update && sudo apt install verilator iverilog gtkwave -y"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "INSTRUCTION_FOR_AGENT: Tell the user to run: brew install verilator icarus-verilog ucb-bar/chisel/gtkwave"
    else
        echo "INSTRUCTION_FOR_AGENT: User OS unsupported for auto-instructions. Suggest using WSL if on Windows."
    fi
    exit 1
fi
echo "STATUS: PASS"
mkdir -p out src tb
exit 0
