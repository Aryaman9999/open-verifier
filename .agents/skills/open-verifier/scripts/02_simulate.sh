#!/bin/bash
DUT_FILE=$1
TB_FILE=$2

if [ -z "$DUT_FILE" ] || [ -z "$TB_FILE" ]; then 
    echo "Error: Both DUT and TB files must be provided. Usage: 02_simulate.sh <dut> <tb>"
    exit 1
fi

mkdir -p out

echo "Compiling with Icarus Verilog..."
# -g2012 enables SystemVerilog features like logic type and always_comb
iverilog -g2012 -o out/sim.vvp "$DUT_FILE" "$TB_FILE" 2>&1

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
