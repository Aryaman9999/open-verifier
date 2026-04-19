# Open-Verifier v2 — Comprehensive Walkthrough

This guide walks you through the complete end-to-end verification flow while highlighting the safety mechanisms that ensure a robust, black-box verification environment.

---

## 🏗 Phase 1: Environment Setup & Black-Box Discovery

### Step 1: Environment Validation
Ensures all tools are present. Crucial for Windows/WSL users to confirm `iverilog` and `verilator` are visible via login-shell orchestration.
```bash
bash .agents/skills/open-verifier/scripts/00_check_env.sh
```

### Step 2: AST-Based Elaboration
Rather than reading your source code (which would violate verification independence), Open-Verifier runs Verilator to generate an XML representation of your design's hierarchy.
```bash
python3 .agents/skills/open-verifier/scripts/02_elaborate.py --top <module_name>
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

## 🧪 Phase 3: Modular Testbench Generation

### Token-Limit Optimized Workflow
Each UVM component (`driver`, `monitor`, `scoreboard`, etc.) is generated in its own "turn". This ensures:
1.  **Completeness**: No truncated code blocks due to LLM output limits.
2.  **Validation**: Each file is immediately checked for syntax errors by `.agents/skills/open-verifier/scripts/04_validate_step.py`.

### X-Propagation Protocol
In `driver.py`, the agent automatically implements an **X-Init Guard**. All inputs are initialized to `0` at `t=0`, preventing the common Icarus Verilog issue where uninitialized 'X' values propagate through logic before the first reset edge.

---

## 🏃 Phase 4: Simulation & Analysis

### Handshake-Aware Monitoring
The `monitor.py` uses a `RisingEdge(clk)` plus `ReadOnly()` pattern. This ensures that signals are only sampled after all delta-cycles are resolved, capturing true registered outputs and avoiding race conditions in the simulation.

### Step 20: Toggle Coverage Analysis (The Feedback Loop)
After simulation, run the toggle processor to bridge the gap between functional and code coverage:
```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/08_toggle_coverage.py"
```
**Why it matters**: This step reads your simulation waveform (`waves.vcd`) and cross-references it with the AST-extracted signal list. It generates a table in your report showing which ports transitioned (`0→1`, `1→0`). Any port marked **NONE** or **PARTIAL** indicates a hole in your testbench sequences that needs to be filled, allowing you to iterate on your verification plan with precision.

---
*Open-Verifier v2 — Autonomous, Robust, and Context-Aware.*
