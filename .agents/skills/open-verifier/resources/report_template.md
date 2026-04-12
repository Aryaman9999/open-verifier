# Verification Report

## 1. Design Context
* **DUT File:** [Path]
* **Testbench File:** [Path]
* **Testbench Source:** [Agent-Generated / User-Provided / Agent-Improved]

## 2. Environment
* **Date:** [Auto-filled by agent: YYYY-MM-DD]
* **iverilog version:** [Output of: iverilog -V 2>&1 | head -1]
* **Verilator version:** [Output of: verilator --version | head -1]
* **OS:** [Output of: uname -sr]

## 3. Compilation & Syntax
* **Verilator Lint:** [PASS / FAIL]
* **Icarus Elaborate:** [PASS / FAIL]
* **Agent Auto-Fixes Applied:** [None / List each fix as a bullet]

## 4. Simulation Results
* **Functional Status:** [PASS / FAIL / PARTIAL]
* **X/Z Anomalies Detected:** [None / Describe signal and likely cause]
* **Test Vectors & Scenarios Covered:**
  * [List each test case run — e.g., "ADD: 4+3=7 ✓"]
  * [Edge case: zero inputs]
  * [Edge case: max values / overflow]

## 5. Known Limitations / DUT Bugs Found
* [None / Describe any bugs found in the DUT that were NOT auto-fixed]

## 6. Waveforms
* **VCD Generated:** [Yes / No]
* **VCD Path:** `out/waves.vcd`
* **Viewer:** GTKWave (`bash .agents/skills/open-verifier/scripts/03_view_waves.sh`)
