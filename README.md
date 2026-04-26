# 🔬 Open Verifier

### AI-driven black-box UVM verification for Verilog & SystemVerilog

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![pyUVM](https://img.shields.io/badge/pyUVM-2.8.0-blueviolet?style=for-the-badge)
![cocotb](https://img.shields.io/badge/cocotb-1.8%2B-00A86B?style=for-the-badge)
![Icarus Verilog](https://img.shields.io/badge/Icarus-v12-orange?style=for-the-badge)
![SymbiYosys](https://img.shields.io/badge/SymbiYosys-Formal-critical?style=for-the-badge)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

> **You provide the DUT and the spec PDF.
> The agent generates the entire UVM testbench, runs simulation and formal verification, and delivers a coverage report - without ever reading your RTL.**

---

## ⚡ What Makes This Different

| | Traditional AI Verification | **Open Verifier** |
|---|:---:|:---:|
| Reads RTL source | ✅ causes design-intent bias | ❌ **Never** |
| Spec-driven test generation | ❌ | ✅ |
| Full UVM methodology | ❌ | ✅ pyUVM + cocotb |
| Formal verification | ❌ | ✅ SymbiYosys BMC + K-induction |
| Functional coverage | ❌ | ✅ Mapped to spec rules |
| Toggle coverage | ❌ | ✅ VCD post-analysis |
| Single human checkpoint | ❌ | ✅ Binding map review only |
| Open toolchain | Varies | ✅ 100% open source |

---

## 🏗️ Architecture

Two isolated deterministic pipelines gather context before any generation begins - the spec is never mixed with the RTL.

```mermaid
flowchart TD
    subgraph INPUTS["📥 Inputs"]
        PDF["📄 Protocol Spec PDF"]
        DUT["🔌 DUT Source - src/"]
    end

    subgraph PIPELINE_A["🔵 Pipeline A - Spec Context"]
        A1["ToC Extraction"]
        A2["Agentic Chunking"]
        A3["protocol_rules.yaml"]
        A1 --> A2 --> A3
    end

    subgraph PIPELINE_B["🟠 Pipeline B - DUT Interface"]
        B1["Filelist Generation"]
        B2["Verilator Elaboration"]
        B3["AST Pruning - top ports only"]
        B4["interface.yaml"]
        B1 --> B2 --> B3 --> B4
    end

    PDF --> PIPELINE_A
    DUT --> PIPELINE_B

    A3 --> PAUSE
    B4 --> PAUSE

    PAUSE{{"🛑 CRITICAL PAUSE - Human reviews binding_map.yaml"}}

    PAUSE --> SIM_GEN
    PAUSE --> FORMAL_GEN

    subgraph SIM_GEN["🟢 Simulation Branch"]
        S1["seq_item → sequences → driver"]
        S2["monitor → scoreboard → env"]
        S3["test.py + Makefile"]
        S1 --> S2 --> S3
    end

    subgraph FORMAL_GEN["🔴 Formal Branch"]
        F1["formal_props.sv"]
        F2["verify.sby"]
        F1 --> F2
    end

    SIM_GEN --> SIMULATE["▶️ Icarus Verilog simulation"]
    FORMAL_GEN --> FORMAL["▶️ SymbiYosys BMC / K-induction"]
    SIMULATE --> TOGGLE["📊 Toggle Coverage - VCD analysis"]

    SIMULATE --> REPORT
    FORMAL --> REPORT
    TOGGLE --> REPORT

    REPORT["📋 verification_report.md"]

    style PAUSE fill:#e74c3c,color:#fff,stroke:#c0392b
    style REPORT fill:#27ae60,color:#fff,stroke:#1e8449
```

---

## 🔒 The Black-Box Principle

```mermaid
flowchart LR
    subgraph WRONG["❌ Standard AI Approach"]
        direction TB
        RTL_W["RTL Source"] --> AI_W["AI Agent"]
        AI_W --> TB_W["Testbench mirrors RTL bugs"]
    end

    subgraph RIGHT["✅ Open Verifier"]
        direction TB
        SPEC_R["Protocol Spec"] --> AI_R["AI Agent"]
        IFACE_R["Top-level ports only"] --> AI_R
        AI_R --> TB_R["Spec-compliant testbench"]
    end

    style WRONG fill:#fadbd8,stroke:#e74c3c
    style RIGHT fill:#d5f5e3,stroke:#27ae60
```

The agent is explicitly prohibited from reading `src/`. Its only behavioral source of truth is the extracted spec YAML.

---

## 🔄 Run Flow

```mermaid
sequenceDiagram
    participant U as 👤 Engineer
    participant A as 🤖 Agent
    participant S as Icarus Verilog
    participant F as SymbiYosys

    U->>A: Place DUT in src/ and provide spec PDF
    A->>A: Extract protocol_rules.yaml from spec
    A->>A: Generate interface.yaml via Verilator
    A->>U: 🛑 CRITICAL PAUSE - review binding_map.yaml
    U->>A: "binding map approved"
    A->>A: Generate 8 UVM Python files one at a time
    A->>S: make
    S-->>A: Simulation results and VCD
    A->>A: Generate formal_props.sv and verify.sby
    A->>F: sby verify.sby
    F-->>A: PROVED or FAILED with counterexample VCD
    A->>A: Toggle coverage analysis from VCD
    A->>U: 📋 verification_report.md
```

---

## 📊 Coverage - Three Tiers

```mermaid
flowchart LR
    subgraph T1["Tier 1 - Functional"]
        CP["CoverPoint per spec rule<br/>CoverCross for signal intersections<br/>Sampled in monitor after ReadOnly"]
    end

    subgraph T2["Tier 2 - Toggle"]
        TC["VCD post-analysis<br/>Per-port 0→1 and 1→0<br/>transition tracking"]
    end

    subgraph T3["Tier 3 - Formal"]
        FM["SVA assertions<br/>SymbiYosys BMC <br/>Counterexample VCD on failure"]
    end

    T1 --> R["📋 Sections 4 and 5<br/>of report"]
    T2 --> R
    T3 --> R

    style T1 fill:#d6eaf8,stroke:#2e86c1
    style T2 fill:#d5f5e3,stroke:#27ae60
    style T3 fill:#fdebd0,stroke:#e67e22
```

Tier 1 catches protocol compliance failures. Tier 2 catches untested signal paths. Tier 3 proves properties hold for all reachable states within the BMC bound.

---

## ⚙️ The 20-Step FSM

One step per agent turn. Each step is validated and checkpointed to `out/state.json` - interrupted runs resume from the last completed step.

```mermaid
stateDiagram-v2
    [*] --> ENV_CHECK
    ENV_CHECK --> GEN_FILELIST
    GEN_FILELIST --> ELABORATE
    ELABORATE --> EXTRACT_SPEC
    EXTRACT_SPEC --> BINDING_REVIEW

    state BINDING_REVIEW {
        [*] --> AwaitingApproval
        note right of AwaitingApproval: Only mandatory\nhuman checkpoint
    }

    BINDING_REVIEW --> VALIDATE_WRAPPER : binding map approved
    VALIDATE_WRAPPER --> FORMAL_GUARD_CHECK

    state FORMAL_GUARD_CHECK {
        [*] --> Scanning
        note right of Scanning: Checks DUT for unguarded\n$display/$finish/$readmemh
    }

    FORMAL_GUARD_CHECK --> GEN_SEQ_ITEM
    GEN_SEQ_ITEM --> GEN_SEQUENCES
    GEN_SEQUENCES --> GEN_DRIVER
    GEN_DRIVER --> GEN_MONITOR
    GEN_MONITOR --> GEN_SCOREBOARD
    GEN_SCOREBOARD --> GEN_ENV
    GEN_ENV --> GEN_TEST
    GEN_TEST --> GEN_MAKEFILE
    GEN_MAKEFILE --> SIMULATE

    state SIMULATE {
        [*] --> Running
        note right of Running: TOPOLOGY errors\nauto-retry up to 3x
    }

    SIMULATE --> GEN_FORMAL_PROPS
    GEN_FORMAL_PROPS --> GEN_SBY_CONFIG
    GEN_SBY_CONFIG --> RUN_FORMAL
    RUN_FORMAL --> REPORT
    REPORT --> TOGGLE_COVERAGE
    TOGGLE_COVERAGE --> [*]
```

---

## 📦 Repo Structure

```
open-verifier/
├── .agents/skills/open-verifier/
│   ├── SKILL.md                       ← Agent FSM - 20-step pipeline
│   └── scripts/
│       ├── 00_check_env.sh            ← Toolchain validation
│       ├── 01_gen_filelist.py         ← Scans src/, writes dut.f
│       ├── 02_elaborate.py            ← Verilator AST → interface.yaml
│       ├── 03_extract_spec.py         ← PDF chapter extraction
│       ├── 03a_fetch_adjacent_pages.py← Page-boundary context window
│       ├── 04_validate_step.py        ← Per-file symbol validation
│       ├── 05_check_top_wrapper.py    ← Port diff vs interface.yaml
│       ├── 06_view_waves.sh           ← GTKWave launcher
│       ├── 06b_formal_guard_check.py  ← Scans DUT for unguarded sim tasks
│       ├── 07_run_formal.sh           ← SymbiYosys runner (180s timeout)
│       ├── 08_toggle_coverage.py      ← VCD → toggle coverage table
│       ├── 99_reset.sh                ← Clean all generated artifacts
│       └── update_state.py            ← State.json CLI updater
│
├── src/                               ← Your DUT files (Agent doesnt read these files)
│
├── out/                               ← Generated artifacts (gitignored)
│   ├── dut.f
│   ├── interface.yaml
│   ├── protocol_rules.yaml
│   ├── binding_map.yaml
│   └── state.json                     ← FSM checkpoint - enables resume
│
└── uvm_tb/                            ← Agent-generated testbench (gitignored)
    ├── seq_item.py
    ├── sequences.py
    ├── driver.py
    ├── monitor.py
    ├── scoreboard.py
    ├── env.py
    ├── test.py
    ├── Makefile
    ├── formal/
    │   ├── formal_props.sv
    │   └── verify.sby
    └── verification_report.md
```

---

## 🚀 Quick Start

**Prerequisites**

```bash
# Ubuntu / WSL
sudo apt install verilator iverilog gtkwave python3-pip -y
pip install cocotb==1.8.1 pyuvm==2.8.0 cocotb-coverage PyMuPDF pyyaml

# Optional - enables formal verification (Tier 3)
# Use oss-cad-suite tarball — do NOT use apt packages (outdated, causes GLIBC conflicts)
cd ~
wget https://github.com/YosysHQ/oss-cad-suite-build/releases/latest/download/oss-cad-suite-linux-x64.tgz
tar -xzf oss-cad-suite-linux-x64.tgz
source ~/oss-cad-suite/environment   # Add to ~/.bashrc for persistence
```

**Run**

1. Clone this repo and open it in a supported agentic IDE (Cursor, Windsurf, Antigravity)
2. Place your DUT `.v` / `.sv` files in `src/`
3. Have your protocol spec PDF accessible
4. Say: **"verify my DUT against the spec"**

The agent reads `SKILL.md` and runs the full 20-step pipeline automatically, pausing once for your binding map review.

---

## 🛠️ Toolchain

| Layer | Tool | Purpose |
|:---:|:---:|:---|
| Simulation | [Icarus Verilog](http://iverilog.icarus.com) | Compile and simulate DUT |
| Testbench | [cocotb 1.8](https://cocotb.org) | Python coroutine interface to simulator |
| UVM | [pyUVM 2.8.0](https://github.com/pyuvm/pyuvm) | Python UVM component framework |
| Coverage | [cocotb-coverage](https://github.com/mciepluc/cocotb-coverage) | CoverPoint and CoverCross decorators |
| Formal | [SymbiYosys](https://symbiyosys.readthedocs.io) | Bounded model checking (optional) |
| SMT Solver | [Z3](https://github.com/Z3Prover/z3) | Formal backend |
| Interface | [Verilator](https://www.veripool.org/verilator/) | AST extraction only, not simulation |
| Spec parsing | [PyMuPDF](https://pymupdf.readthedocs.io) | PDF ToC and page rendering |
| Waveforms | [GTKWave](https://gtkwave.sourceforge.net) | VCD viewer |

---

## 📜 License

MIT - see [LICENSE](LICENSE)

---

*Open Verifier never reads your source. That's the guarantee.*
