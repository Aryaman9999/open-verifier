# Agent Instructions — open-verifier v2: cocotb + pyUVM Tier

## Context

This document instructs you to implement the UVM verification tier for the
`open-verifier` project. The existing `master` branch contains a working
module-based SystemVerilog verification skill using Icarus Verilog + Verilator.
You are building a **parallel tier** on a new branch that adds UVM methodology
support via cocotb + pyUVM, keeping the open-source-only constraint.

**Do not touch or modify any files on master. All work is on the new branch.**

---

## Step 0 — Branch Setup

Create and switch to a new branch before doing anything else:

```bash
git checkout -b feature/cocotb-pyuvm
```

---

## Step 1 — Understand the Existing Structure

Before creating any files, read the following existing files so you understand
the conventions already established in this repo:

- `.agents/skills/open-verifier/SKILL.md` — existing skill structure and phase conventions
- `.agents/skills/open-verifier/scripts/00_check_env.sh` — env check pattern
- `.agents/skills/open-verifier/scripts/02_simulate.sh` — simulation runner pattern
- `.agents/skills/open-verifier/resources/report_template.md` — report format
- `README.md` — overall project documentation style

Match the style, naming conventions, and comment patterns of these files
exactly in everything you create.

---

## Step 2 — Create the New Skill Directory Structure

Create the following directory tree. Do not create any files yet, just the
directories:

```
.agents/skills/open-verifier-uvm/
├── SKILL.md
├── scripts/
│   ├── 00_check_env_uvm.sh
│   ├── 01_simulate_cocotb.sh
│   └── 02_view_waves.sh          ← identical to master version, copy it
├── resources/
│   └── report_template_uvm.md
└── examples/
    ├── 03_simple_alu.v            ← reuse-friendly DUT for UVM example
    └── test_simple_alu/
        ├── test_alu.py            ← pyUVM testbench
        └── Makefile               ← cocotb Makefile for this example
```

Also create:

```
uvm_tb/        ← where agent-generated cocotb testbenches land (like tb/ on master)
```

---

## Step 3 — Create `00_check_env_uvm.sh`

**Path:** `.agents/skills/open-verifier-uvm/scripts/00_check_env_uvm.sh`

This script must check for ALL of the following tools and report clearly on
each. Follow the exact same pattern as the existing `00_check_env.sh`:

Tools to check:
- `iverilog` — simulation backend for cocotb
- `python3` — required for cocotb and pyUVM
- `pip3` — required to install Python packages
- `cocotb` — check via `python3 -c "import cocotb" 2>/dev/null`
- `pyuvm` — check via `python3 -c "import pyuvm" 2>/dev/null`
- `gtkwave` — waveform viewer

For Python packages (cocotb, pyuvm), if they are missing, print:

```
INSTRUCTION_FOR_AGENT: Tell the user to run: pip3 install cocotb pyuvm --break-system-packages
```

At the end, if all checks pass, run:

```bash
mkdir -p out uvm_tb src
```

Exit 0 on full pass, exit 1 on any missing tool.

---

## Step 4 — Create `01_simulate_cocotb.sh`

**Path:** `.agents/skills/open-verifier-uvm/scripts/01_simulate_cocotb.sh`

This script takes one argument: the path to the testbench directory
(e.g., `uvm_tb/test_my_dut/`).

```bash
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
```

---

## Step 5 — Copy `02_view_waves.sh`

Copy the existing waveform viewer script verbatim:

```bash
cp .agents/skills/open-verifier/scripts/03_view_waves.sh \
   .agents/skills/open-verifier-uvm/scripts/02_view_waves.sh
```

No changes needed — GTKWave usage is identical.

---

## Step 6 — Create `report_template_uvm.md`

**Path:** `.agents/skills/open-verifier-uvm/resources/report_template_uvm.md`

```markdown
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
```

---

## Step 7 — Create the SKILL.md

**Path:** `.agents/skills/open-verifier-uvm/SKILL.md`

```markdown
---
name: open-verifier-uvm
description: UVM verification assistant using cocotb + pyUVM. Generates UVM-methodology testbenches in Python, executes simulation via Icarus Verilog backend, and produces structured verification reports. Trigger when a user asks to verify a DUT using UVM, cocotb, sequences, scoreboards, or constrained-random testing.
---

# Open Verifier UVM Tier

You are an expert UVM verification assistant. Your goal is to take a user's
Design Under Test (DUT), verify it end-to-end using UVM methodology via
cocotb + pyUVM, and deliver a clean report.

---

## Toolchain Grounding Rules

**BACKEND:** cocotb drives the DUT from Python. Icarus Verilog is the
simulation engine (`SIM=icarus`). The DUT itself is still written in
Verilog/SystemVerilog — only the TESTBENCH is Python.

**PYUVM METHODOLOGY:** pyUVM implements UVM in Python. The class names and
methodology mirror standard UVM exactly:
- `uvm_component` → base for all TB components
- `uvm_sequence_item` → transaction object
- `uvm_sequence` → stimulus generator
- `uvm_driver` → drives DUT pins via cocotb coroutines
- `uvm_monitor` → samples DUT outputs
- `uvm_scoreboard` → checks correctness
- `uvm_env` → assembles components
- `uvm_test` → top-level test class, decorated with `@pyuvm.test`

**NO SV TESTBENCH:** Do not generate any SystemVerilog testbench. The entire
TB is Python. The DUT source files remain as .v or .sv in src/.

**COCOTB COROUTINES:** All signal interactions use `await` syntax:
```python
await cocotb.triggers.RisingEdge(dut.clk)
dut.input_signal.value = 1
await cocotb.triggers.Timer(10, units="ns")
```

**MAKEFILE REQUIRED:** Every cocotb testbench directory needs a Makefile.
Always generate it with this template:
```makefile
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
VERILOG_SOURCES = $(shell find $(PWD)/../../src -name "*.v" -o -name "*.sv")
TOPLEVEL = <dut_module_name>
MODULE = test_<dut_name>
include $(shell cocotb-config --makefiles)/Makefile.sim
```

**VCD WAVEFORMS:** Add this to the Makefile to enable VCD output with Icarus:
```makefile
export COCOTB_RESOLVE_X ?= ZEROS
COMPILE_ARGS += -DVCD_OUTPUT
```
And in the Python TB, add a `$dumpfile`/`$dumpvars` equivalent via:
```python
dut._id("$dumpfile", extended=False)  # Not needed — cocotb handles VCD via Makefile
```
Instead, set in Makefile: `WAVES ?= 1`

---

## Workflow Execution Phases

### Phase 1: Environment Check
Action: Run `.agents/skills/open-verifier-uvm/scripts/00_check_env_uvm.sh`
On Failure: Relay exact installation instructions and HALT until user confirms.

### Phase 2: DUT Lint (Reuse existing skill)
Action: Run `.agents/skills/open-verifier/scripts/01_lint.sh`
This reuses the master branch Verilator linter — the DUT is still Verilog.
Follow the same confirmation-gate rule: NEVER modify DUT files without explicit
user confirmation. Present issues with before/after diffs, wait for yes/no.

### Phase 3: UVM Testbench Handling

Pre-check: Scan `uvm_tb/` for an existing testbench directory for this DUT.

If an existing TB is found:
- List the found directory and its files to the user.
- Ask: "I found an existing cocotb testbench at `uvm_tb/<dir>/`. Would you like me to:
  (A) Use it as-is,
  (B) Review and improve it, or
  (C) Discard it and generate a fresh one?"
- Follow the same A/B/C logic as the master skill.

If no existing TB (full generation):
Generate a complete pyUVM testbench in `uvm_tb/<dut_name>/` containing:

1. `test_<dut_name>.py` with ALL of the following classes:
   - A `<DutName>Item` class extending `uvm_sequence_item` with transaction fields
   - A `<DutName>Sequence` class extending `uvm_sequence` generating stimulus
     - Must cover: normal operation, edge cases (zero, max values), boundary conditions
   - A `<DutName>Driver` class extending `uvm_driver` using cocotb coroutines
   - A `<DutName>Monitor` class extending `uvm_monitor` sampling DUT outputs
   - A `<DutName>Scoreboard` class extending `uvm_scoreboard` with a reference model
   - A `<DutName>Env` class extending `uvm_env` wiring everything together
   - At minimum TWO test classes decorated with `@pyuvm.test`:
     - `Test<DutName>Normal` — standard functional test
     - `Test<DutName>EdgeCases` — boundary/edge case test

2. `Makefile` — using the template above, filled in for this DUT

3. Include `cocotb.log` statements at key points so the agent can read
   pass/fail status from simulation output.

### Phase 4: Simulation
Action: Run `.agents/skills/open-verifier-uvm/scripts/01_simulate_cocotb.sh uvm_tb/<dut_name>/`
Analysis: Read `out/sim_output.log` and check for:
- pyUVM PASSED/FAILED markers per test
- Scoreboard mismatch messages
- X/Z anomaly flags from the script
- Any Python exceptions or cocotb errors

On Failure: Diagnose, fix the testbench (NOT the DUT unless confirmed by user),
re-run until clean.

### Phase 5: Report + Waveforms
Action:
1. Run `python3 -c "import cocotb; print(cocotb.__version__)"` and
   `python3 -c "import pyuvm; print(pyuvm.__version__)"` to get versions.
2. Read `.agents/skills/open-verifier-uvm/resources/report_template_uvm.md`
3. Fill in and save the report to `out/uvm_report.md`
4. Present the report summary in chat.
5. Ask: "Simulation complete. Would you like me to open GTKWave?"
6. If yes: run `.agents/skills/open-verifier-uvm/scripts/02_view_waves.sh`

---

## IMPORTANT Global Rules

- NEVER silently modify any DUT (.v or .sv) file at any point in the workflow.
- NEVER generate SystemVerilog testbenches — all TB code is Python.
- ALWAYS explain cocotb/pyUVM concepts in plain English when reporting issues,
  since students may be new to both Python-based TB and UVM methodology.
- When a student asks "what is a sequencer" or "why do I need a scoreboard",
  answer in plain English before continuing the workflow — treat these as
  teaching moments, not interruptions.
```

---

## Step 8 — Create Example DUT

**Path:** `.agents/skills/open-verifier-uvm/examples/03_simple_alu.v`

Create a simple 8-bit ALU DUT (add, subtract, AND, OR operations) with:
- Inputs: `clk`, `rst`, `a [7:0]`, `b [7:0]`, `op [1:0]`
- Output: `result [8:0]` (9 bits to capture carry/overflow)
- Synchronous reset
- Clean, well-commented Verilog — this is a teaching example

---

## Step 9 — Create Example pyUVM Testbench

**Path:** `.agents/skills/open-verifier-uvm/examples/test_simple_alu/test_alu.py`

Write a complete, well-commented pyUVM testbench for `03_simple_alu.v` that:
- Implements all 6 classes (Item, Sequence, Driver, Monitor, Scoreboard, Env)
- Has TWO test classes: `TestALUNormal` and `TestALUEdgeCases`
- Uses `cocotb.log.info()` for clear test progress logging
- Has a reference model in the scoreboard (Python function mirroring ALU logic)
- Is heavily commented explaining WHAT each class does and WHY — this is a
  teaching example students will read to understand UVM methodology

**Path:** `.agents/skills/open-verifier-uvm/examples/test_simple_alu/Makefile`

Create the cocotb Makefile pointing at `03_simple_alu.v`.

---

## Step 10 — Update Root README.md

Add a new section to the existing `README.md` (do NOT rewrite the existing
content, only append). Add after the existing "What Makes This Different"
section:

```markdown
## UVM Tier (Branch: `feature/cocotb-pyuvm`)

A second verification tier is available on the `feature/cocotb-pyuvm` branch,
adding full UVM methodology support via cocotb + pyUVM.

| Feature | master (Tier 1) | feature/cocotb-pyuvm (Tier 2) |
|---|---|---|
| Testbench language | Verilog/SystemVerilog | Python |
| Methodology | Module-based | Full UVM (sequences, driver, monitor, scoreboard) |
| Simulation backend | Icarus Verilog | Icarus Verilog via cocotb |
| UVM classes | No | Yes (pyUVM) |
| Best for | Beginners | Intermediate / UVM methodology learners |

### Additional Install (UVM Tier)
pip3 install cocotb pyuvm
```

---

## Step 11 — Commit

Once all files are created and verified, make a single clean commit:

```bash
git add .
git commit -m "feat: add cocotb + pyUVM verification tier (Tier 2)

- New skill: .agents/skills/open-verifier-uvm/
- Scripts: env check, cocotb simulation runner, waveform viewer
- SKILL.md with full UVM workflow phases and grounding rules
- pyUVM testbench template covering all 6 UVM classes
- Example: 8-bit ALU DUT + complete annotated pyUVM testbench
- Updated README with Tier 1 vs Tier 2 comparison table"
```

---

## Verification Checklist

Before committing, confirm every item:

- [ ] Branch is `feature/cocotb-pyuvm`, NOT master
- [ ] No files on master have been modified
- [ ] `00_check_env_uvm.sh` checks all 6 tools/packages
- [ ] `01_simulate_cocotb.sh` runs `make -C` with `SIM=icarus`
- [ ] `01_simulate_cocotb.sh` includes X/Z grep and UVM PASS/FAIL grep
- [ ] `SKILL.md` includes the Makefile template
- [ ] `SKILL.md` has the DUT-modification confirmation gate rule
- [ ] Example DUT is clean, well-commented Verilog
- [ ] Example pyUVM TB has all 6 classes + 2 test classes
- [ ] Example pyUVM TB is heavily commented for teaching
- [ ] README updated with tier comparison table
- [ ] All new scripts start with `#!/bin/bash`
- [ ] `uvm_tb/` directory created (add a `.gitkeep` inside it)