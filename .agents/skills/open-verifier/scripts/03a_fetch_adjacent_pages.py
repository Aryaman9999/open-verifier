#!/usr/bin/env python3
"""
03a_fetch_adjacent_pages.py — Sliding-window page extractor for protocol specs.

Extracts pages adjacent to a given page number from a PDF, producing text and
PNG files in a temporary output directory. Used when timing diagrams or tables
span page boundaries.

Usage:
  python3 03a_fetch_adjacent_pages.py \\
    --pdf "spec.pdf" \\
    --current_page 42 \\
    --direction next \\
    --count 2 \\
    --out_dir "out/spec_pages"
"""

import argparse, fitz, json, os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--pdf", required=True)
parser.add_argument("--current_page", type=int, required=True)
parser.add_argument("--direction", choices=["prev", "next", "both"], default="next")
parser.add_argument("--count", type=int, default=2)
parser.add_argument("--out_dir", default="out/spec_pages")
args = parser.parse_args()

out_dir = Path(args.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(args.pdf)
pages = []

if args.direction in ["prev", "both"]:
    start = max(1, args.current_page - args.count)
    for i in range(start, args.current_page):
        pages.append(i)

pages.append(args.current_page)

if args.direction in ["next", "both"]:
    end = args.current_page + args.count
    for i in range(args.current_page + 1, end + 1):
        if i <= len(doc):
            pages.append(i)

extracted = []
for i in pages:
    page = doc.load_page(i-1)
    text = page.get_text("text")
    pix = page.get_pixmap(dpi=300)
    base = f"page_{i:03d}"
    (out_dir / f"{base}.txt").write_text(text)
    pix.save(str(out_dir / f"{base}.png"))
    extracted.append(base)

print(json.dumps({"extracted": extracted, "status": "ok", "message": f"Extracted {len(extracted)} pages to {out_dir}"}))
