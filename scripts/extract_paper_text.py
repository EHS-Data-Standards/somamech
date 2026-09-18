#!/usr/bin/env python3
"""Extract a local PDF's text into the local-only reference cache.

Writes references_cache_local/PMID_<n>.md in the same format the quote
checker (linkml-reference-validator) reads, so quotes taken from a paywalled
paper can be verified on this machine. The local cache folder is gitignored —
paywalled full text never reaches the public repository.

Run ``just fetch-reference PMID:<n>`` first: the paper's real title is copied
from the committed cache entry so title checks agree between the two caches.

Text fidelity
-------------
A quote is checked as a literal substring of this file, so an extraction
artifact reads exactly like a wrong quote. Two are worth knowing about:

* **Ligatures.** Publisher PDFs set "fi"/"fl" as single glyphs (U+FB01,
  U+FB02...). Extractors hand those straight back, so "significant" arrives as
  "signiﬁcant" and no honest quote containing that word can ever match. The
  mapping back to ASCII is lossless and unambiguous, so this script always
  applies it.
* **Spurious mid-word spaces.** pypdf breaks a word at a font change, turning
  "significant" into "signi ﬁcant". There is no safe way to repair that after
  the fact — the same pattern appears legitimately in "and ﬂaring" — so this
  script prefers poppler's ``pdftotext``, which does not introduce the break,
  and falls back to pypdf only when poppler is not installed. The frontmatter
  records which extractor ran.

What is *not* repaired: the maths font's rendering of decimal points as
colons ("-166:8") and of subscripts ("PM2:5"), and en dashes in compounds
("exposure-response"). Those are judgement calls, not encoding artifacts, and
rewriting them here to make a quote match would defeat the point of the check.
A quote that trips over one of them should be narrowed to a span that does
not, never reworded.

Usage:
    python scripts/extract_paper_text.py path/to/paper.pdf PMID:12345678
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]

# Typographic ligatures -> the ASCII letters they stand for. Lossless: these
# code points have no meaning beyond "these letters, set as one glyph".
LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "st",
    "\ufb06": "st",
}


def expand_ligatures(text: str) -> str:
    """Replace ligature glyphs with their letters (see module docstring)."""
    for glyph, letters in LIGATURES.items():
        text = text.replace(glyph, letters)
    return text


def extract_with_pdftotext(pdf_path: Path) -> str | None:
    """Text via poppler's pdftotext, or None if it is unavailable or fails."""
    exe = shutil.which("pdftotext")
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [exe, "-q", str(pdf_path), "-"],
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", errors="replace").strip() or None


def extract_with_pypdf(pdf_path: Path) -> tuple[str, int]:
    """Text via pypdf, plus the page count."""
    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n\n".join(pages).strip(), len(pages)


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

    text = extract_with_pdftotext(pdf_path)
    extractor = "pdftotext (poppler)"
    if text is None:
        text, _ = extract_with_pypdf(pdf_path)
        extractor = "pypdf"
        print(
            "NOTE: poppler's pdftotext is not available, falling back to pypdf. "
            "pypdf splits words at font changes ('signi ficant'), so some "
            "otherwise-exact quotes may not verify. Install poppler for a "
            "faithful extraction.",
            file=sys.stderr,
        )
    if not text:
        print("ERROR: no text could be extracted (scanned/image-only PDF?)", file=sys.stderr)
        return 1
    text = expand_ligatures(text)

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
        f"extracted_with: {extractor}, ligatures expanded\n"
        "---\n\n"
        f"# {title or args.pmid}\n\n"
        "## Content\n\n"
        f"{text}\n"
    )
    print(
        f"Wrote {out_file.relative_to(ROOT)} ({len(text):,} characters, "
        f"extracted with {extractor}, ligatures expanded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
