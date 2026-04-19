#!/usr/bin/env python3
"""
04_validate_step.py — Per-file deterministic validator.
Checks syntax and required symbols for each generated testbench file.

Usage: python3 04_validate_step.py <filename>
Returns: exit 0 on pass, exit 1 on fail with structured JSON error output.

Output schema:
{
  "file": "<filename>",
  "status": "PASS" | "FAIL",
  "errors": [
    {"category": "TOPOLOGY", "message": "<what is missing>", "symbol": "<symbol>"}
  ]
}
"""

import ast
import json
import os
import sys


def check_python_syntax(filepath):
    """Validate Python syntax using ast.parse. Returns (ok, error_msg)."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Python syntax error at line {e.lineno}: {e.msg}"


def check_symbol(content, symbol):
    """Check if a symbol string exists in the file content."""
    return symbol in content


def read_file(filepath):
    """Read file content as string."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def validate_seq_item(filepath):
    """Validate seq_item.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_object_utils", "@uvm_object_utils decorator missing"),
        ("uvm_sequence_item", "uvm_sequence_item base class missing (snake_case required)"),
        ("def randomize", "randomize() method missing"),
        ("ConstraintFailure", "ConstraintFailure exception class missing"),
        ("COCOTB_RANDOM_SEED", "COCOTB_RANDOM_SEED environment variable usage missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_sequences(filepath):
    """Validate sequences.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_object_utils", "@uvm_object_utils decorator missing"),
        ("uvm_sequence", "uvm_sequence base class missing (snake_case required)"),
        ("await self.start_item", "await self.start_item() call missing"),
        ("await self.finish_item", "await self.finish_item() call missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_driver(filepath):
    """Validate driver.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_component_utils", "@uvm_component_utils decorator missing"),
        ("uvm_driver", "uvm_driver base class missing (snake_case required)"),
        ("async def run_phase", "async def run_phase missing (must be async)"),
        ("get_next_item", "get_next_item() call missing in driver loop"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_monitor(filepath):
    """Validate monitor.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_component_utils", "@uvm_component_utils decorator missing"),
        ("uvm_monitor", "uvm_monitor base class missing (snake_case required)"),
        ("async def run_phase", "async def run_phase missing (must be async)"),
        ("uvm_analysis_port", "uvm_analysis_port declaration missing (snake_case required)"),
        ("CoverPoint", "CoverPoint (cocotb-coverage) usage missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_scoreboard(filepath):
    """Validate scoreboard.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_component_utils", "@uvm_component_utils decorator missing"),
        ("uvm_component", "uvm_component base class missing (Scoreboard must use uvm_component)"),
        ("def write", "write() callback method missing (Required for FIFO-less scoreboard)"),
        ("uvm_analysis_export", "uvm_analysis_export usage missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_env(filepath):
    """Validate env.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@uvm_component_utils", "@uvm_component_utils decorator missing"),
        ("uvm_env", "uvm_env base class missing (snake_case required)"),
        ("connect_phase", "connect_phase method missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_test(filepath):
    """Validate test.py"""
    errors = []
    ok, err = check_python_syntax(filepath)
    if not ok:
        errors.append({"category": "TOPOLOGY", "message": err, "symbol": "syntax"})
        return errors

    content = read_file(filepath)
    checks = [
        ("@cocotb.test", "@cocotb.test decorator missing"),
        ("uvm_test", "uvm_test base class missing (snake_case required)"),
        ("Clock(", "Clock() instantiation missing (from cocotb.clock import Clock)"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_makefile(filepath):
    """Validate Makefile"""
    errors = []
    content = read_file(filepath)
    checks = [
        ("TOPLEVEL", "TOPLEVEL variable missing"),
        ("MODULE", "MODULE variable missing"),
        ("COCOTB_RANDOM_SEED", "COCOTB_RANDOM_SEED variable missing"),
        ("include $(shell cocotb-config", "cocotb Makefile.sim include missing"),
        ("COCOTB_RESOLVE_X", "COCOTB_RESOLVE_X flag missing"),
    ]
    for symbol, message in checks:
        if not check_symbol(content, symbol):
            errors.append({"category": "TOPOLOGY", "message": message, "symbol": symbol})
    return errors


def validate_formal_props(filepath):
    """Validate formal/formal_props.sv"""
    errors = []
    content = read_file(filepath)

    if not check_symbol(content, "assert property"):
        errors.append({"category": "TOPOLOGY", "message": "No 'assert property' statement found", "symbol": "assert property"})

    if not check_symbol(content, "endmodule"):
        errors.append({"category": "TOPOLOGY", "message": "No 'endmodule' keyword found", "symbol": "endmodule"})

    # Accept either wrapper or bind approach and report which was found
    has_wrapper = check_symbol(content, "module dut_with_props")
    has_bind = check_symbol(content, "bind")
    if not has_wrapper and not has_bind:
        errors.append({
            "category": "TOPOLOGY",
            "message": "Neither 'module dut_with_props' (wrapper) nor 'bind' statement found",
            "symbol": "dut_with_props/bind"
        })
    else:
        approach = "wrapper" if has_wrapper else "bind"
        # Not an error, just informational — printed to stdout
        print(f"[INFO] Formal approach detected: {approach}")

    return errors


# Map basenames to their validators
VALIDATORS = {
    "seq_item.py": validate_seq_item,
    "sequences.py": validate_sequences,
    "driver.py": validate_driver,
    "monitor.py": validate_monitor,
    "scoreboard.py": validate_scoreboard,
    "env.py": validate_env,
    "test.py": validate_test,
    "Makefile": validate_makefile,
    "formal_props.sv": validate_formal_props,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 04_validate_step.py <filename>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        result = {
            "file": filepath,
            "status": "FAIL",
            "errors": [{"category": "TOPOLOGY", "message": f"File not found: {filepath}", "symbol": "file"}]
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    # Get the basename for lookup
    basename = os.path.basename(filepath)

    # Find the appropriate validator
    validator = VALIDATORS.get(basename)

    if validator is None:
        # Unknown file — print warning and exit 0 (don't block unknown files)
        result = {
            "file": filepath,
            "status": "PASS",
            "errors": [],
            "warning": f"No validator defined for '{basename}' — passing by default"
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Run validation
    errors = validator(filepath)

    if errors:
        result = {
            "file": filepath,
            "status": "FAIL",
            "errors": errors
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)
    else:
        result = {
            "file": filepath,
            "status": "PASS",
            "errors": []
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)


if __name__ == "__main__":
    main()
