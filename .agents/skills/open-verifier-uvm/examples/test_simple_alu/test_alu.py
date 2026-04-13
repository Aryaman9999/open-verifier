"""
==============================================================================
pyUVM Testbench for simple_alu — Teaching Example
==============================================================================

This testbench demonstrates the COMPLETE UVM methodology using pyUVM:

  1. Sequence Item (AluItem)     — Defines the transaction: what data moves
  2. Sequence (AluSequence)      — Generates the stimulus: what test vectors
  3. Driver (AluDriver)          — Drives the DUT pins: applies stimulus
  4. Monitor (AluMonitor)        — Samples DUT outputs: observes results
  5. Scoreboard (AluScoreboard)  — Checks correctness: expected vs actual
  6. Environment (AluEnv)        — Wires everything together
  7. Tests (TestALUNormal, etc.) — Top-level test entry points

HOW TO READ THIS FILE:
  - Start from the bottom (test classes) and work UP to understand the
    hierarchy: Test → Env → Components → Items.
  - Every class has docstrings explaining WHAT it does and WHY.
  - Comments inline explain cocotb-specific patterns (await, signals, etc.).

WHY UVM?
  UVM (Universal Verification Methodology) structures verification into
  reusable components. Instead of one monolithic testbench, you get modular
  pieces that can be swapped out — e.g., change the sequence to test different
  scenarios without touching the driver or scoreboard.

==============================================================================
"""

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import pyuvm
from pyuvm import *
import logging
import random


# =============================================================================
# 1. SEQUENCE ITEM — The "transaction object"
# =============================================================================
# In UVM, a sequence item represents ONE transaction — one set of inputs
# and the expected/actual output. Think of it as a single row in a test vector
# table: "apply these inputs, expect this output."
# =============================================================================

class AluItem(uvm_sequence_item):
    """
    Represents one ALU transaction.

    Fields:
        a       (int): 8-bit operand A  (stimulus)
        b       (int): 8-bit operand B  (stimulus)
        op      (int): 2-bit operation  (stimulus)
        result  (int): 9-bit ALU result (response — filled by monitor)
    """

    def __init__(self, name="AluItem"):
        super().__init__(name)
        self.a = 0
        self.b = 0
        self.op = 0
        self.result = 0

    def __str__(self):
        """Pretty-print for log messages — you'll see this in simulation output."""
        op_names = {0: "ADD", 1: "SUB", 2: "AND", 3: "OR"}
        op_str = op_names.get(self.op, "???")
        return f"AluItem(a=0x{self.a:02x}, b=0x{self.b:02x}, op={op_str}, result=0x{self.result:03x})"


# =============================================================================
# 2. SEQUENCE — The "stimulus generator"
# =============================================================================
# A sequence creates a series of sequence items (transactions) and sends them
# to the driver via the sequencer. In standard UVM this uses `start_item` /
# `finish_item`. In pyUVM, the pattern is the same.
#
# WHY separate from driver? Because you can write MANY sequences (random,
# directed, corner-case) and plug them into the SAME driver. Reusability!
# =============================================================================

class AluSequence(uvm_sequence):
    """
    Generates stimulus for the ALU.

    This sequence creates transactions covering:
      - All four operations with representative values
      - Normal arithmetic values
      - Edge cases are handled by a separate sequence (AluEdgeCaseSequence)
    """

    async def body(self):
        """
        The body() method is called when the sequence is started.
        It creates items, randomizes them, and sends them to the driver.
        """
        # Test all four operations with several random value pairs
        for op in range(4):
            for _ in range(5):
                item = AluItem("stim_item")
                item.a = random.randint(0, 255)
                item.b = random.randint(0, 255)
                item.op = op
                await self.start_item(item)
                await self.finish_item(item)
                self.logger.info(f"Sent: {item}")


class AluEdgeCaseSequence(uvm_sequence):
    """
    Generates edge-case stimulus for the ALU.

    Covers boundary conditions that are easy to get wrong:
      - Zero operands (a=0, b=0)
      - Maximum operands (a=0xFF, b=0xFF)
      - One operand zero, one max
      - Overflow scenarios for ADD
      - Underflow scenarios for SUB
    """

    async def body(self):
        # Define edge-case test vectors: (a, b, op)
        edge_cases = [
            # Zero inputs — all operations
            (0x00, 0x00, 0),  # ADD: 0+0
            (0x00, 0x00, 1),  # SUB: 0-0
            (0x00, 0x00, 2),  # AND: 0&0
            (0x00, 0x00, 3),  # OR:  0|0
            # Max inputs — all operations
            (0xFF, 0xFF, 0),  # ADD: 255+255=510 (carry!)
            (0xFF, 0xFF, 1),  # SUB: 255-255=0
            (0xFF, 0xFF, 2),  # AND: 0xFF
            (0xFF, 0xFF, 3),  # OR:  0xFF
            # Asymmetric edge cases
            (0xFF, 0x00, 0),  # ADD: 255+0
            (0x00, 0xFF, 0),  # ADD: 0+255
            (0x00, 0xFF, 1),  # SUB: 0-255 (underflow/borrow)
            (0x01, 0x01, 1),  # SUB: 1-1=0
            (0x80, 0x80, 0),  # ADD: 128+128=256 (carry)
            (0xAA, 0x55, 2),  # AND: alternating bits → 0x00
            (0xAA, 0x55, 3),  # OR:  alternating bits → 0xFF
        ]

        for a, b, op in edge_cases:
            item = AluItem("edge_item")
            item.a = a
            item.b = b
            item.op = op
            await self.start_item(item)
            await self.finish_item(item)
            self.logger.info(f"Sent edge case: {item}")


# =============================================================================
# 3. DRIVER — Drives the DUT pins
# =============================================================================
# The driver takes transactions from the sequencer and applies them to the
# DUT's input ports using cocotb signal assignments. It's the bridge between
# the abstract transaction world and the physical signal world.
#
# In cocotb, we use `dut.signal_name.value = X` to drive and
# `await RisingEdge(dut.clk)` to synchronize to clock edges.
# =============================================================================

class AluDriver(uvm_driver):
    """
    Drives AluItem transactions onto the DUT's input pins.

    For each transaction received from the sequencer:
      1. Wait for a rising clock edge (synchronize)
      2. Apply a, b, op to the DUT inputs
      3. Wait one more clock edge for the DUT to register the result
    """

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.dut = cocotb.top

    async def run_phase(self):
        await self.get_and_drive()

    async def get_and_drive(self):
        """Main driver loop — pull items from sequencer and apply to DUT."""
        while True:
            item = await self.seq_item_port.get_next_item()
            await RisingEdge(self.dut.clk)

            # Drive the DUT input pins
            self.dut.a.value = item.a
            self.dut.b.value = item.b
            self.dut.op.value = item.op

            # Wait for the result to propagate (registered output = 1 cycle)
            await RisingEdge(self.dut.clk)

            self.seq_item_port.item_done()


# =============================================================================
# 4. MONITOR — Samples DUT outputs
# =============================================================================
# The monitor passively observes the DUT's output signals. It does NOT drive
# anything — it only reads. After sampling, it broadcasts the observed
# transaction to the scoreboard via an analysis port.
#
# WHY separate from driver? The monitor sees what the DUT ACTUALLY does,
# while the driver only knows what it SENT. The scoreboard compares both.
# =============================================================================

class AluMonitor(uvm_monitor):
    """
    Monitors the DUT's output and broadcasts observed transactions.

    On every clock edge, it samples the DUT's input and output ports,
    creates an AluItem with the observed values, and sends it to the
    scoreboard through the analysis port.
    """

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.dut = cocotb.top

    async def run_phase(self):
        """Continuously sample the DUT and broadcast transactions."""
        while True:
            await RisingEdge(self.dut.clk)
            # Small delay to let signals settle after clock edge
            await Timer(1, units="ns")

            item = AluItem("mon_item")
            item.a = int(self.dut.a.value)
            item.b = int(self.dut.b.value)
            item.op = int(self.dut.op.value)
            item.result = int(self.dut.result.value)

            self.ap.write(item)


# =============================================================================
# 5. SCOREBOARD — Checks correctness
# =============================================================================
# The scoreboard receives transactions from the monitor and compares the DUT's
# actual output against a REFERENCE MODEL (a Python function that computes the
# expected result). If there's a mismatch, it logs an error.
#
# WHY a reference model? Instead of hardcoding expected values for every test,
# we write a Python function that mirrors the DUT's logic. This scales to any
# number of random test vectors — the scoreboard checks them all automatically.
# =============================================================================

class AluScoreboard(uvm_scoreboard):
    """
    Compares DUT output to a Python reference model.

    The reference model computes what the ALU SHOULD output for given inputs.
    If the DUT's actual result doesn't match, a FAIL is reported.
    """

    def build_phase(self):
        self.ap = uvm_analysis_export("ap", self)
        self.pass_count = 0
        self.fail_count = 0
        # Skip the first few transactions during reset
        self.skip_count = 2
        self.skipped = 0

    def write(self, item):
        """
        Called by the monitor's analysis port for every observed transaction.
        Compares actual vs expected using the reference model.
        """
        # Skip initial reset transactions where result is expected to be 0
        if self.skipped < self.skip_count:
            self.skipped += 1
            return

        expected = self.reference_model(item.a, item.b, item.op)

        if item.result == expected:
            self.pass_count += 1
            self.logger.info(
                f"MATCH: a=0x{item.a:02x} b=0x{item.b:02x} op={item.op} "
                f"→ result=0x{item.result:03x} (expected=0x{expected:03x})"
            )
        else:
            self.fail_count += 1
            self.logger.error(
                f"MISMATCH: a=0x{item.a:02x} b=0x{item.b:02x} op={item.op} "
                f"→ result=0x{item.result:03x} (expected=0x{expected:03x})"
            )

    @staticmethod
    def reference_model(a, b, op):
        """
        Python reference model mirroring the ALU's Verilog logic.

        This function computes the EXPECTED output for any input combination.
        It must exactly mirror what the DUT does — if this disagrees with the
        DUT, the scoreboard will flag mismatches.

        Args:
            a  (int): 8-bit operand A (0-255)
            b  (int): 8-bit operand B (0-255)
            op (int): 2-bit operation (0=ADD, 1=SUB, 2=AND, 3=OR)

        Returns:
            int: 9-bit expected result (0-511)
        """
        if op == 0:    # ADD
            return (a + b) & 0x1FF       # 9-bit mask for carry
        elif op == 1:  # SUB
            return (a - b) & 0x1FF       # 9-bit mask for borrow
        elif op == 2:  # AND
            return a & b
        elif op == 3:  # OR
            return a | b
        else:
            return 0

    def report_phase(self):
        """Print final scoreboard summary at end of simulation."""
        self.logger.info("=" * 60)
        self.logger.info(f"SCOREBOARD SUMMARY: {self.pass_count} PASSED, {self.fail_count} FAILED")
        if self.fail_count > 0:
            self.logger.error("SCOREBOARD RESULT: FAILED")
        else:
            self.logger.info("SCOREBOARD RESULT: PASSED")
        self.logger.info("=" * 60)


# =============================================================================
# 6. ENVIRONMENT — Wires components together
# =============================================================================
# The environment (uvm_env) is the container that instantiates and connects
# all verification components. Think of it as the "circuit board" that holds
# the driver, monitor, and scoreboard and wires their ports together.
#
# WHY an env? Modularity. You can create different environments for different
# levels of testing (unit, block, system) by composing different components.
# =============================================================================

class AluEnv(uvm_env):
    """
    UVM Environment for the ALU.

    Instantiates the driver, monitor, and scoreboard, then connects
    the monitor's analysis port to the scoreboard's analysis export
    so observed transactions flow automatically to the checker.
    """

    def build_phase(self):
        """Create all sub-components."""
        self.driver = AluDriver("driver", self)
        self.monitor = AluMonitor("monitor", self)
        self.scoreboard = AluScoreboard("scoreboard", self)

    def connect_phase(self):
        """Wire the monitor's output to the scoreboard's input."""
        # This is the key UVM connection: monitor observes → scoreboard checks
        self.monitor.ap.connect(self.scoreboard.ap)


# =============================================================================
# 7. TEST CLASSES — Top-level entry points
# =============================================================================
# Each test class represents a different verification scenario. They all use
# the same environment but run different sequences (stimulus generators).
#
# The @pyuvm.test() decorator registers the class as a cocotb test that pyUVM
# will discover and run. Each test:
#   1. Builds the environment
#   2. Starts clock + reset
#   3. Runs a specific sequence through the driver
#   4. Reports results
# =============================================================================

@pyuvm.test()
class TestALUNormal(uvm_test):
    """
    Standard functional test for the ALU.

    Runs the AluSequence which tests all four operations with random values.
    This verifies that the ALU produces correct results under normal operating
    conditions.
    """

    def build_phase(self):
        self.env = AluEnv("env", self)

    async def run_phase(self):
        self.raise_objection()

        dut = cocotb.top

        # Start the clock — 10ns period (100 MHz)
        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

        # Apply reset for 5 clock cycles
        dut.rst.value = 1
        dut.a.value = 0
        dut.b.value = 0
        dut.op.value = 0
        for _ in range(5):
            await RisingEdge(dut.clk)
        dut.rst.value = 0
        await RisingEdge(dut.clk)

        # Run the normal stimulus sequence
        seq = AluSequence("normal_seq")
        await seq.start(self.env.driver.seq_item_port)

        # Allow a few extra cycles for the pipeline to flush
        for _ in range(5):
            await RisingEdge(dut.clk)

        self.drop_objection()

    def report_phase(self):
        sb = self.env.scoreboard
        if sb.fail_count > 0:
            self.logger.error(f"TestALUNormal FAILED — {sb.fail_count} mismatches detected")
        else:
            self.logger.info(f"TestALUNormal PASSED — {sb.pass_count} checks passed")


@pyuvm.test()
class TestALUEdgeCases(uvm_test):
    """
    Edge-case / boundary test for the ALU.

    Runs the AluEdgeCaseSequence which targets specific boundary conditions:
      - Zero inputs, maximum inputs
      - Carry (ADD overflow), borrow (SUB underflow)
      - Alternating bit patterns for AND/OR
    This verifies the ALU handles extreme values correctly.
    """

    def build_phase(self):
        self.env = AluEnv("env", self)

    async def run_phase(self):
        self.raise_objection()

        dut = cocotb.top

        # Start the clock — 10ns period (100 MHz)
        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

        # Apply reset for 5 clock cycles
        dut.rst.value = 1
        dut.a.value = 0
        dut.b.value = 0
        dut.op.value = 0
        for _ in range(5):
            await RisingEdge(dut.clk)
        dut.rst.value = 0
        await RisingEdge(dut.clk)

        # Run the edge-case stimulus sequence
        seq = AluEdgeCaseSequence("edge_seq")
        await seq.start(self.env.driver.seq_item_port)

        # Allow a few extra cycles for the pipeline to flush
        for _ in range(5):
            await RisingEdge(dut.clk)

        self.drop_objection()

    def report_phase(self):
        sb = self.env.scoreboard
        if sb.fail_count > 0:
            self.logger.error(f"TestALUEdgeCases FAILED — {sb.fail_count} mismatches detected")
        else:
            self.logger.info(f"TestALUEdgeCases PASSED — {sb.pass_count} checks passed")
