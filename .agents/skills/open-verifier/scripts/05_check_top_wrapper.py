#!/usr/bin/env python3
"""
05_check_top_wrapper.py — Diffs top wrapper port names against interface.yaml.

Usage: python3 05_check_top_wrapper.py <path_to_wrapper.sv>

Reads out/interface.yaml for the ground truth port list.
Parses the wrapper .sv file for port declarations using regex
(no full SV parser required — just extract port names).
Reports:
  - Ports in interface.yaml but missing from wrapper (ERROR)
  - Ports in wrapper but not in interface.yaml (WARNING — may be intentional)
Exit 1 if any ERROR-level mismatches exist.
"""

import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_interface_ports(interface_yaml_path):
    """Load port names from out/interface.yaml."""
    with open(interface_yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if not data or "ports" not in data:
        print("ERROR: interface.yaml is missing or has no 'ports' section.", file=sys.stderr)
        sys.exit(1)

    return {port["name"] for port in data["ports"]}


def extract_wrapper_ports(wrapper_path):
    """Parse a .sv wrapper file for port declarations using regex.
    Extracts port names from input/output/inout declarations and module port lists."""
    with open(wrapper_path, "r", encoding="utf-8") as f:
        content = f.read()

    ports = set()

    # Pattern 1: Match explicit port declarations
    # e.g., input logic [7:0] port_name,
    #        output wire port_name
    #        inout port_name
    port_decl_pattern = re.compile(
        r'(?:input|output|inout)\s+'       # direction keyword
        r'(?:wire|reg|logic)?\s*'           # optional type
        r'(?:signed\s+)?'                   # optional signed
        r'(?:\[[\d:]+\]\s*)?'              # optional bus width [N:M]
        r'(\w+)',                            # port name (captured)
        re.MULTILINE
    )
    for match in port_decl_pattern.finditer(content):
        ports.add(match.group(1))

    # Pattern 2: Match ANSI-style module port declarations
    # e.g., module wrapper (
    #          input logic clk,
    #          output logic [7:0] data
    #        );
    # Already covered by Pattern 1 above

    # Pattern 3: Match ports in a comma-separated port list (non-ANSI style)
    # e.g., module wrapper (clk, rst_n, data_in, data_out);
    module_pattern = re.compile(
        r'module\s+\w+\s*'                  # module keyword + name
        r'(?:#\s*\([^)]*\)\s*)?'            # optional parameter list
        r'\(\s*'                             # opening paren
        r'([^)]+)'                           # port list (captured)
        r'\)',                               # closing paren
        re.DOTALL
    )
    module_match = module_pattern.search(content)
    if module_match:
        port_list_text = module_match.group(1)
        # If it contains direction keywords, it's ANSI style (already handled)
        if not re.search(r'\b(?:input|output|inout)\b', port_list_text):
            # Non-ANSI: just comma-separated names
            for name in re.findall(r'\b(\w+)\b', port_list_text):
                ports.add(name)

    return ports


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 05_check_top_wrapper.py <path_to_wrapper.sv>", file=sys.stderr)
        sys.exit(1)

    wrapper_path = sys.argv[1]

    # Validate wrapper file exists
    if not pathlib.Path(wrapper_path).exists():
        print(f"ERROR: Wrapper file not found: {wrapper_path}", file=sys.stderr)
        sys.exit(1)

    # Resolve interface.yaml path
    script_dir = pathlib.Path(__file__).resolve().parent
    interface_yaml = script_dir / ".." / ".." / ".." / ".." / "out" / "interface.yaml"
    interface_yaml = interface_yaml.resolve()

    if not interface_yaml.exists():
        print(f"ERROR: interface.yaml not found at {interface_yaml}", file=sys.stderr)
        print("Run 02_elaborate.py first to generate interface.yaml.", file=sys.stderr)
        sys.exit(1)

    # Load ground truth ports from interface.yaml
    expected_ports = load_interface_ports(interface_yaml)

    # Extract ports from wrapper file
    wrapper_ports = extract_wrapper_ports(wrapper_path)

    # Compute differences
    missing_from_wrapper = expected_ports - wrapper_ports  # ERROR
    extra_in_wrapper = wrapper_ports - expected_ports       # WARNING

    # Report results
    has_errors = False

    print(f"=== Top Wrapper Port Check ===")
    print(f"Interface (interface.yaml): {len(expected_ports)} ports")
    print(f"Wrapper ({wrapper_path}):   {len(wrapper_ports)} ports")
    print()

    if missing_from_wrapper:
        has_errors = True
        print("ERROR — Ports in interface.yaml but MISSING from wrapper:")
        for port in sorted(missing_from_wrapper):
            print(f"  [ERROR] {port}")
        print()

    if extra_in_wrapper:
        print("WARNING — Ports in wrapper but NOT in interface.yaml (may be intentional):")
        for port in sorted(extra_in_wrapper):
            print(f"  [WARN]  {port}")
        print()

    if not missing_from_wrapper and not extra_in_wrapper:
        print("PASS — All ports match exactly.")

    if has_errors:
        print("\nRESULT: FAIL — Fix the missing ports before proceeding.")
        sys.exit(1)
    else:
        print("\nRESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
