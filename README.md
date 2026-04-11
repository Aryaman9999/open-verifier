# Open Verifier

An AI-powered VLSI verification skill that turns your coding assistant into a strict, educational digital logic Teaching Assistant.

Students write Verilog — the assistant lints, scaffolds testbenches, runs simulations, and guides debugging using the **Socratic method**. It never hands out answers.

## What It Does

| Phase | Action |
|-------|--------|
| **0 — Environment Check** | Validates that Verilator, Icarus Verilog, and GTKWave are installed |
| **1 — Lint & Syntax** | Runs Verilator in strict mode to catch errors before simulation |
| **2 — TB Scaffolding** | Generates a testbench skeleton — students must write the stimulus themselves |
| **3 — Simulate & Debug** | Compiles and runs via Icarus Verilog, helps debug X/Z states through guided questions |
| **4 — Waveforms & Report** | Launches GTKWave and generates a structured verification report |

## Toolchain

| Tool | Purpose |
|------|---------|
| [Verilator](https://www.veripool.org/verilator/) | Linting & syntax checking |
| [Icarus Verilog](http://iverilog.icarus.com/) | Simulation engine |
| [GTKWave](https://gtkwave.sourceforge.net/) | Waveform viewer |

### Install (Linux)
```bash
sudo apt update && sudo apt install verilator iverilog gtkwave -y
```

### Install (macOS)
```bash
brew install verilator icarus-verilog gtkwave
```

## Repo Structure

```
.agents/skills/open-verifier/
├── SKILL.md              # Skill definition & workflow rules
├── scripts/
│   ├── 00_check_env.sh   # Environment validator
│   ├── 01_lint.sh        # Verilator lint runner
│   ├── 02_simulate.sh    # Icarus compile + VVP simulation
│   └── 03_view_waves.sh  # GTKWave launcher
├── resources/
│   ├── report_template.md
│   └── waiver.vlt        # Verilator lint waivers for beginners
└── examples/
    ├── 01_comb_alu.v         # Combinational ALU example
    ├── 01_comb_alu_tb.v
    ├── 02_seq_counter.v      # Sequential counter example
    └── 02_seq_counter_tb.v
src/    # Your DUT source files go here
tb/     # Your testbench files go here
out/    # Simulation outputs (VCD, logs)
```

## How to Use

1. Clone this repo and open it in an AI coding assistant that supports skills (e.g., Antigravity)
2. Place your Verilog DUT in `src/`
3. Ask the assistant to **verify**, **test**, or **simulate** your design
4. The skill activates automatically — it will lint your code, scaffold a testbench, and guide you through the full verification flow

## Examples Included

- **Combinational ALU** (`examples/01_comb_alu.v`) — 4-bit ALU with add, subtract, AND, OR
- **Sequential Counter** (`examples/02_seq_counter.v`) — 8-bit counter with synchronous reset and enable

## Philosophy

This skill is deliberately **not** a code generator. It follows a teaching-first approach:

- **Linting errors?** It explains the concept and asks a guiding question
- **Testbench needed?** It scaffolds the structure but forces students to write the test vectors
- **Simulation bugs?** It helps trace X/Z states backward instead of giving the fix

The goal is to build verification intuition, not copy-paste habits.

## License

MIT — see [LICENSE](./LICENSE).
