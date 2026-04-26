# Open-Verifier v2 — Comprehensive Walkthrough

This guide walks you through the complete end-to-end verification flow while highlighting the safety mechanisms that ensure a robust, black-box verification environment.

---

## 🏗 Phase 1: Environment Setup & Black-Box Discovery

### Step 1: Environment Validation
Ensures all tools are present. Crucial for Windows/WSL users to confirm `iverilog` and `verilator` are visible via login-shell orchestration.
```bash
bash -l -c "bash .agents/skills/open-verifier/scripts/00_check_env.sh"
```

### Step 2: AST-Based Elaboration
Rather than reading your source code (which would violate verification independence), Open-Verifier runs Verilator to generate an XML representation of your design's hierarchy.
```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/02_elaborate.py --top <module_name>"
```
> [!IMPORTANT]
> **Black-Box Standard**: By parsing the XML AST, the agent discovers signal widths and types from the `typetable` without analyzing implementation details. This maintains the integrity of the "Stimulus-Response" verification model.

---

## 📄 Phase 2: Agentic Specification Extraction

### Step 3: Intelligent Pagination
When protocol rules or timing diagrams span multiple pages in your PDF, the agent uses **Intelligent Pagination** (`03a_fetch_adjacent_pages.py`) to retrieve "look-ahead" context. This ensures that a rule starting on Page 4 and ending on Page 5 is captured in its entirety.

### Step 4: Binding Review (The Human Bridge)
To ensure the testbench connects to the correct physical ports, you will review the `out/binding_map.yaml`. This step bridges the gap between spec-nomenclature (e.g., "Ready Signal") and RTL-nomenclature (e.g., `o_rdy`).
> [!NOTE]
> The workflow **halts** here. You must approve the binding map to prevent driving the wrong signals.

---

## 🛡 Phase 3: Formal Guard Pre-Check

### Step 6b: Scan for Unguarded Simulation Constructs
Before generating any testbench file, the agent scans the DUT for `$display`, `$finish`, `$readmemh`, `$dumpfile`, and `$dumpvars` that are not inside `` `ifndef FORMAL `` guards. These constructs cause Yosys to abort during formal elaboration.

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/06b_formal_guard_check.py"
```

The script outputs structured JSON showing which constructs are guarded and which are not. It also checks for the VCD dump block required for waveform capture during simulation.

> [!WARNING]
> If unguarded constructs are found, the agent halts and asks you to add guards before proceeding. Skipping this step means formal verification will fail at STEP 18 with `ERROR: Found simulation-only construct`.

---

## 🧪 Phase 4: Modular Testbench Generation

### DUT-Agnostic Design
All class names, signal names, and field names are derived from the YAML artifacts at generation time — never hardcoded. The `{ProtocolName}` pattern ensures the same skill works for AXI, SPI, I2C, or any protocol.

### Token-Limit Optimized Workflow
Each UVM component (`driver`, `monitor`, `scoreboard`, etc.) is generated in its own "turn". This ensures:
1.  **Completeness**: No truncated code blocks due to LLM output limits.
2.  **Validation**: Each file is immediately checked for syntax errors by `04_validate_step.py`.

### X-Propagation Protocol
In `driver.py`, the agent automatically implements an **X-Init Guard**. All inputs are initialized to `0` at `t=0`, preventing the common Icarus Verilog issue where uninitialized 'X' values propagate through logic before the first reset edge.

### VALID/READY Handshake Enforcement
The driver `_drive()` method implements a proper handshake wait loop: once VALID is asserted, it is held until READY is sampled high. This prevents the most common driver bug — deasserting VALID after one clock regardless of READY — which silently corrupts every transaction and produces false assertion failures downstream.

---

## 🏃 Phase 5: Simulation & Analysis

### Handshake-Aware Monitoring
The `monitor.py` uses a `RisingEdge(clk)` plus `ReadOnly()` pattern. This ensures that signals are only sampled after all delta-cycles are resolved, capturing true registered outputs and avoiding race conditions in the simulation.

### Toggle Coverage Analysis (The Feedback Loop)
After simulation, run the toggle processor to bridge the gap between functional and code coverage:
```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/08_toggle_coverage.py"
```
**Why it matters**: This step reads your simulation waveform (`waves.vcd`) and cross-references it with the AST-extracted signal list. It generates a table in your report showing which ports transitioned (`0→1`, `1→0`). Any port marked **NONE** or **PARTIAL** indicates a hole in your testbench sequences that needs to be filled.

---

## 🔒 Phase 6: Formal Verification

### Assume vs Assert Strategy
For slave DUTs, master-driven inputs (VALID, ADDR, DATA) are modeled as `assume` constraints while slave-driven outputs (READY, RESP) are checked with `assert`. This prevents false failures from the solver exploring invalid input combinations.

### Reset Initialization
Every formal properties module includes `initial assume(rst)` (or `!rst_n` for active-low) to ensure the solver starts from a valid reset state instead of exploring uninitialized garbage.

### BMC vs K-Induction Decision
The agent automatically chooses the formal mode based on the DUT's characteristics:
- **BMC** (`mode bmc depth 50`): for designs without large memory arrays — finds bugs within N cycles
- **K-induction** (`mode prove depth 20`): for memory DUTs or when BMC times out — proves properties hold for all reachable states

### Memory Parameter Reduction
For DUTs with parameterized memories (ADDR_WIDTH, DEPTH), formal with full-size memory is intractable. The agent injects `chparam -set ADDR_WIDTH 4` into the SBY config to reduce the state space. Handshake properties don't depend on memory depth.

### Timeout Protection
`07_run_formal.sh` kills SymbiYosys after 180 seconds and outputs a structured `FORMAL_TIMEOUT` message with recovery steps: switch mode, reduce parameters, or document as state-space limitation.

---

## 📊 State Management

Pipeline progress is tracked in `out/state.json`. Interrupted runs resume from the last completed step. State updates use the CLI script exclusively:
```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/update_state.py <step_name> --status complete"
```

> [!CAUTION]
> The agent is prohibited from writing `state.json` directly or using inline `python3 -c` commands. These fail due to Windows↔bash↔Python triple-quoting issues. The `update_state.py` script handles all edge cases.

---
*Open-Verifier v2 — Autonomous, Robust, and Context-Aware.*
