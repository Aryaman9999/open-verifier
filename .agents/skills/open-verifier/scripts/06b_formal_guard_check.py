#!/usr/bin/env python3
"""
06_formal_guard_check.py — Scans src/ for simulation-only constructs that
cause Yosys to abort during formal elaboration.

Replaces the fragile `grep -rn '\$display\|\$finish...' src/` command which
breaks due to PowerShell→bash→grep triple-escaping on Windows/WSL.

Usage: python3 06_formal_guard_check.py [--src-dir SRC_DIR]

Returns: exit 0 if all constructs are guarded (or none found)
         exit 1 if unguarded constructs found

Output: structured JSON to stdout
{
  "status": "PASS" | "FAIL",
  "vcd_block_present": true | false,
  "unguarded": [
    {"file": "src/foo.v", "line": 42, "construct": "$display", "content": "..."}
  ],
  "guarded": [
    {"file": "src/foo.v", "line": 10, "construct": "$dumpfile", "guard": "`ifndef FORMAL"}
  ]
}
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path


# Simulation-only constructs that Yosys rejects
SIM_CONSTRUCTS = [
    r'\$display',
    r'\$finish',
    r'\$test\$plusargs',
    r'\$dumpfile',
    r'\$dumpvars',
    r'\$readmemh',
    r'\$readmemb',
    r'\$write',
    r'\$fopen',
    r'\$fclose',
    r'\$fwrite',
]

# Combined pattern
SIM_PATTERN = re.compile('|'.join(SIM_CONSTRUCTS))

# Guard pattern — looks for `ifndef FORMAL or `ifdef SIMULATION etc.
GUARD_PATTERN = re.compile(r'`(?:ifndef\s+FORMAL|ifdef\s+SIMULATION|ifdef\s+COCOTB_SIM)')


def scan_file(filepath):
    """Scan a single Verilog/SystemVerilog file for sim-only constructs.
    Returns (unguarded_list, guarded_list, has_vcd_block).
    """
    unguarded = []
    guarded = []
    has_vcd_block = False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        print(f"[WARN] Cannot read {filepath}: {e}", file=sys.stderr)
        return unguarded, guarded, has_vcd_block

    in_guard = False
    guard_depth = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track `ifndef FORMAL / `ifdef SIMULATION guards
        if GUARD_PATTERN.search(stripped):
            in_guard = True
            guard_depth += 1
        elif stripped.startswith('`endif') and in_guard:
            guard_depth -= 1
            if guard_depth <= 0:
                in_guard = False
                guard_depth = 0
        elif stripped.startswith('`ifdef') or stripped.startswith('`ifndef'):
            if in_guard:
                guard_depth += 1

        # Check for VCD dump block
        if '$dumpfile' in line and '$dumpvars' in ''.join(lines[max(0, i-3):i+3]):
            has_vcd_block = True

        # Find simulation constructs
        for match in SIM_PATTERN.finditer(line):
            construct = match.group(0)
            entry = {
                "file": str(filepath),
                "line": i,
                "construct": construct,
                "content": stripped[:120],
            }
            if in_guard:
                entry["guard"] = "`ifndef FORMAL"
                guarded.append(entry)
            else:
                unguarded.append(entry)

    return unguarded, guarded, has_vcd_block


def main():
    parser = argparse.ArgumentParser(
        description="Check DUT source for unguarded simulation-only constructs"
    )
    parser.add_argument(
        '--src-dir', default='src/',
        help='Directory to scan (default: src/)'
    )
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    if not src_dir.exists():
        result = {
            "status": "FAIL",
            "error": f"Source directory not found: {src_dir}",
            "vcd_block_present": False,
            "unguarded": [],
            "guarded": [],
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    all_unguarded = []
    all_guarded = []
    vcd_found = False

    # Find all .v and .sv files
    for ext in ('*.v', '*.sv'):
        for filepath in src_dir.rglob(ext):
            unguarded, guarded_items, has_vcd = scan_file(filepath)
            all_unguarded.extend(unguarded)
            all_guarded.extend(guarded_items)
            if has_vcd:
                vcd_found = True

    status = "FAIL" if all_unguarded else "PASS"

    result = {
        "status": status,
        "vcd_block_present": vcd_found,
        "unguarded": all_unguarded,
        "guarded": all_guarded,
    }

    print(json.dumps(result, indent=2))

    if all_unguarded:
        print(f"\n[FAIL] Found {len(all_unguarded)} unguarded simulation construct(s):", file=sys.stderr)
        for item in all_unguarded:
            print(f"  {item['file']}:{item['line']} — {item['construct']}", file=sys.stderr)
        print("\nAdd `ifndef FORMAL guards around these lines before proceeding.", file=sys.stderr)
        sys.exit(1)
    else:
        if not vcd_found:
            print("\n[WARN] No VCD dump block ($dumpfile/$dumpvars) found in DUT.", file=sys.stderr)
            print("  Simulation will produce an empty waves.vcd. Tell user to add:", file=sys.stderr)
            print("  `ifndef FORMAL", file=sys.stderr)
            print("  initial begin", file=sys.stderr)
            print("    if ($test$plusargs(\"vcd\")) begin", file=sys.stderr)
            print("      $dumpfile(\"waves.vcd\");", file=sys.stderr)
            print("      $dumpvars(0, <top_module>);", file=sys.stderr)
            print("    end", file=sys.stderr)
            print("  end", file=sys.stderr)
            print("  `endif", file=sys.stderr)
        print(f"\n[PASS] All {len(all_guarded)} simulation construct(s) are properly guarded.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
