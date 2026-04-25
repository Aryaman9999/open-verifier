---
name: open-verifier
description: Automated VLSI verification assistant. Runs syntax checks, generates testbenches, executes simulations, and produces verification reports for Verilog/SystemVerilog designs. Trigger whenever a user asks to verify, test, simulate, or debug a Verilog/SystemVerilog DUT.
---

# SKILL: Open Verifier v2 — Implementation Agent

---

## PRIME DIRECTIVE

You are implementing a hardware verification system, one file at a time. You are NOT allowed to:

- Read any file in `src/` for any reason
- Generate more than one deliverable file per turn
- Proceed to the next step without running the validator first
- Invent your own API patterns — use only the exact patterns in this file
- Use any SystemVerilog UVM syntax in Python files

Your only sources of truth are:

1. `out/state.json` — tells you exactly where you are
2. `out/interface.yaml` — tells you DUT port names and module name
3. `out/protocol_rules.yaml` — tells you all rules, coverage directives, formal properties
4. `out/binding_map.yaml` — tells you spec→DUT signal name mappings (re-read before EVERY Python file)
5. This SKILL.md — tells you every pattern to follow

**Before every single action**, read `out/state.json` and identify the first step that is `pending` or `stale`. Work on only that step. Nothing else.

**Windows/WSL environments:** If tools (verilator, iverilog, cocotb-config) are installed in WSL but the project lives on a Windows filesystem, wrap ALL `python3` and script invocations as `bash -l -c "python3 ..."`. The `-l` login flag sources `~/.bashrc` and puts WSL tools on PATH. A non-login shell silently cannot find them, producing "command not found" errors even for correctly installed tools.

---

## STEP 0 — READ STATE FIRST

```bash
bash -l -c "cat out/state.json" 2>/dev/null || echo "state.json missing — run 00_check_env.sh first"
```

Find the first `pending` step. That is your only task for this turn.

---

## STEP 1 — ENV_CHECK

```bash
bash -l -c "bash .agents/skills/open-verifier/scripts/00_check_env.sh"
```

**`00_check_env.sh` must `mkdir -p out/` as its very first action** — before writing `out/.formal_available` or reading `out/state.json`. On a fresh checkout `out/` does not exist; any write to it fails. Directory creation belongs here, not in a later step.

On pass: update `state.json` `env_check` → `complete`. On fail: stop, show missing tool, do not proceed.

---

## STEP 2 — GEN_FILELIST

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/01_gen_filelist.py"
```

Script must recursively find all `.v` and `.sv` files under `src/` and write to `out/dut.f`.

**CRITICAL — path format:** Write **project-root-relative paths** (e.g. `src/dummy_alu.v`), NOT absolute paths. Absolute paths on Windows/WSL contain the user's home directory (`/mnt/c/Users/DELL DN/...`). The space in `DELL DN` causes GNU Make to split the path into two tokens, breaking `VERILOG_SOURCES` with "No rule to make target" errors. Relative paths from the project root never traverse the user directory and are safe.

```python
# Write relative path from project root — forward slashes only
rel = path.relative_to(project_root)
path_str = str(rel).replace("\\", "/")   # e.g. "src/dummy_alu.v"
```

**CRITICAL — `state.json` defensive initialization:** Every script that calls `update_state()` must handle a missing or malformed `state.json`. Before writing, check that the file exists and contains a valid `steps` dict. If not, create the skeleton:

```python
import json, pathlib

STATE_PATH = pathlib.Path("out/state.json")

def load_state():
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text())
            if "steps" in data:
                return data
        except json.JSONDecodeError:
            pass
    # Create skeleton if missing or malformed
    return {"schema_version": "1.0", "steps": {}}

def update_state(step_name, status="complete", **kwargs):
    state = load_state()
    state["steps"][step_name] = {"status": status, **kwargs}
    STATE_PATH.write_text(json.dumps(state, indent=2))
```

Without this, `state["steps"][step_name]` raises `KeyError: 'steps'` on a fresh checkout.

---

## STEP 3 — ELABORATE

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/02_elaborate.py"
```

Runs `verilator -f out/dut.f --xml-only --top-module <top_name> -o out/verilator_ast.xml`, then prunes to top-level ports only → `out/interface.yaml`.

**CRITICAL — bus width extraction:** Do NOT read width from the `VAR` node directly. Multi-bit ports store their type via a `dtype_id` attribute that references the `typetable` section of the XML. The script must:

1. Parse the `<typetable>` section first, building a `dtype_id → width` map
2. For each top-level port `VAR`, resolve `dtype_id` through that map
3. Write the resolved `width` into `interface.yaml`

Skipping this step causes all multi-bit buses to appear as 1-bit wires, silently corrupting all downstream testbench signal widths.

---

## STEP 4 — EXTRACT_SPEC

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/03_extract_spec.py --list-chapters"
```

Two modes:

- `--list-chapters`: prints chapter list from PDF bookmarks
- `--chapter N`: returns text of chapter N

**fetch_adjacent_pages — when a diagram spans a page boundary:**

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/03a_fetch_adjacent_pages.py \
  --pdf spec.pdf --current_page <N> --direction next --count 2 --out_dir out/spec_pages"
```

Read `.txt` and `.png` from `out/spec_pages/`. Clean after each chapter: `rm -rf out/spec_pages/*`.

Process each chapter relevant to protocol rules. Every rule in `out/protocol_rules.yaml` must have: `id`, `description`, `type`, `signals`, `coverage`, `formal_property` (or null). Add `formal_bmc_depth: 50` at the top level.

---

## STEP 5 — CRITICAL PAUSE: BINDING_REVIEW

1. Read `out/interface.yaml` and `out/protocol_rules.yaml`
2. Generate a proposed `out/binding_map.yaml`
3. **HALT.** Output exactly:

```
CRITICAL PAUSE — Human review required.

I have proposed signal bindings in out/binding_map.yaml.
Please review this file and:
  1. Correct any wrong signal mappings
  2. Verify the suspected clock/reset ports
  3. Save the file

When you are satisfied, tell me: "binding map approved"

Do NOT proceed until you receive this confirmation.
```

4. Wait. Do not generate any code. Do not run any scripts. Do not continue.

---

## STEP 6 — VALIDATE_TOP_WRAPPER

Ask the user for the path to their top-level wrapper SV file, then:

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/05_check_top_wrapper.py <path>"
```

Show diff on mismatch. Do not proceed until it passes.

---

## STEPS 7–14 — TESTBENCH GENERATION

**The law:**

1. Re-read `out/binding_map.yaml` before writing any Python file — every time
2. Write one file
3. Run `bash -l -c "python3 .agents/skills/open-verifier/scripts/04_validate_step.py <filename>"`
4. On fail: fix specific error, retry, max 3 attempts, then halt `TOPOLOGY`
5. Update `state.json` → `complete`
6. Stop. Report. Wait for confirmation.

### NAMING CONVENTION

Derive from `protocol_id`: `axi4_lite` → `Axi4Lite`.

| File            | Class name                                             |
| --------------- | ------------------------------------------------------ |
| `seq_item.py`   | `Axi4LiteSeqItem`                                      |
| `sequences.py`  | `Axi4LiteBaseSequence`, `Axi4LiteRule001Sequence`, ... |
| `driver.py`     | `Axi4LiteDriver`                                       |
| `monitor.py`    | `Axi4LiteMonitor`                                      |
| `scoreboard.py` | `Axi4LiteScoreboard`                                   |
| `env.py`        | `Axi4LiteEnv`                                          |
| `test.py`       | `Axi4LiteBaseTest`                                     |

All imports are bare: `from seq_item import Axi4LiteSeqItem`. No `__init__.py`. Not a package.

---

## STEP 7 — GEN_SEQ_ITEM (`uvm_tb/seq_item.py`)

```python
import random
import os
from pyuvm import *

class ConstraintFailure(Exception):
    pass

SEED = int(os.environ.get("COCOTB_RANDOM_SEED", 0))
random.seed(SEED)

@uvm_object_utils
class Axi4LiteSeqItem(uvm_sequence_item):
    def __init__(self, name="Axi4LiteSeqItem"):
        super().__init__(name)
        # One field per signal in binding_map.yaml — default 0
        self.awvalid = 0
        self.awaddr  = 0
        self.awlen   = 0
        self.awburst = 0

    def randomize(self):
        for _ in range(1000):
            self.awlen   = random.randint(0, 15)
            self.awburst = random.choice([0, 1, 2])
            if self.awburst == 2 and self.awlen not in [1, 3, 7, 15]:
                continue
            return True
        raise ConstraintFailure(f"{self.__class__.__name__}: unsatisfiable after 1000 attempts")
```

---

## STEP 8 — GEN_SEQUENCES (`uvm_tb/sequences.py`)

```python
from pyuvm import *
from seq_item import Axi4LiteSeqItem

@uvm_object_utils
class Axi4LiteBaseSequence(uvm_sequence):
    async def body(self):
        for _ in range(self.num_items):
            item = Axi4LiteSeqItem("item")
            await self.start_item(item)
            item.randomize()
            await self.finish_item(item)
```

---

## STEP 9 — GEN_DRIVER (`uvm_tb/driver.py`)

```python
import cocotb
from pyuvm import *
from seq_item import Axi4LiteSeqItem

@uvm_component_utils
class Axi4LiteDriver(uvm_driver):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def build_phase(self):             # NO phase argument in pyUVM 2.8.0
        super().build_phase()
        self.dut = cocotb.top          # Always cocotb.top — never ConfigDB for DUT

    async def run_phase(self):         # NO phase argument; MUST be async
        # NO raise_objection here — driver runs until test drops its objection
        # Objections live ONLY in test.py run_phase — never in driver or monitor

        # Drive ALL inputs to 0 before reset — prevents X-propagation in Icarus
        self.dut.s_axi_awvalid.value = 0
        self.dut.s_axi_wvalid.value  = 0
        # ... every input signal from binding_map.yaml set to 0 here

        # Wait for reset release
        await cocotb.triggers.RisingEdge(self.dut.clk)
        while self.dut.rst_n.value == 0:
            await cocotb.triggers.RisingEdge(self.dut.clk)

        # Main loop — runs indefinitely until test phase ends
        while True:
            req = await self.seq_item_port.get_next_item()
            await self._drive(req)
            self.seq_item_port.item_done()
        # NO drop_objection here

    async def _drive(self, item):
        self.dut.s_axi_awvalid.value = item.awvalid
        self.dut.s_axi_awaddr.value  = item.awaddr
        await cocotb.triggers.RisingEdge(self.dut.clk)
```

---

## STEP 10 — GEN_MONITOR (`uvm_tb/monitor.py`)

```python
import cocotb
from pyuvm import *
from cocotb_coverage.coverage import CoverPoint, CoverCross
from seq_item import Axi4LiteSeqItem

@uvm_component_utils
class Axi4LiteMonitor(uvm_monitor):
    def build_phase(self):             # NO phase argument
        super().build_phase()
        self.ap  = uvm_analysis_port("ap", self)
        self.dut = cocotb.top

    async def run_phase(self):         # NO phase argument; MUST be async
        # NO raise_objection here — monitor runs until test drops its objection
        # Objections live ONLY in test.py run_phase — never in driver or monitor
        while True:
            await cocotb.triggers.RisingEdge(self.dut.clk)
            # REQUIRED: await ReadOnly() after RisingEdge before reading any signal.
            # ReadOnly() waits until all delta cycles in this timestep are resolved.
            # Reading signals at RisingEdge directly causes a race — the DUT's
            # registered outputs may not have updated yet in the same timestep.
            await cocotb.triggers.ReadOnly()
            if self.dut.i_valid.value and self.dut.i_ready.value:
                await self._sample()
            # Do NOT add another RisingEdge here — ReadOnly() already advanced past
            # the race window. An extra RisingEdge skips every other transaction.
        # NO drop_objection here

    async def _sample(self):
        @CoverPoint(
            "axi4lite.awburst",
            xf=lambda x: x,
            bins=list(range(3)),
            bins_labels=["FIXED", "INCR", "WRAP"]
        )
        async def _sample_awburst(awburst):
            pass
        await _sample_awburst(int(self.dut.s_axi_awburst.value))

        item = Axi4LiteSeqItem("monitored")
        item.awvalid = int(self.dut.s_axi_awvalid.value)
        item.awburst = int(self.dut.s_axi_awburst.value)
        item.awlen   = int(self.dut.s_axi_awlen.value)
        self.ap.write(item)
```

**Sampling caution:** Use `ReadOnly()` after `RisingEdge` to avoid the timestep race — see monitor template above. Do NOT add a second `RisingEdge` after sampling; that skips every other transaction.

---

## STEP 11 — GEN_SCOREBOARD (`uvm_tb/scoreboard.py`)

**Pattern: `write()` callback on `uvm_component`. No FIFO, no polling, no `run_phase`.**

**Latency — read the DUT spec first.** Before generating the scoreboard, determine whether the DUT is combinational (result same cycle as inputs) or registered (result arrives N cycles later). Use the appropriate template below. Getting this wrong causes silent false-passes on every transaction after the first.

**Template A — combinational DUT (zero latency):**

```python
from pyuvm import *
from seq_item import Axi4LiteSeqItem

@uvm_component_utils
class Axi4LiteScoreboard(uvm_component):
    def build_phase(self):
        super().build_phase()
        self.analysis_export = uvm_analysis_export("analysis_export", self)
        self.analysis_export.write = self.write   # explicit bind — required in pyUVM 2.x

    def write(self, item):
        self._check(item)

    def _check(self, item):
        # raise AssertionError — UVMFatalError does not exist in pyUVM
        if item.awburst == 2 and item.awlen not in [1, 3, 7, 15]:
            raise AssertionError(
                f"RULE_003 VIOLATED: WRAP burst with illegal AWLEN={item.awlen}"
            )
```

**Template B — registered DUT with N-cycle latency (two analysis ports, one queue):**

The monitor must use two separate analysis ports — one that fires when inputs are captured, one when outputs are captured. The scoreboard queues the inputs and matches them against the outputs when they arrive.

```python
from pyuvm import *
from seq_item import Axi4LiteSeqItem
from collections import deque

@uvm_component_utils
class Axi4LiteScoreboard(uvm_component):
    def build_phase(self):
        super().build_phase()
        # Two exports — connect to monitor's input_ap and output_ap respectively
        self.input_export  = uvm_analysis_export("input_export", self)
        self.output_export = uvm_analysis_export("output_export", self)
        self.input_export.write  = self.write_input   # explicit bind
        self.output_export.write = self.write_output  # explicit bind
        self.pending = deque()

    def write_input(self, item):
        # Fired by monitor when input handshake is observed
        self.pending.append(item)

    def write_output(self, item):
        # Fired by monitor when output is valid — compare against oldest pending input
        if not self.pending:
            raise AssertionError("Output received with no pending input in queue")
        expected = self.pending.popleft()
        self._check(expected, item)

    def _check(self, inp, out):
        # Compare inp fields against out fields per protocol_rules.yaml
        pass
```

When using Template B, `env.py` must connect both ports:

```python
def connect_phase(self):
    self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
    self.monitor.input_ap.connect(self.scoreboard.input_export)
    self.monitor.output_ap.connect(self.scoreboard.output_export)
```

And the monitor must declare both ports in `build_phase` and write to each at the appropriate cycle.

---

## STEP 12 — GEN_ENV (`uvm_tb/env.py`)

```python
from pyuvm import *
from driver import Axi4LiteDriver
from monitor import Axi4LiteMonitor
from scoreboard import Axi4LiteScoreboard

@uvm_component_utils
class Axi4LiteEnv(uvm_env):
    def build_phase(self):             # NO phase argument
        super().build_phase()
        self.driver     = Axi4LiteDriver.create("driver", self)
        self.monitor    = Axi4LiteMonitor.create("monitor", self)
        self.scoreboard = Axi4LiteScoreboard.create("scoreboard", self)
        self.sequencer  = uvm_sequencer.create("sequencer", self)

    def connect_phase(self):           # NO phase argument
        self.driver.seq_item_port.connect(self.sequencer.seq_item_export)
        self.monitor.ap.connect(self.scoreboard.analysis_export)
```

---

## STEP 13 — GEN_TEST (`uvm_tb/test.py`)

```python
import cocotb
from cocotb.clock import Clock
from pyuvm import *
from env import Axi4LiteEnv
from sequences import Axi4LiteBaseSequence

@cocotb.test(timeout_time=500, timeout_unit="us")
async def run_test(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # VCD dump — do NOT rely on +vcd_file plusarg alone.
    # Icarus requires $dumpfile/$dumpvars in the DUT, or use cocotb's built-in:
    # cocotb.simulator.set_command_line_args("-lxt2") is Icarus-only alternative.
    # Simplest cross-platform approach: use COCOTB_WAVE_FILE env var or check
    # that DUT has an initial dump block. Warn the user if neither is present.

    # Do NOT use ConfigDB for DUT handle in pyUVM 2.x
    # Components access DUT via cocotb.top directly

    dut.rst_n.value = 0
    for _ in range(5):
        await cocotb.triggers.RisingEdge(dut.clk)
    dut.rst_n.value = 1

    await uvm_root().run_test("Axi4LiteBaseTest")

@uvm_component_utils
class Axi4LiteBaseTest(uvm_test):
    def build_phase(self):             # NO phase argument in pyUVM 2.8.0
        super().build_phase()
        self.env = Axi4LiteEnv.create("env", self)
        # uvm_root().set_timeout() does NOT exist — timeout via @cocotb.test above

    async def run_phase(self):         # NO phase argument; MUST be async
        self.raise_objection()         # self.raise_objection(), not phase.raise_objection
        seq = Axi4LiteBaseSequence("base_seq")
        seq.num_items = 100
        await seq.start(self.env.sequencer)
        self.drop_objection()          # self.drop_objection(), not phase.drop_objection
```

---

## STEP 14 — GEN_MAKEFILE (`uvm_tb/Makefile`)

```makefile
TOPLEVEL      = dummy_alu        # must exactly match top_module in out/interface.yaml
TOPLEVEL_LANG = verilog
SIM           = icarus
MODULE        = test             # basename of test.py only — no path, no .py

COCOTB_RANDOM_SEED ?= $(shell python3 -c "import time; print(int(time.time()))")
export COCOTB_RANDOM_SEED
$(info [open-verifier] Seed: $(COCOTB_RANDOM_SEED))

# dut.f contains project-root-relative paths (e.g. src/dummy_alu.v)
# Prepend ../ to make them relative to uvm_tb/ where make runs.
# Do NOT use absolute paths — spaces in the user's home directory break GNU Make.
VERILOG_SOURCES := $(addprefix ../, $(shell grep -v '^\s*$$' ../out/dut.f | grep -v '^\s*\#'))

# Parameter injection — one line per entry in interface.yaml parameters
# COMPILE_ARGS += -P$(TOPLEVEL).DATA_WIDTH=32

COMPILE_ARGS += -DCOCOTB_RESOLVE_X=ZEROS

# VCD: +vcd_file is a hint to cocotb only. Icarus will NOT generate a VCD unless
# the DUT has $dumpfile/$dumpvars in an initial block.
# DO NOT add SIM_ARGS += -lxt2 — it creates a spurious empty file named 'xt2' in uvm_tb/.
PLUSARGS     += +vcd_file=../out/waves.vcd

include $(shell cocotb-config --makefiles)/Makefile.sim
```

After writing: run `bash -l -c "cd uvm_tb && make --dry-run"` to verify before marking complete.
The `-l` (login shell) flag is required — cocotb-config is not on PATH in non-login bash.

---

## STEP 15 — SIMULATE

```bash
bash -l -c "cd uvm_tb && make"
```

**CRITICAL — always use `bash -l -c` (login shell).** Plain `bash -c` does not source `~/.bashrc` or `~/.profile`, so Python-installed tools like `cocotb-config` and `iverilog` are not on PATH. The make will fail with "cocotb-config: No such file or directory" even though the tools are installed.

Classify every error. Do NOT fix `ELABORATION`. DO retry `TOPOLOGY` (max 3, regenerate failing file only).

---

## STEP 16 — GEN_FORMAL_PROPS (`uvm_tb/formal/formal_props.sv`)

```bash
cat out/.formal_available
```

If `false`: skip to STEP 19, mark formal steps `skipped`.

**REQUIRED pre-check before generating.** Grep the DUT for simulation-only system tasks that cause Yosys to fatal:

```bash
bash -l -c "grep -rn '\\\$display\|\\\$finish\|\\\$test\\\$plusargs\|\\\$dumpfile\|\\\$dumpvars' src/"
```

If any matches are found WITHOUT a `` `ifndef FORMAL `` guard on the preceding line, tell the user to add it:

```verilog
`ifndef FORMAL
initial begin
  if ($test$plusargs("vcd")) begin
    $dumpfile("waves.vcd");
    $dumpvars(0, top_module);
  end
end
`endif
```

Do NOT generate `formal_props.sv` until the user confirms guards are in place.

**SVA syntax — IMMEDIATE assertions only. NO `property`/`endproperty`.**

Open-source Yosys does NOT support concurrent `property`/`endproperty` syntax — that requires the commercial Verific frontend. Using it produces `ERROR: syntax error, unexpected TOK_PROPERTY`. Use immediate assertions inside `always @(posedge clk)` blocks instead. Computationally equivalent for BMC.

```systemverilog
// uvm_tb/formal/formal_props.sv
// `define FORMAL activates `ifndef FORMAL guards in the DUT
`define FORMAL

module axi_formal_props (
  input logic clk,
  input logic rst_n,
  // One input per signal referenced in any rule — DUT port names from binding_map.yaml
  input logic        s_axi_awvalid,
  input logic        s_axi_awready,
  input logic [1:0]  s_axi_awburst,
  input logic [3:0]  s_axi_awlen
);
  // RULE_001: AWVALID must not deassert before AWREADY
  always @(posedge clk) begin
    if (rst_n) begin
      if ($rose(s_axi_awvalid)) begin
        assert (s_axi_awvalid)
          else $error("RULE_001 VIOLATED: AWVALID deasserted before AWREADY");
      end
    end
  end

  // RULE_003: WRAP burst requires AWLEN in {1, 3, 7, 15}
  always @(posedge clk) begin
    if (rst_n) begin
      if (s_axi_awburst == 2'b10) begin
        assert (s_axi_awlen inside {4'd1, 4'd3, 4'd7, 4'd15})
          else $error("RULE_003 VIOLATED: WRAP burst with illegal AWLEN=%0d", s_axi_awlen);
      end
    end
  end

endmodule

// uvm_tb/formal/dut_with_props.sv
`define FORMAL
module dut_with_props (/* copy exact port list from interface.yaml */);
  axi_slave dut (.*);
  axi_formal_props props (
    .clk(clk), .rst_n(rst_n),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_awburst(s_axi_awburst),
    .s_axi_awlen(s_axi_awlen)
  );
endmodule
```

**FORBIDDEN** (Yosys parse errors): `property`, `endproperty`, `sequence`, `endsequence`, `throughout`, `within`, `intersect`, `first_match`, `expect`, `|->`, `|=>` in concurrent context.

**ALLOWED** in immediate assertions: `assert(...)`, `$rose`, `$fell`, `$stable`, `$past`, `inside {}`.

---

## STEP 17 — GEN_SBY_CONFIG (`uvm_tb/formal/verify.sby`)

```
[options]
mode bmc
depth 50

[engines]
smtbmc z3

[script]
read -sv dut_with_props.sv
read -sv formal_props.sv
read -sv -f ../../../out/dut.f
prep -top dut_with_props

[files]
dut_with_props.sv
formal_props.sv
```

---

## STEP 18 — RUN_FORMAL

```bash
bash -l -c "source ~/oss-cad-suite/environment && bash .agents/skills/open-verifier/scripts/07_run_formal.sh"
```

**oss-cad-suite must be sourced via its own `environment` script** — do NOT manually add `bin/` to PATH. The suite bundles its own C libraries; sourcing `environment` sets `LD_LIBRARY_PATH` correctly to avoid GLIBC conflicts. If the suite is not in `~/oss-cad-suite`, ask the user for its location before proceeding.

If `sby` is not found after sourcing: report that the user must install oss-cad-suite into WSL home (`~/`) and extract using `tar -xzf oss-cad-suite*.tgz -C ~/` — never install on `/mnt/c/`.

Yosys parse failure on DUT → `ELABORATION` error, `source: formal`. Check whether the DUT has unguarded `$display`/`$test$plusargs` — these must be wrapped in `` `ifndef FORMAL `` (see STEP 16 pre-check). Suggest `sv2v` for complex SV syntax. Do not touch DUT source.

---

## STEP 19 — REPORT

Write `uvm_tb/verification_report.md`:

1. Simulation Findings
2. Formal Results (or SKIPPED)
3. Infrastructure Failures
4. Coverage Summary (functional — from cocotb-coverage JSON output)

Section 5 (Toggle Coverage) is appended by STEP 20 below.

---

## STEP 20 — TOGGLE_COVERAGE

```bash
bash -l -c "python3 .agents/skills/open-verifier/scripts/08_toggle_coverage.py"
```

Reads `out/waves.vcd` and `out/interface.yaml`. Appends **Section 5 — Toggle Coverage** to `uvm_tb/verification_report.md`.

If `out/waves.vcd` is missing or zero bytes: append a note stating the DUT needs a `$dumpfile`/`$dumpvars` initial block. Do not fail the pipeline — mark step `complete` with a `SKIPPED` status.

The appended section format:

```markdown
## Section 5 — Toggle Coverage

| Port          | Direction | Width | 0→1 | 1→0 | Status  |
| ------------- | --------- | ----- | --- | --- | ------- |
| clk           | input     | 1     | ✓   | ✓   | FULL    |
| rst_n         | input     | 1     | ✓   | ✓   | FULL    |
| s_axi_awvalid | input     | 1     | ✓   | ✓   | FULL    |
| s_axi_awready | output    | 1     | ✓   | ✗   | PARTIAL |
| s_axi_awdata  | input     | 32    | ✓   | ✓   | FULL    |

**Untoggled ports:** s_axi_awready (missing 1→0)
**Toggle coverage:** 9/10 transitions (90%)
```

Ports with status `NONE` (neither transition seen) are highest priority for `--mode add-sequence`.

---

## ERROR TAXONOMY

| Category            | `source`      | Recoverable | Action                                    |
| ------------------- | ------------- | ----------- | ----------------------------------------- |
| `ELABORATION`       | sim or formal | NO          | Report, stop                              |
| `TOPOLOGY`          | sim           | YES ×3      | Fix symbol, regenerate file               |
| `ASSERTION_FAILURE` | sim or formal | NO          | Finding — record, continue                |
| `TIMEOUT`           | sim           | YES ×3      | Check `drop_objection()`, regen `test.py` |
| `COVERAGE_MISS`     | sim           | NO          | Record, suggest `--mode add-sequence`     |

---

## ABSOLUTE RULES

1. **NEVER read `src/`**
2. **NEVER generate more than one file per turn**
3. **NEVER skip the validator**
4. **NEVER use `uvm_config_db`**
5. **NEVER use decorator as function call** — always `@uvm_component_utils`
6. **NEVER write synchronous `run_phase`** — always `async def run_phase(self)`
7. **NEVER include `phase` argument** in `build_phase`, `connect_phase`, or `run_phase` — pyUVM 2.8.0 does not pass it; including it raises TypeError
8. **NEVER use `phase.raise_objection()` or `phase.drop_objection()`** — always `self.raise_objection()` and `self.drop_objection()`
9. **NEVER use `throughout`, `within`, `intersect`** in SVA
10. **NEVER use `bind`** in formal — use wrapper module
11. **NEVER use package-prefixed imports** — bare `from X import` only
12. **NEVER proceed past CRITICAL PAUSE** without "binding map approved"
13. **NEVER use CamelCase pyUVM base class names** — see reference table
14. **NEVER use `uvm_tlm_analysis_fifo.get()` or `.try_get()`** — use `write()` callback
15. **NEVER pass DUT via ConfigDB** — always `self.dut = cocotb.top`
16. **NEVER call `uvm_root().set_timeout()`** — use `@cocotb.test(timeout_time=N, timeout_unit="us")`
17. **NEVER write backslash paths in `dut.f`** — always forward slashes
18. **NEVER put `raise_objection` or `drop_objection` in driver or monitor** — objections belong ONLY in `test.py` `run_phase`. Driver/monitor in the `while True` loop have no objection management. Violating this causes a three-way deadlock at 40ns with no error output.
19. **NEVER use `property`/`endproperty` in `formal_props.sv`** — open-source Yosys rejects concurrent SVA syntax with `ERROR: syntax error, unexpected TOK_PROPERTY`. Always use immediate assertions inside `always @(posedge clk)` blocks.
20. **NEVER run oss-cad-suite tools without sourcing its environment script** — always `source ~/oss-cad-suite/environment` before calling `sby` or `yosys`. Manual PATH injection causes GLIBC `undefined symbol` errors. The suite must also live in WSL home (`~/`), never on `/mnt/c/`.

---

## PYUVM 2.8.0 REFERENCE

### Phase method signatures — NO `phase` argument

```python
def build_phase(self):      # correct
def build_phase(self, phase):  # WRONG — TypeError in pyUVM 2.8.0

def connect_phase(self):    # correct
async def run_phase(self):  # correct — also must be async
```

### Objections — on `self`, not on `phase`

```python
self.raise_objection()      # correct
self.drop_objection()       # correct
phase.raise_objection(self) # WRONG — phase is not in scope
phase.drop_objection(self)  # WRONG
```

### Base classes — snake_case only

| Role            | Correct               | Wrong                              |
| --------------- | --------------------- | ---------------------------------- |
| Sequence item   | `uvm_sequence_item`   | `UVMSequenceItem`                  |
| Sequence        | `uvm_sequence`        | `UVMSequence`                      |
| Driver          | `uvm_driver`          | `UVMDriver`                        |
| Monitor         | `uvm_monitor`         | `UVMMonitor`                       |
| Scoreboard      | `uvm_component`       | `uvm_scoreboard` / `UVMScoreboard` |
| Environment     | `uvm_env`             | `UVMEnv`                           |
| Test            | `uvm_test`            | `UVMTest`                          |
| Sequencer       | `uvm_sequencer`       | `UVMSequencer`                     |
| Analysis port   | `uvm_analysis_port`   | `UVMAnalysisPort`                  |
| Analysis export | `uvm_analysis_export` | `UVMAnalysisExport`                |

### Methods

| Task                   | Correct                                                    | Wrong                                         |
| ---------------------- | ---------------------------------------------------------- | --------------------------------------------- |
| Register test          | `@uvm_component_utils`                                     | `@uvm_test_utils` — does not exist            |
| Get DUT                | `self.dut = cocotb.top`                                    | `ConfigDB().get(...)` — broken in 2.x         |
| Bind scoreboard export | `self.analysis_export.write = self.write` in `build_phase` | relying on autodiscovery                      |
| Scoreboard receive     | `def write(self, item):`                                   | `self.mon_fifo.get()` — does not exist        |
| Fatal error            | `raise AssertionError("msg")`                              | `raise UVMFatalError("msg")` — does not exist |
| Timeout                | `@cocotb.test(timeout_time=N, timeout_unit="us")`          | `uvm_root().set_timeout()` — does not exist   |
| Create component       | `MyComp.create("name", parent)`                            | `MyComp("name", parent)`                      |
| Get seq item           | `await self.seq_item_port.get_next_item()`                 | without `await`                               |
| Start sequence         | `await seq.start(sequencer)`                               | without `await`                               |
| Send seq item          | `await self.start_item(i)` / `await self.finish_item(i)`   | `uvm_do(item)`                                |

---

## DESIGN CAUTIONS — READ BEFORE GENERATING ANY TESTBENCH FILE

These are failure patterns confirmed during stress testing. Ignoring them causes re-spins.

**C1 — Monitor must use `ReadOnly()` after `RisingEdge` before reading signals.** Reading DUT signal values immediately at `RisingEdge(clk)` creates a timestep race — the simulator and cocotb are in the same delta cycle, so registered outputs may not have updated yet. Always:

```python
await cocotb.triggers.RisingEdge(self.dut.clk)
await cocotb.triggers.ReadOnly()   # wait for all deltas to resolve
# NOW safe to read signal values
```

Do NOT add a second `RisingEdge` after `ReadOnly()` — that skips every other transaction.

**C2 — Latency decoupling: determine DUT type before generating scoreboard.** Check `interface.yaml` and the spec for output latency. If the DUT is registered (result appears N cycles after inputs), use Template B (two analysis ports + deque). If purely combinational, use Template A (single port). The agent must ask or infer this from the spec before writing `scoreboard.py`. Getting it wrong causes silent false-passes.

**C3 — Explicit analysis export binding.** Always `self.analysis_export.write = self.write` in `build_phase`. Some pyUVM 2.x builds don't autodiscover the parent's `write()`.

**C4 — VCD dump requires `$dumpfile`/`$dumpvars` in DUT.** `+vcd_file` is a cocotb hint only. Do NOT add `SIM_ARGS += -lxt2` — this creates a spurious empty file named `xt2` in `uvm_tb/`. Verify the DUT has an initial dump block before trusting waveform output.

**C5 — Bus width from typetable, not VAR node.** Multi-bit port widths are in the Verilator XML `typetable`. `02_elaborate.py` must resolve `dtype_id` through the typetable. A width-1 fallback silently corrupts all signal driving.

**C6 — Relative paths in `dut.f`, NOT absolute.** Absolute paths on Windows/WSL traverse the user's home directory. If that directory contains a space (`DELL DN`), GNU Make splits the path into two tokens at the space and reports "No rule to make target". Write project-root-relative paths (`src/dummy_alu.v`) and use `$(addprefix ../, ...)` in the Makefile. The `../` hop never crosses the user directory.

**C7 — Always `bash -l -c` for all tool invocations.** Every `python3`, `verilator`, `iverilog`, and `cocotb-config` call must go through a login shell on Windows/WSL. Plain `bash -c` or direct execution from Windows terminal cannot see WSL-installed binaries.

**C8 — `00_check_env.sh` must create `out/` before anything else.** The env check writes `out/.formal_available`. On a fresh checkout `out/` doesn't exist. The very first line of the script must be `mkdir -p out/`.

**C9 — VCD requires `$dumpfile`/`$dumpvars` in the DUT source.** The `+vcd_file` plusarg is a cocotb hint only. Icarus ignores it without an explicit dump block. Check whether the user's DUT has:

```verilog
initial begin
  if ($test$plusargs("vcd")) begin
    $dumpfile("waves.vcd");
    $dumpvars(0, <top_module>);
  end
end
```

If not, tell the user to add it before running simulation. Do NOT add it yourself — `src/` is read-only to the agent. Do NOT add `SIM_ARGS += -lxt2` to the Makefile — it creates a spurious empty file named `xt2` in `uvm_tb/`.

**C10 — Objections ONLY in test.py. Driver and monitor have none.** The driver holds an objection then enters `while True` waiting for seq items. The sequencer waits for a driver request. The test waits for the sequence to start. Three-way deadlock — simulation hangs silently at ~40ns, no error output. Resolution: only `test.py` `run_phase` calls `self.raise_objection()` at the start and `self.drop_objection()` after `await seq.start()`. Driver and monitor have no objection calls anywhere.

**C11 — Unguarded simulation system tasks cause Yosys fatal errors.** `$dumpfile`, `$dumpvars`, `$display`, `$finish`, and `$test$plusargs` are simulation-only constructs. Yosys reports `ERROR: Found simulation-only construct` and aborts. All of these must be inside `` `ifndef FORMAL `` blocks in the DUT source. Run the STEP 16 grep pre-check before generating any formal file. Both `formal_props.sv` and `dut_with_props.sv` must have `` `define FORMAL `` at the top so these guards activate during formal elaboration.

**C12 — oss-cad-suite in WSL home, sourced via its own script.** Installing on `/mnt/c/` causes GLIBC `undefined symbol: __tunable_is_initialized` — the suite's bundled libraries conflict with the WSL host glibc. Moving via `mv` across the `/mnt/c/` boundary is a slow cross-filesystem copy that looks frozen and corrupts the installation if cancelled. Correct extraction: `tar -xzf oss-cad-suite*.tgz -C ~/` directly into WSL home. Correct activation: `source ~/oss-cad-suite/environment` — this sets `LD_LIBRARY_PATH` properly. Do NOT manually add `bin/` to PATH.
