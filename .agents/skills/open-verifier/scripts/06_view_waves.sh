#!/usr/bin/env bash
# 06_view_waves.sh — Launch GTKWave for simulation or formal counterexample VCD.
#
# Usage:
#   bash 06_view_waves.sh                          # opens out/waves.vcd (simulation)
#   bash 06_view_waves.sh --formal <path/to/cex.vcd>  # opens formal counterexample
#
# After cloning, make this file executable:
#   chmod +x .agents/skills/open-verifier/scripts/06_view_waves.sh
#
# Exits with an error if gtkwave is not found or the VCD file does not exist.

set -e

# Resolve script directory for relative path defaults
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEFAULT_VCD="${SCRIPT_DIR}/../../../../out/waves.vcd"

# Check gtkwave is available
if ! command -v gtkwave &>/dev/null; then
  echo "[ERROR] gtkwave not found. Install GTKWave >= 3.3 to view waveforms."
  echo "  Ubuntu/Debian: sudo apt install gtkwave"
  echo "  macOS:         brew install gtkwave"
  exit 1
fi

# Parse arguments
VCD_FILE=""
if [ "$1" = "--formal" ]; then
  if [ -z "$2" ]; then
    echo "[ERROR] --formal requires a path to the counterexample VCD file."
    echo "Usage: bash 06_view_waves.sh --formal <path/to/cex.vcd>"
    exit 1
  fi
  VCD_FILE="$2"
  echo "[INFO] Opening formal counterexample VCD: $VCD_FILE"
elif [ -n "$1" ]; then
  # Treat first argument as VCD path
  VCD_FILE="$1"
  echo "[INFO] Opening VCD: $VCD_FILE"
else
  # Default: simulation waveform
  VCD_FILE="$DEFAULT_VCD"
  echo "[INFO] Opening simulation VCD: $VCD_FILE"
fi

# Verify VCD file exists
if [ ! -f "$VCD_FILE" ]; then
  echo "[ERROR] VCD file not found: $VCD_FILE"
  echo "  Run simulation first (cd uvm_tb && make) or check the path."
  exit 1
fi

# Launch GTKWave
echo "[INFO] Launching GTKWave..."
gtkwave "$VCD_FILE" &
echo "[OK] GTKWave launched for: $VCD_FILE"
