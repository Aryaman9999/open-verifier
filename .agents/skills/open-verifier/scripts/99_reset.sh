#!/bin/bash
# Reset the environment to a blank state for a new verification run.

echo "[open-verifier] Resetting workspace..."

# 1. Remove output artifacts
rm -rf out/
echo "  - Removed out/"

# 2. Remove generated testbench
rm -rf uvm_tb/
echo "  - Removed uvm_tb/"

# 3. Remove temporary simulation files
rm -rf sim_build/
rm -f results.xml
echo "  - Removed simulation temp files"

# 4. Clean up python caches
find . -type d -name "__pycache__" -exec rm -rf {} +
echo "  - Cleaned python caches"

echo "[open-verifier] Workspace is now clean and ready for a new run."
