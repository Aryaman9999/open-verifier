#!/usr/bin/env python3
"""
08_toggle_coverage.py — Toggle Coverage Post-Processor
Open Verifier v2

Reads:
  out/waves.vcd         — VCD waveform from simulation
  out/interface.yaml    — Top-level port list (name, direction, width)

Appends:
  uvm_tb/verification_report.md — Section 5: Toggle Coverage table

Exit codes:
  0 — ran successfully (even if coverage is partial)
  1 — fatal error (bad interface.yaml, unreadable report file)
"""

import pathlib
import sys
import re
import yaml

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR    = pathlib.Path(__file__).parent
PROJECT_ROOT  = SCRIPT_DIR.parents[3]          # .agents/skills/open-verifier/scripts → root
OUT_DIR       = PROJECT_ROOT / "out"
VCD_PATH      = OUT_DIR / "waves.vcd"
IFACE_PATH    = OUT_DIR / "interface.yaml"
REPORT_PATH   = PROJECT_ROOT / "uvm_tb" / "verification_report.md"


# ── VCD parser ─────────────────────────────────────────────────────────────

def parse_vcd(vcd_path: pathlib.Path) -> dict[str, set]:
    """
    Minimal VCD parser. Returns a dict mapping signal name → set of observed
    transition types: {"0→1", "1→0"}.

    Handles only scalar (1-bit) signals for toggle purposes. Multi-bit buses
    are tracked for any-bit toggle (0→non-zero and non-zero→0).

    Does not require an external library — pure stdlib.
    """
    transitions: dict[str, set] = {}   # signal_name → {"0→1", "1→0"}
    id_to_name:  dict[str, str] = {}   # VCD identifier code → signal name
    current_values: dict[str, str] = {}  # identifier → last value string

    if not vcd_path.exists() or vcd_path.stat().st_size == 0:
        return {}

    with vcd_path.open("r", errors="replace") as f:
        in_dumpvars = False
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            # ── variable declarations ──────────────────────────────────────
            # $var wire 1 ! clk $end
            # $var wire 8 " s_axi_awdata [7:0] $end
            if line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 5:
                    id_code   = parts[3]
                    sig_name  = parts[4]          # bare name, no bit range
                    id_to_name[id_code] = sig_name
                    transitions[sig_name]    = set()
                    current_values[id_code]  = "x"
                continue

            # ── initial values block ───────────────────────────────────────
            if line.startswith("$dumpvars"):
                in_dumpvars = True
                continue
            if line.startswith("$end") and in_dumpvars:
                in_dumpvars = False
                continue

            # ── value changes ──────────────────────────────────────────────
            # Scalar:  0! or 1" or x#
            # Vector:  b00101010 $  (followed by identifier on same or next token)
            if line.startswith("b") or line.startswith("B"):
                # vector change: b<value> <id>
                parts = line.split()
                if len(parts) >= 2:
                    vec_val = parts[0][1:]         # strip leading 'b'
                    id_code = parts[1]
                    if id_code in id_to_name:
                        name    = id_to_name[id_code]
                        old_val = current_values.get(id_code, "x")
                        _record_transition(transitions, name, old_val, vec_val)
                        current_values[id_code] = vec_val
                continue

            # scalar: value char immediately followed by id code (no space)
            if len(line) >= 2 and line[0] in "01xzXZ":
                val     = line[0]
                id_code = line[1:]
                if id_code in id_to_name:
                    name    = id_to_name[id_code]
                    old_val = current_values.get(id_code, "x")
                    _record_transition(transitions, name, old_val, val)
                    current_values[id_code] = val
                continue

    return transitions


def _record_transition(transitions: dict, name: str, old_val: str, new_val: str):
    """Record a 0→1 or 1→0 transition for scalar values.
    For vectors, treat all-zero as logical 0 and any nonzero as logical 1."""
    def logical(v: str) -> str:
        if v in ("x", "z", "X", "Z"):
            return "x"
        # vector: check if all bits are 0
        digits = v.replace("x", "0").replace("z", "0").replace("X", "0").replace("Z", "0")
        try:
            return "0" if int(digits, 2) == 0 else "1"
        except ValueError:
            return "x"

    old_l = logical(old_val)
    new_l = logical(new_val)

    if old_l == "0" and new_l == "1":
        transitions[name].add("0→1")
    elif old_l == "1" and new_l == "0":
        transitions[name].add("1→0")


# ── status helper ──────────────────────────────────────────────────────────

def toggle_status(seen: set) -> str:
    if "0→1" in seen and "1→0" in seen:
        return "FULL"
    if seen:
        return "PARTIAL"
    return "NONE"


# ── main ───────────────────────────────────────────────────────────────────

def main():
    # ── load interface.yaml ────────────────────────────────────────────────
    if not IFACE_PATH.exists():
        print(f"ERROR: {IFACE_PATH} not found. Run 02_elaborate.py first.")
        sys.exit(1)

    with IFACE_PATH.open() as f:
        iface = yaml.safe_load(f)

    ports = iface.get("ports", [])
    if not ports:
        print("ERROR: No ports found in interface.yaml.")
        sys.exit(1)

    # ── check VCD ─────────────────────────────────────────────────────────
    vcd_missing = not VCD_PATH.exists() or VCD_PATH.stat().st_size == 0

    if vcd_missing:
        section = _skipped_section()
    else:
        transitions = parse_vcd(VCD_PATH)
        section     = _build_section(ports, transitions)

    # ── append to report ───────────────────────────────────────────────────
    if not REPORT_PATH.exists():
        print(f"WARNING: {REPORT_PATH} not found — creating it.")
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text("# Verification Report\n\n")

    existing = REPORT_PATH.read_text()

    # Remove any previous Section 5 block before appending fresh one
    existing = re.sub(
        r"\n## Section 5 — Toggle Coverage.*",
        "",
        existing,
        flags=re.DOTALL
    )

    REPORT_PATH.write_text(existing.rstrip() + "\n\n" + section + "\n")
    print(f"Toggle coverage appended to {REPORT_PATH}")


def _skipped_section() -> str:
    return (
        "## Section 5 — Toggle Coverage\n\n"
        "> **SKIPPED** — `out/waves.vcd` is missing or empty.\n"
        "> The DUT must contain an `initial` block with `$dumpfile` / `$dumpvars` "
        "for waveform output. Add the following to the DUT source and re-run simulation:\n"
        ">\n"
        "> ```verilog\n"
        "> initial begin\n"
        ">   if ($test$plusargs(\"vcd\")) begin\n"
        ">     $dumpfile(\"waves.vcd\");\n"
        ">     $dumpvars(0, <top_module>);\n"
        ">   end\n"
        "> end\n"
        "> ```\n"
    )


def _build_section(ports: list, transitions: dict) -> str:
    rows         = []
    total_trans  = 0
    seen_trans   = 0
    untoggled    = []

    for port in ports:
        name      = port.get("name", "?")
        direction = port.get("direction", "?")
        width     = port.get("width", 1)

        # Expected transitions per port: 2 (0→1 and 1→0)
        # Clocks will always show FULL — that's correct and expected
        total_trans += 2

        seen    = transitions.get(name, set())
        status  = toggle_status(seen)
        col_01  = "✓" if "0→1" in seen else "✗"
        col_10  = "✓" if "1→0" in seen else "✗"

        seen_trans += len(seen)

        if status == "NONE":
            untoggled.append(f"{name} (never toggled)")
        elif status == "PARTIAL":
            missing = "1→0" if "0→1" in seen else "0→1"
            untoggled.append(f"{name} (missing {missing})")

        rows.append(
            f"| {name:<30} | {direction:<8} | {str(width):<5} "
            f"| {col_01:<3} | {col_10:<3} | {status} |"
        )

    pct = int(100 * seen_trans / total_trans) if total_trans else 0

    header = (
        "## Section 5 — Toggle Coverage\n\n"
        "| Port                           | Direction | Width | 0→1 | 1→0 | Status  |\n"
        "|--------------------------------|-----------|-------|-----|-----|---------|"
    )

    table  = header + "\n" + "\n".join(rows)
    footer = f"\n\n**Toggle coverage:** {seen_trans}/{total_trans} transitions ({pct}%)"

    if untoggled:
        footer += "\n\n**Incomplete ports:**\n" + "\n".join(f"- {u}" for u in untoggled)
        footer += "\n\nPorts with status `NONE` are highest priority for `--mode add-sequence`."
    else:
        footer += "\n\n✓ All ports toggled in both directions."

    return table + footer


if __name__ == "__main__":
    main()