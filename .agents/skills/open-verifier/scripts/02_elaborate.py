#!/usr/bin/env python3
"""
02_elaborate.py — Runs Verilator on dut.f to produce XML AST,
then prunes to top-level ports only → out/interface.yaml

Usage: python3 02_elaborate.py --top <module_name>
"""

import argparse
import hashlib
import json
import os
import pathlib
import datetime
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import yaml


def update_state(step_name, artifact_path=None, status="complete"):
    """Update out/state.json with step completion and artifact hash."""
    script_dir = pathlib.Path(__file__).resolve().parent
    state_path = script_dir / ".." / ".." / ".." / ".." / "out" / "state.json"
    state_path = state_path.resolve()
    state = json.loads(state_path.read_text()) if state_path.exists() else {"schema_version": "1.0", "steps": {}}
    entry = {"status": status, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
    if artifact_path:
        data = pathlib.Path(artifact_path).read_bytes()
        entry["artifact"] = artifact_path
        entry["hash"] = "sha256:" + hashlib.sha256(data).hexdigest()
    state["steps"][step_name] = entry
    state["last_updated"] = entry["timestamp"]
    state_path.write_text(json.dumps(state, indent=2))


# Clock/reset heuristic patterns
CLOCK_PATTERNS = re.compile(r"^(clk|clock|i_clk|i_clock|sys_clk|aclk)$", re.IGNORECASE)
RESET_PATTERNS = re.compile(r"^(rst|reset|rst_n|resetn|i_rst|i_reset|i_rst_n|areset_n|aresetn)$", re.IGNORECASE)


def is_suspected_clock(name):
    """Heuristic: tag ports matching clock-like patterns."""
    return bool(CLOCK_PATTERNS.match(name))


def is_suspected_reset(name):
    """Heuristic: tag ports matching reset-like patterns."""
    return bool(RESET_PATTERNS.match(name))


def find_top_module(root, top_name):
    """Find the top MODULE node in the Verilator XML AST."""
    # Verilator XML structure: <verilator_xml> -> <netlist> -> <module>
    # Search recursively for MODULE or module elements with the matching name
    for elem in root.iter():
        tag = elem.tag.lower() if elem.tag else ""
        if tag in ("module", "mod"):
            name = elem.get("name", "")
            if name == top_name:
                return elem
    # Also try looking for typetable -> module pattern
    for elem in root.iter("module"):
        if elem.get("name") == top_name:
            return elem
    return None


def extract_ports(module_node, typetable):
    """Extract VAR nodes that are direct children with dir=input/output/inout."""
    ports = []
    for child in module_node:
        tag = child.tag.lower() if child.tag else ""
        if tag == "var":
            direction = child.get("dir", "").lower()
            if direction in ("input", "output", "inout"):
                name = child.get("name", "")
                dtype_id = child.get("dtype_id")
                
                # Determine width from typetable lookup
                width = typetable.get(dtype_id, 1)

                ports.append({
                    "name": name,
                    "direction": direction,
                    "width": width,
                    "suspected_clock": is_suspected_clock(name),
                    "suspected_reset": is_suspected_reset(name),
                })
    return ports


def extract_parameters(module_node):
    """Extract PARAM children from the MODULE node."""
    params = {}
    for child in module_node:
        tag = child.tag.lower() if child.tag else ""
        if tag in ("param", "var"):
            # Parameters may appear as var with param=true or as param nodes
            is_param = child.get("param", "").lower() == "true" or tag == "param"
            if is_param:
                name = child.get("name", "")
                value = child.get("value", child.text or "")
                if name:
                    params[name] = value
    return params


def main():
    script_dir = pathlib.Path(__file__).resolve().parent
    default_out = str(script_dir / ".." / ".." / ".." / ".." / "out")

    parser = argparse.ArgumentParser(
        description="Run Verilator elaboration and extract top-level ports to interface.yaml"
    )
    parser.add_argument(
        "--top",
        type=str,
        required=False,
        default=None,
        help="Top-level module name"
    )
    args = parser.parse_args()

    out_dir = pathlib.Path(default_out).resolve()
    dut_f = out_dir / "dut.f"

    # Read top module name — from CLI arg or from top_module.txt (written by 01_gen_filelist.py)
    top_name = args.top
    if not top_name:
        top_module_file = out_dir / "top_module.txt"
        if top_module_file.exists():
            top_name = top_module_file.read_text().strip()
        else:
            print("ERROR: --top <module_name> is required (or run 01_gen_filelist.py with --top-module first)", file=sys.stderr)
            sys.exit(1)

    # Verify dut.f exists
    if not dut_f.exists():
        print(f"ERROR: {dut_f} not found. Run 01_gen_filelist.py first.", file=sys.stderr)
        sys.exit(1)

    # Check verilator is available
    try:
        subprocess.run(["verilator", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("ERROR: verilator not found. Install Verilator >= 4.0.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: verilator version check failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Create verilator build directory
    verilator_build = out_dir / "verilator_build"
    verilator_build.mkdir(parents=True, exist_ok=True)

    # Run verilator to produce XML AST
    cmd = [
        "verilator",
        "-Wno-DEPRECATED",
        "-Wno-fatal",
        "-f", str(dut_f),
        "--xml-only",
        "--top-module", top_name,
        "-Mdir", str(verilator_build),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ERROR: Verilator elaboration failed (exit code {result.returncode})", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        update_state("elaborate", status="failed")
        sys.exit(1)

    # Find the XML output
    xml_file = verilator_build / f"V{top_name}.xml"
    if not xml_file.exists():
        # Try alternative name patterns
        xml_candidates = list(verilator_build.glob("*.xml"))
        if xml_candidates:
            xml_file = xml_candidates[0]
        else:
            print(f"ERROR: No XML file found in {verilator_build}", file=sys.stderr)
            update_state("elaborate", status="failed")
            sys.exit(1)

    # Parse the XML AST
    print(f"Parsing XML AST: {xml_file}")
    tree = ET.parse(str(xml_file))
    root = tree.getroot()

    # Parse typetable to resolve widths
    typetable = {}
    for dtype in root.findall(".//typetable/*"):
        dtype_id = dtype.get("id")
        if dtype_id:
            # For basic types, extract width from left/right or width attributes
            # left=7, right=0 -> width 8
            left = dtype.get("left")
            right = dtype.get("right")
            if left is not None and right is not None:
                typetable[dtype_id] = abs(int(left) - int(right)) + 1
            else:
                width = dtype.get("width")
                typetable[dtype_id] = int(width) if width else 1

    # Find the top module node
    module_node = find_top_module(root, top_name)
    if module_node is None:
        print(f"ERROR: Module '{top_name}' not found in XML AST", file=sys.stderr)
        update_state("elaborate", status="failed")
        sys.exit(1)

    # Extract ports (B3 pruning: only direct children with dir=input/output/inout)
    ports = extract_ports(module_node, typetable)
    if not ports:
        print(f"ERROR: No ports found for module '{top_name}'", file=sys.stderr)
        update_state("elaborate", status="failed")
        sys.exit(1)

    # Extract parameters
    parameters = extract_parameters(module_node)

    # Build interface.yaml structure
    interface = {
        "top_module": top_name,
        "parameters": parameters if parameters else {},
        "ports": ports,
    }

    # Write out/interface.yaml
    interface_yaml_path = out_dir / "interface.yaml"
    with open(interface_yaml_path, "w") as f:
        yaml.dump(interface, f, default_flow_style=False, sort_keys=False)

    # Print summary
    input_count = sum(1 for p in ports if p["direction"] == "input")
    output_count = sum(1 for p in ports if p["direction"] == "output")
    inout_count = sum(1 for p in ports if p["direction"] == "inout")
    clock_count = sum(1 for p in ports if p["suspected_clock"])
    reset_count = sum(1 for p in ports if p["suspected_reset"])

    print(f"\nInterface extraction complete for module '{top_name}':")
    print(f"  Ports: {len(ports)} total ({input_count} in, {output_count} out, {inout_count} inout)")
    print(f"  Parameters: {len(parameters)}")
    print(f"  Suspected clocks: {clock_count}")
    print(f"  Suspected resets: {reset_count}")
    print(f"  Written to: {interface_yaml_path}")

    # Update state.json
    update_state("elaborate", artifact_path=str(interface_yaml_path))


if __name__ == "__main__":
    main()
