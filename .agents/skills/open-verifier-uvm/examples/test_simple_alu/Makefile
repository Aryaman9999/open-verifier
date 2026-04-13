# ==============================================================================
# cocotb Makefile for simple_alu example
# ==============================================================================
# This Makefile tells cocotb:
#   - Which simulator to use (Icarus Verilog)
#   - Where to find the DUT source files
#   - What the top-level module name is
#   - Which Python module contains the tests
# ==============================================================================

# Simulator selection — Icarus Verilog (open-source)
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Find all Verilog/SystemVerilog source files in the examples directory
# For the example, the DUT is alongside this test directory
VERILOG_SOURCES = $(PWD)/../03_simple_alu.v

# Top-level module name — must match the Verilog module name exactly
TOPLEVEL = simple_alu

# Python module containing the test classes (filename without .py)
MODULE = test_alu

# Enable waveform dumping
WAVES ?= 1

# Resolve X states to zeros (prevents cocotb from crashing on X)
export COCOTB_RESOLVE_X ?= ZEROS

# Include cocotb's build system — this does all the heavy lifting
include $(shell cocotb-config --makefiles)/Makefile.sim
