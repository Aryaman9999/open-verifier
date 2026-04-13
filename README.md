# Open Verifier

An AI-powered VLSI verification skill that turns your coding assistant into an automated end-to-end verification engineer for Verilog and SystemVerilog designs.

You provide the DUT — the agent handles linting, testbench generation, simulation, debugging, and report generation. Fully autonomous, only pausing when it needs your input.

## How It Works

```
DUT ──▶ Env Check ──▶ Syntax Lint ──▶ TB Generation ──▶ Simulate ──▶ Report + Waveforms
         (auto)        (auto)          (auto)            (auto)        (delivered)
```

| Phase | What Happens |
|-------|-------------|
| **1 — Environment Check** | Validates that Verilator, Icarus Verilog, and GTKWave are installed |
| **2 — Syntax Lint** | Runs Verilator in strict mode; reports issues and offers to auto-fix them |
| **3 — Testbench Generation** | Generates a complete testbench with full stimulus, edge cases, clock gen, and VCD dump |
| **4 — Simulation** | Compiles and runs via Icarus Verilog; analyzes output for X/Z states and functional bugs |
| **5 — Report & Waveforms** | Generates a structured verification report and offers to launch GTKWave |

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

### Windows
Use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) and install the Linux packages above.

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
│   └── waiver.vlt        # Verilator lint waivers
└── examples/
    ├── 01_comb_alu.v         # Combinational ALU example
    ├── 01_comb_alu_tb.v
    ├── 02_seq_counter.v      # Sequential counter example
    └── 02_seq_counter_tb.v
src/    # Place your DUT source files here
tb/     # Auto-generated testbenches land here
out/    # Simulation outputs (VCD, logs, reports)
```

## Quick Start

1. Clone this repo and open it in an AI coding assistant that supports skills (e.g., Gemini CLI, Antigravity)
2. Place your Verilog/SystemVerilog DUT in `src/`
3. Ask the assistant to **verify**, **test**, or **simulate** your design
4. The skill activates automatically — it checks your environment, lints the code, generates a testbench, runs simulation, and delivers a verification report

## Examples Included

- **Combinational ALU** (`examples/01_comb_alu.v`) — 4-bit ALU with add, subtract, AND, OR
- **Sequential Counter** (`examples/02_seq_counter.v`) — 8-bit counter with synchronous reset and enable

## What Makes This Different

- **Fully automated** — the agent writes the entire testbench, not just a skeleton
- **Self-correcting** — if syntax issues are found, it offers to fix them and re-lint
- **Complete reports** — every run produces a structured verification report with pass/fail status and coverage details
- **Waveform ready** — VCD files are generated automatically; GTKWave launch is one confirmation away

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
```bash
pip3 install cocotb pyuvm
```

## License

MIT — see [LICENSE](./LICENSE).
