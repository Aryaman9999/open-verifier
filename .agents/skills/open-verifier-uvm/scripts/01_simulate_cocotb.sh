#!/bin/bash
TB_DIR=$1

if [ -z "$TB_DIR" ]; then
    echo "Error: TB directory must be provided. Usage: 01_simulate_cocotb.sh <tb_dir>"
    exit 1
fi

if [ ! -f "$TB_DIR/Makefile" ]; then
    echo "Error: No Makefile found in $TB_DIR. cocotb requires a Makefile."
    exit 1
fi

mkdir -p out

echo "Running cocotb simulation in $TB_DIR..."
# Run make from the TB directory, capture output
make -C "$TB_DIR" SIM=icarus 2>&1 | tee out/sim_output.log

if [ $? -ne 0 ]; then
    echo "Simulation failed. See out/sim_output.log for details."
    exit 1
fi

echo "--------------------------------------------------------"
echo "Analysing simulation output for anomalies..."

if grep -qiE "(^|\s|=)[xz][xz0-9]*(\s|$|,)" out/sim_output.log; then
    echo "ANOMALY_DETECTED: Possible X or Z states found in simulation output."
    echo "ANOMALY_DETAIL: Review out/sim_output.log for lines containing x/z values."
    echo "AGENT_ACTION_REQUIRED: Diagnose root cause - check reset logic or undriven signals."
else
    echo "ANOMALY_CHECK: No X/Z states detected in simulation output."
fi

# Check for pyUVM PASS/FAIL markers
if grep -q "FAILED" out/sim_output.log; then
    echo "UVM_STATUS: FAIL - One or more pyUVM tests reported FAILED."
elif grep -q "PASSED" out/sim_output.log; then
    echo "UVM_STATUS: PASS - All pyUVM tests passed."
else
    echo "UVM_STATUS: UNKNOWN - Could not determine pass/fail from output."
fi

echo "Simulation complete. Output logged to out/sim_output.log"
exit 0
