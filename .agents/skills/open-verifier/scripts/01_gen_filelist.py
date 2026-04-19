#!/usr/bin/env python3
"""
01_gen_filelist.py — Scans src/ recursively, writes absolute paths of all
.v and .sv files to out/dut.f, one per line.

Usage: python3 01_gen_filelist.py [--src <path>] [--top-module <name>]
Defaults: src=../../src  out=../../out/dut.f (relative to this script)
"""

import argparse
import hashlib
import json
import os
import pathlib
import datetime
import sys


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


def main():
    # Resolve script directory for default paths
    script_dir = pathlib.Path(__file__).resolve().parent
    default_src = str(script_dir / ".." / ".." / ".." / ".." / "src")
    default_out = str(script_dir / ".." / ".." / ".." / ".." / "out")

    parser = argparse.ArgumentParser(
        description="Scan src/ for Verilog/SystemVerilog files and generate dut.f filelist."
    )
    parser.add_argument(
        "--src",
        type=str,
        default=default_src,
        help="Path to the source directory (default: ../../src relative to script)"
    )
    parser.add_argument(
        "--top-module",
        type=str,
        default=None,
        help="Top-level module name (stored for use by 02_elaborate.py)"
    )
    args = parser.parse_args()

    src_path = pathlib.Path(args.src).resolve()
    out_dir = pathlib.Path(default_out).resolve()

    # Validate src/ exists and is a directory
    if not src_path.exists():
        print(f"ERROR: Source directory does not exist: {src_path}", file=sys.stderr)
        sys.exit(1)
    if not src_path.is_dir():
        print(f"ERROR: Source path is not a directory: {src_path}", file=sys.stderr)
        sys.exit(1)

    # mkdir -p the out/ directory
    out_dir.mkdir(parents=True, exist_ok=True)

    # Recursively find all .v and .sv files under src/
    source_files = sorted(
        [f.resolve() for f in src_path.rglob("*") if f.suffix in (".v", ".sv") and f.is_file()]
    )

    # Exit with error if no source files found
    if not source_files:
        print(f"ERROR: No .v or .sv files found under {src_path}", file=sys.stderr)
        sys.exit(1)

    # Write absolute paths to out/dut.f
    dut_f_path = out_dir / "dut.f"
    with open(dut_f_path, "w") as f:
        for src_file in source_files:
            rel_path = os.path.relpath(src_file, out_dir.parent).replace("\\", "/")
            f.write(str(rel_path) + "\n")

    # If top-module is specified, store it in out/ for 02_elaborate.py
    if args.top_module:
        top_module_path = out_dir / "top_module.txt"
        top_module_path.write_text(args.top_module)

    # Print summary
    print(f"Found {len(source_files)} source files. Written to {dut_f_path}")
    for sf in source_files:
        print(f"  {sf}")

    # Update state.json
    update_state("gen_filelist", artifact_path=str(dut_f_path))


if __name__ == "__main__":
    main()
