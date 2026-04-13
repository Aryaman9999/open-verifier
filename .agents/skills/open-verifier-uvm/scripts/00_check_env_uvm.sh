#!/bin/bash
MISSING_TOOLS=0
echo "--- Checking Open-Verifier UVM Environment ---"

check_tool() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "[OK] $1 is installed. Path: $(command -v $1)"
    else
        echo "[ERROR] $1 is NOT installed."
        MISSING_TOOLS=1
    fi
}

check_python_pkg() {
    if python3 -c "import $1" 2>/dev/null; then
        echo "[OK] Python package '$1' is installed."
    else
        echo "[ERROR] Python package '$1' is NOT installed."
        MISSING_TOOLS=1
    fi
}

check_tool "iverilog"
check_tool "python3"
check_tool "pip3"
check_python_pkg "cocotb"
check_python_pkg "pyuvm"
check_tool "gtkwave"

if [ $MISSING_TOOLS -ne 0 ]; then
    echo "STATUS: FAIL - Missing Dependencies."
    echo "INSTRUCTION_FOR_AGENT: Tell the user to run: pip3 install cocotb pyuvm --break-system-packages"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "INSTRUCTION_FOR_AGENT: Tell the user to run: sudo apt update && sudo apt install iverilog gtkwave -y"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "INSTRUCTION_FOR_AGENT: Tell the user to run: brew install icarus-verilog gtkwave"
    else
        echo "INSTRUCTION_FOR_AGENT: User OS unsupported for auto-instructions. Suggest using WSL if on Windows."
    fi
    exit 1
fi
echo "STATUS: PASS"
mkdir -p out uvm_tb src
exit 0
