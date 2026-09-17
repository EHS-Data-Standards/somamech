#!/usr/bin/env python3
"""Extract a local PDF's text into the local-only reference cache.

Writes references_cache_local/PMID_<n>.md in the same format the quote
checker (linkml-reference-validator) reads, so quotes taken from a paywalled
paper can be verified on this machine. The local cache folder is gitignored —
paywalled full text never reaches the public repository.

Run ``just fetch-reference PMID:<n>`` first: the paper's real title is copied
from the committed cache entry so title checks agree between the two caches.

Usage:
    python scripts/extract_paper_text.py path/to/paper.pdf PMID:12345678
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def cached_title(pmid: str) -> str:
    """Read the paper's title from the committed reference cache, if present."""
    cache_file = ROOT / "references_cache" / f"{pmid.replace(':', '_')}.md"
    if cache_file.is_file():
        m = re.search(r"^title:\s*(.+)$", cache_file.read_text(), re.MULTILINE)
        if m:
            return m.group(1).strip().strip('"')
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="path to the PDF file")
    ap.add_argument("pmid", help="the paper's PubMed ID, e.g. PMID:12345678")
    ap.add_argument("--out-dir", default="references_cache_local")
    ap.add_argument("--title", default="", help="paper title (default: copied from references_cache/)")
    args = ap.parse_args()

    if not re.fullmatch(r"PMID:\d+", args.pmid):
        print(f"ERROR: {args.pmid!r} is not a PMID:<digits> identifier", file=sys.stderr)
        return 1
    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"ERROR: no such file: {pdf_path}", file=sys.stderr)
        return 1

    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n\n".join(pages).strip()
    if not text:
        print("ERROR: no text could be extracted (scanned/image-only PDF?)", file=sys.stderr)
        return 1

    title = args.title or cached_title(args.pmid)
    if not title:
        print(
            "WARNING: no title found — run `just fetch-reference "
            f"{args.pmid}` first, or pass --title. Title checks will fail "
            "until the frontmatter has the real title.",
            file=sys.stderr,
        )

    out_dir = ROOT / args.out_dir
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{args.pmid.replace(':', '_')}.md"
    title_line = f'title: "{title}"' if title else "title: UNKNOWN"
    out_file.write_text(
        "---\n"
        f'reference_id: "{args.pmid}"\n'
        f"{title_line}\n"
        "content_type: full_text_pdf_local\n"
        f"source_file: {pdf_path.name}\n"
        "---\n\n"
        f"# {title or args.pmid}\n\n"
        "## Content\n\n"
        f"{text}\n"
    )
    print(f"Wrote {out_file.relative_to(ROOT)} ({len(text):,} characters, {len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
