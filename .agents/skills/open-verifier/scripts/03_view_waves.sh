#!/bin/bash
VCD_FILE=$1

if [ -z "$VCD_FILE" ]; then 
    VCD_FILE="out/waves.vcd"
fi

if [ ! -f "$VCD_FILE" ]; then 
    echo "Error: Waveform file $VCD_FILE not found. Make sure \$dumpvars was in the TB."
    exit 1
fi

echo "Launching GTKWave..."
# OS detection for proper GUI launching
if [[ "$OSTYPE" == "darwin"* ]]; then
    open -a GTKWave "$VCD_FILE" &
else
    gtkwave "$VCD_FILE" &
fi
exit 0
