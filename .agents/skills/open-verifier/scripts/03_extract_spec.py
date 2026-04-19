#!/usr/bin/env python3
"""
03_extract_spec.py — Structural PDF parser for protocol specifications.

Two modes:
  --list-chapters          Print chapter names and page numbers from PDF ToC
  --chapter N --pdf PATH   Extract and print text of chapter N

Usage:
  python3 03_extract_spec.py --pdf spec.pdf --list-chapters
  python3 03_extract_spec.py --pdf spec.pdf --chapter 3
"""

import argparse
import json
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
    sys.exit(1)


def list_chapters(pdf_path):
    """Extract internal bookmark tree (ToC) and print as numbered list with page numbers.
    Falls back to listing all pages with their first line of text if no ToC exists."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    if toc:
        print(f"Table of Contents for: {pdf_path}")
        print(f"{'#':<6} {'Level':<7} {'Title':<60} {'Page':<6}")
        print("-" * 80)
        for idx, (level, title, page_num) in enumerate(toc, 1):
            indent = "  " * (level - 1)
            print(f"{idx:<6} {level:<7} {indent}{title:<60} {page_num:<6}")
    else:
        # Fallback: list all pages with their first line of text as a title
        print(f"No ToC found in {pdf_path}. Listing pages with first-line titles:")
        print(f"{'#':<6} {'Page':<7} {'First Line':<70}")
        print("-" * 80)
        for page_idx in range(len(doc)):
            page = doc.load_page(page_idx)
            text = page.get_text("text").strip()
            first_line = text.split("\n")[0][:70] if text else "(empty page)"
            print(f"{page_idx + 1:<6} {page_idx + 1:<7} {first_line}")

    doc.close()


def extract_chapter(pdf_path, chapter_num):
    """Identify start and end page from ToC, extract text from those pages.
    NEVER loads the entire PDF into memory at once — uses page-by-page iteration."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    if not toc:
        print(f"ERROR: No ToC found in {pdf_path}. Cannot extract by chapter number.", file=sys.stderr)
        print("Use --list-chapters to see available pages, then extract by page range.", file=sys.stderr)
        doc.close()
        sys.exit(1)

    if chapter_num < 1 or chapter_num > len(toc):
        print(f"ERROR: Chapter {chapter_num} out of range. PDF has {len(toc)} ToC entries.", file=sys.stderr)
        doc.close()
        sys.exit(1)

    # Get the chapter entry (1-indexed from user, 0-indexed internally)
    level, title, start_page = toc[chapter_num - 1]

    # Find end page: next entry at the same or higher level, or end of document
    end_page = len(doc)  # default to end of document
    for i in range(chapter_num, len(toc)):
        next_level, _, next_page = toc[i]
        if next_level <= level:
            end_page = next_page - 1
            break

    # Clamp to valid range
    start_page = max(1, start_page)
    end_page = min(end_page, len(doc))

    print(f"=== Chapter {chapter_num}: {title} ===")
    print(f"=== Pages {start_page} to {end_page} ===")
    print()

    # Extract text page-by-page (never load entire PDF into memory)
    total_chars = 0
    for page_num in range(start_page - 1, end_page):  # fitz uses 0-indexed pages
        page = doc.load_page(page_num)
        text = page.get_text("text")
        total_chars += len(text)
        print(text)
        print(f"\n--- [Page {page_num + 1}] ---\n")

    # Print JSON metadata summary at the end
    metadata = {
        "chapter": chapter_num,
        "title": title,
        "pages": [start_page, end_page],
        "char_count": total_chars,
    }
    print("\n=== METADATA ===")
    print(json.dumps(metadata))

    doc.close()


def main():
    parser = argparse.ArgumentParser(
        description="Structural PDF parser for protocol specifications."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="Path to the protocol specification PDF"
    )
    parser.add_argument(
        "--list-chapters",
        action="store_true",
        help="Print chapter names and page numbers from PDF ToC"
    )
    parser.add_argument(
        "--chapter",
        type=int,
        default=None,
        help="Extract and print text of chapter N"
    )
    args = parser.parse_args()

    # Validate PDF exists
    import pathlib
    pdf_path = pathlib.Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    if args.list_chapters:
        list_chapters(args.pdf)
    elif args.chapter is not None:
        extract_chapter(args.pdf, args.chapter)
    else:
        print("ERROR: Specify either --list-chapters or --chapter N", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
