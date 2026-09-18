#!/usr/bin/env python3
"""Verification receipts for evidence quotes CI cannot see.

Some papers can only be cached abstract-only in the public repository (the
publisher blocks automated full-text fetching and the PMC copy is
restricted). Quotes from those papers are verified locally — against text
extracted from the curator's own PDF into the gitignored
``references_cache_local/`` — and CI cannot repeat that check. A *receipt*
bridges the gap: after the local quote check passes, ``write`` records a
SHA-256 hash of every such snippet in ``verification/PMID_<n>.json``, which
IS committed. In CI, ``check`` recomputes each hash from the kb YAML and
requires a matching receipt, so CI can at least prove that the local
verification ran over exactly the snippets in the PR, and that nobody edited
a quote after it was verified.

A receipt attests to a local check; it is not the check itself. Writing one
requires the paper's full text to be present in the local cache, and
``just verify-snippets`` only writes receipts after the quote checker has
passed against that text. A reviewer auditing a restricted paper should
re-derive the text from the PDF and re-run the verification rather than
trusting the receipt (see the extraction-pr-review skill).

Usage:
    python scripts/snippet_receipts.py write kb/publications/FILE.yaml...
    python scripts/snippet_receipts.py check kb/publications/FILE.yaml...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REFS_CACHE = ROOT / "references_cache"
REFS_CACHE_LOCAL = ROOT / "references_cache_local"
RECEIPTS_DIR = ROOT / "verification"


def snippet_hash(snippet: str) -> str:
    """Hash the snippet exactly as parsed from the YAML."""
    return hashlib.sha256(snippet.encode("utf-8")).hexdigest()


def cache_content_type(pmid: str) -> str | None:
    """content_type from the committed cache entry, or None if not cached."""
    cache_file = REFS_CACHE / f"{pmid.replace(':', '_')}.md"
    if not cache_file.is_file():
        return None
    m = re.search(r"^content_type:\s*(\S+)", cache_file.read_text(), re.MULTILINE)
    return m.group(1) if m else None


def collect_snippets(data: object, out: dict[str, set[str]]) -> None:
    """Walk the parsed YAML, collecting snippet strings per reference PMID."""
    if isinstance(data, dict):
        ref = data.get("reference")
        snippet = data.get("snippet")
        if isinstance(ref, str) and isinstance(snippet, str):
            out.setdefault(ref, set()).add(snippet)
        for value in data.values():
            collect_snippets(value, out)
    elif isinstance(data, list):
        for item in data:
            collect_snippets(item, out)


def abstract_only_snippets(kb_file: Path) -> dict[str, set[str]]:
    """Snippets in this kb file whose committed cache entry is abstract-only."""
    with kb_file.open() as f:
        data = yaml.safe_load(f)
    per_ref: dict[str, set[str]] = {}
    collect_snippets(data, per_ref)
    return {
        ref: snippets
        for ref, snippets in per_ref.items()
        if (cache_content_type(ref) or "").startswith("abstract")
    }


def receipt_path(pmid: str) -> Path:
    return RECEIPTS_DIR / f"{pmid.replace(':', '_')}.json"


def cmd_write(files: list[Path]) -> int:
    wrote_any = False
    for kb_file in files:
        for ref, snippets in sorted(abstract_only_snippets(kb_file).items()):
            local = REFS_CACHE_LOCAL / f"{ref.replace(':', '_')}.md"
            if not local.is_file():
                print(
                    f"ERROR: {ref} is abstract-only in the committed cache and its "
                    f"full text is not in {REFS_CACHE_LOCAL.name}/ — run "
                    f"'just extract-paper-text <pdf> {ref}' and re-run "
                    f"'just verify-snippets' before writing a receipt.",
                    file=sys.stderr,
                )
                return 1
            RECEIPTS_DIR.mkdir(exist_ok=True)
            path = receipt_path(ref)
            receipt = {
                "reference_id": ref,
                "kb_file": str(kb_file),
                "content_type_in_committed_cache": cache_content_type(ref),
                "verified_with": "just verify-snippets (linkml-reference-validator, committed + local cache)",
                "verified_date": date.today().isoformat(),
                "snippet_sha256": sorted(snippet_hash(s) for s in snippets),
            }
            path.write_text(json.dumps(receipt, indent=2) + "\n")
            print(f"Receipt written: {path.relative_to(ROOT)} ({len(snippets)} snippets for {ref})")
            wrote_any = True
    if not wrote_any:
        print("No abstract-only references cited — no receipts needed.")
    return 0


def cmd_check(files: list[Path]) -> int:
    problems = 0
    checked = 0
    for kb_file in files:
        for ref, snippets in sorted(abstract_only_snippets(kb_file).items()):
            path = receipt_path(ref)
            if not path.is_file():
                print(
                    f"[ERROR] {kb_file}: {ref} is abstract-only in the committed cache "
                    f"and has no verification receipt ({path.relative_to(ROOT)}). "
                    f"Run 'just verify-snippets {kb_file}' locally (with the full text "
                    f"in references_cache_local/) and commit the receipt."
                )
                problems += len(snippets)
                continue
            receipt = json.loads(path.read_text())
            known = set(receipt.get("snippet_sha256", []))
            for snippet in sorted(snippets):
                checked += 1
                if snippet_hash(snippet) not in known:
                    preview = snippet[:60] + ("…" if len(snippet) > 60 else "")
                    print(
                        f"[ERROR] {kb_file}: snippet not covered by the receipt for "
                        f"{ref} — it was added or edited after local verification. "
                        f"Re-run 'just verify-snippets {kb_file}' and commit the "
                        f"updated receipt. Snippet: \"{preview}\""
                    )
                    problems += 1
    if problems:
        print(f"{problems} receipt problem(s) found.")
        return 1
    print(f"Receipts OK: {checked} abstract-only snippet(s) covered by committed receipts.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["write", "check"])
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    if args.command == "write":
        return cmd_write(args.files)
    return cmd_check(args.files)


if __name__ == "__main__":
    sys.exit(main())
