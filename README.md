# Open-Verifier v2 🚀

An autonomous, agentic toolchain for end-to-end VLSI verification. Open-Verifier automates the journey from a hardware specification PDF and RTL source code to a comprehensive UVM-based verification environment and simulation report.

## 🏛 Architectural Philosophy

Open-Verifier is built on a **Black-Box Verification Standard**. To maintain strict verification integrity, the agent is prohibited from reading source code in `src/`. Instead, it interacts with the design through structured metadata and elaborated artifacts.

### 🔍 Key Features

- **AST-Driven Elaboration**: Uses Verilator XML AST parsing to extract design interfaces. This ensures the agent understands the DUT boundaries (ports, widths, types) without ever "seeing" the implementation logic, maintaining a true black-box stimulus/response relationship.
- **Intelligent Agentic Pagination**: Employs context-aware retrieval to fetch adjacent PDF pages when diagrams or rules span page boundaries. This prevents "fragmented context" errors and ensures protocol rules are complete and accurate.
- **Reliability-First Generation**: Testbench components are generated one file at a time, strictly adhering to **Output Token Limits**. This modular approach prevents truncation errors and ensures every class, method, and constraint is fully implemented.
- **Interactive Binding Map**: A dedicated human-in-the-loop phase where spec signal names are mapped to DUT ports. This prevents the "naming mismatch" common in automated tools and ensures the testbench drives the correct physical wires.
- **Toggle Coverage Post-Processor**: A pure-Python VCD parser (`08_toggle_coverage.py`) that automatically appends a signal transition table to your verification report. It identifies untoggled ports to guide iterative sequence generation.
- **Robust X-Propagation Handling**: Integrated protocol for Icarus Verilog and Verilator that pre-drives all DUT inputs to `0` before reset release. This stops 'X' states from entering the design and causing spurious simulation failures.

## 🛠 Technology Stack

- **Core**: Python 3.12+, Bash
- **Verification Framework**: `cocotb`, `pyuvm` 2.8.0
- **Simulation**: Icarus Verilog (`iverilog`), Verilator
- **Analysis**: PyMuPDF (`fitz`) for Structural PDF Parsing, Verilator XML for AST Elaboration, Custom VCD Parser for Toggle Coverage.
- **Formal**: Yosys, SymbiYosys (SBY), Z3

## 📖 Workflow Architecture

The toolchain follows a deterministic 20-step verification pipeline:

1. **Environment Check**: Validates binaries and python packages.
2. **Filelist Generation**: Scans for source files recursively.
3. **AST Elaboration**: Enforces the black-box boundary via XML export.
4. **Agentic Spec Extraction**: Context-aware rule parsing from PDF.
5. **Binding Review**: Human-validated spec-to-DUT mapping.
6. **TB Generation**: Layered UVM file creation (modular for token-limit safety).
7. **Simulation**: Execution of constrained random tests.
8. **Toggle Analysis**: VCD-based structural verification.
9. **Final Reporting**: Automated generation of markdown-based verification summaries.

## 🚀 Getting Started

1. Place Verilog/SystemVerilog source files in `src/`.
2. Provide a protocol specification PDF in the root.
3. Run initialization:
   ```bash
   bash .agents/skills/open-verifier/scripts/00_check_env.sh
   ```

---

*Open-Verifier v2 — Autonomous, Black-Box, Scalable Verification.*
