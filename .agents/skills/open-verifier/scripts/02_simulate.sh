#!/bin/bash
TB_FILE=$1

if [ -z "$TB_FILE" ]; then 
    echo "Error: TB file must be provided. Usage: 02_simulate.sh <tb>"
    exit 1
fi

mkdir -p out

# Recursively find all Verilog files in src/ (supports hierarchical designs)
SRC_FILES=($(find src/ -name "*.v" -o -name "*.sv"))

if [ ${#SRC_FILES[@]} -eq 0 ]; then
    echo "Warning: No .v or .sv files found in src/. Simulating TB only."
fi

echo "Compiling with Icarus Verilog..."
# -g2012 enables SystemVerilog features like logic type and always_comb
iverilog -g2012 -o out/sim.vvp "${SRC_FILES[@]}" "$TB_FILE" 2>&1

if [ $? -ne 0 ]; then 
    echo "Compilation failed during Icarus elaboration phase."
    exit 1
fi

echo "Running Simulation via VVP engine..."
# Run simulation and output log
vvp out/sim.vvp | tee out/sim_output.log

echo "--------------------------------------------------------"
echo "Analysing simulation output for anomalies..."

# Check for X (unknown) or Z (high-impedance) states in signal output
# Matches common $monitor/$display patterns like: x, X, z, Z, xxxx, zzzz
if grep -qiE "(^|\s|=)[xz][xz0-9]*(\s|$|,)" out/sim_output.log; then
    echo "ANOMALY_DETECTED: Possible X or Z states found in simulation output."
    echo "ANOMALY_DETAIL: Review out/sim_output.log for lines containing x/z values."
    echo "AGENT_ACTION_REQUIRED: Diagnose root cause - check reset logic, undriven signals, or uninitialised registers in the DUT."
else
    echo "ANOMALY_CHECK: No X/Z states detected in simulation output."
fi

echo "--------------------------------------------------------"
echo "Simulation complete. Output logged to out/sim_output.log"
exit 0
