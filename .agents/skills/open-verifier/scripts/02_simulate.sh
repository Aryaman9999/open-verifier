#!/bin/bash
TB_FILE=$1

if [ -z "$TB_FILE" ]; then 
    echo "Error: TB file must be provided. Usage: 02_simulate.sh <tb>"
    exit 1
fi

mkdir -p out

# Create an array of all Verilog files in src directory
shopt -s nullglob
SRC_FILES=(src/*.v src/*.sv)

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
echo "Simulation complete. Output logged to out/sim_output.log"
exit 0
