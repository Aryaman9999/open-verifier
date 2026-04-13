# UVM Verification Report

## 1. Design Context
* **DUT File:** [Path]
* **Testbench Directory:** [Path]
* **Testbench Source:** [Agent-Generated / User-Provided / Agent-Improved]

## 2. Environment
* **Date:** [Auto-filled by agent: YYYY-MM-DD]
* **cocotb version:** [Output of: python3 -c "import cocotb; print(cocotb.__version__)"]
* **pyUVM version:** [Output of: python3 -c "import pyuvm; print(pyuvm.__version__)"]
* **iverilog version:** [Output of: iverilog -V 2>&1 | head -1]
* **OS:** [Output of: uname -sr]

## 3. UVM Testbench Structure
* **Sequences Implemented:** [List each sequence class and what it drives]
* **Driver:** [Brief description]
* **Monitor:** [Brief description]
* **Scoreboard:** [Checking strategy — how correctness is verified]
* **Test Cases Run:** [List each @pyuvm.test class]

## 4. Simulation Results
* **Overall Status:** [PASS / FAIL / PARTIAL]
* **Per-Test Results:**
  * [test_name_1]: [PASS / FAIL]
  * [test_name_2]: [PASS / FAIL]
* **X/Z Anomalies Detected:** [None / Describe signal and likely cause]
* **Scoreboard Mismatches:** [None / List each mismatch with expected vs actual]

## 5. Known Limitations / DUT Bugs Found
* [None / Describe any bugs found in the DUT that were NOT auto-fixed]

## 6. Waveforms
* **VCD Generated:** [Yes / No]
* **VCD Path:** `out/waves.vcd`
* **Viewer:** GTKWave (`bash .agents/skills/open-verifier-uvm/scripts/02_view_waves.sh`)
