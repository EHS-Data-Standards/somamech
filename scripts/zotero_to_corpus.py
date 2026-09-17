#!/usr/bin/env python3
"""Build corpus.csv from a Zotero library.

Two ways in:

1. Straight from the Zotero API (needs an API key, since the group library
   is not public — create one at https://www.zotero.org/settings/keys with
   read access to the group):

       ZOTERO_API_KEY=xxxx uv run python scripts/zotero_to_corpus.py \\
           --group 6330536 --collection KKJVB5IK

2. From a CSV exported by the Zotero desktop app (right-click the
   collection -> Export Collection -> Format: CSV):

       uv run python scripts/zotero_to_corpus.py --from-csv export.csv

3. From the manifest written by scripts/zotero_pull_pdfs.py — only papers
   whose PDF was actually downloaded, and each row remembers its local PDF
   filename:

       uv run python scripts/zotero_to_corpus.py --from-manifest pdfs/manifest.csv

Either way the output is corpus.csv with columns pmid,doi,title,notes —
the format scripts/build_stubs.py reads. PMIDs are taken from each item's
"Extra" field when present ("PMID: 12345678"); otherwise the script asks
PubMed to resolve the DOI to a PMID. Items with neither a PMID nor a
resolvable DOI are listed at the end for hand-checking (they are written
to the CSV with an empty pmid so build-stubs will warn, not silently drop).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus.csv"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def http_json(url: str, headers: dict | None = None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp), dict(resp.headers)


def fetch_zotero_items(group: str, collection: str, api_key: str) -> list[dict]:
    """Fetch every bibliographic item in the collection (not attachments/notes)."""
    items: list[dict] = []
    start = 0
    limit = 100
    while True:
        url = (
            f"https://api.zotero.org/groups/{group}/collections/{collection}/items"
            f"?format=json&itemType=-attachment&limit={limit}&start={start}"
        )
        data, _ = http_json(url, {"Zotero-API-Key": api_key})
        page = [
            it["data"]
            for it in data
            if it.get("data", {}).get("itemType") not in ("attachment", "note")
        ]
        items.extend(page)
        if len(data) < limit:
            break
        start += limit
    return items


def pmid_from_extra(extra: str) -> str:
    m = re.search(r"PMID:?\s*(\d+)", extra or "", re.IGNORECASE)
    return f"PMID:{m.group(1)}" if m else ""


def pmid_from_doi(doi: str) -> str:
    """Ask PubMed which PMID a DOI belongs to."""
    if not doi:
        return ""
    url = (
        f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&term="
        + urllib.parse.quote(f'"{doi}"')
    )
    try:
        data, _ = http_json(url)
        ids = data["esearchresult"].get("idlist", [])
        time.sleep(0.4)  # NCBI rate limit without an API key
        if len(ids) == 1:
            return f"PMID:{ids[0]}"
    except Exception as e:  # noqa: BLE001 - a lookup failure just means "unresolved"
        print(f"  (DOI lookup failed for {doi}: {e})", file=sys.stderr)
    return ""


def rows_from_api(args) -> list[dict]:
    api_key = args.api_key or os.environ.get("ZOTERO_API_KEY", "")
    if not api_key:
        sys.exit(
            "No API key. Pass --api-key or set ZOTERO_API_KEY "
            "(create one at https://www.zotero.org/settings/keys "
            "with read access to the group)."
        )
    items = fetch_zotero_items(args.group, args.collection, api_key)
    print(f"Fetched {len(items)} items from Zotero.")
    rows = []
    for it in items:
        rows.append(
            {
                "title": (it.get("title") or "").strip(),
                "doi": (it.get("DOI") or "").strip(),
                "extra": it.get("extra") or "",
                "type": it.get("itemType", ""),
            }
        )
    return rows


def rows_from_csv(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "title": (row.get("Title") or "").strip(),
                    "doi": (row.get("DOI") or "").strip(),
                    "extra": row.get("Extra") or "",
                    "type": row.get("Item Type", ""),
                }
            )
    print(f"Read {len(rows)} items from {path}.")
    return rows


def rows_from_manifest(path: str) -> list[dict]:
    """Read the manifest zotero_pull_pdfs.py writes — one row per downloaded
    PDF. Items with several PDFs (e.g. paper + supplement) become one corpus
    row keyed on the first file."""
    by_item: dict[str, dict] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            item = by_item.setdefault(
                row["item_key"],
                {
                    "title": (row.get("title") or "").strip(),
                    "doi": (row.get("doi") or "").strip(),
                    "extra": f"PMID: {row['pmid'].split(':')[1]}" if row.get("pmid") else "",
                    "type": "journalArticle",
                    "pdf_filename": row["file"],
                },
            )
            if row["file"] != item["pdf_filename"]:
                item.setdefault("extra_files", []).append(row["file"])
    rows = list(by_item.values())
    print(f"Read {len(rows)} papers (with PDFs) from {path}.")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--group", default="6330536", help="Zotero group id")
    ap.add_argument("--collection", default="KKJVB5IK", help="Zotero collection key")
    ap.add_argument("--api-key", default="", help="Zotero API key (or env ZOTERO_API_KEY)")
    ap.add_argument("--from-csv", metavar="FILE", help="use a Zotero CSV export instead of the API")
    ap.add_argument("--from-manifest", metavar="FILE",
                    help="use the manifest written by zotero_pull_pdfs.py (only papers with downloaded PDFs)")
    ap.add_argument("--out", default=str(OUT), help="output path (default corpus.csv)")
    args = ap.parse_args()

    if args.from_manifest:
        rows = rows_from_manifest(args.from_manifest)
    elif args.from_csv:
        rows = rows_from_csv(args.from_csv)
    else:
        rows = rows_from_api(args)

    resolved, unresolved = [], []
    for i, r in enumerate(rows, 1):
        pmid = pmid_from_extra(r["extra"])
        how = "extra field" if pmid else ""
        if not pmid and r["doi"]:
            pmid = pmid_from_doi(r["doi"])
            how = "resolved from DOI" if pmid else ""
        entry = {
            "pmid": pmid,
            "doi": r["doi"],
            "title": r["title"],
            "pdf_filename": r.get("pdf_filename", ""),
            "notes": f"from Zotero ({how})" if how else "from Zotero (NO PMID FOUND — fix by hand)",
        }
        (resolved if pmid else unresolved).append(entry)
        if i % 25 == 0:
            print(f"  ...{i}/{len(rows)} looked up")

    out = Path(args.out)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pmid", "doi", "title", "pdf_filename", "notes"])
        w.writeheader()
        w.writerows(resolved + unresolved)

    print(f"\nWrote {out}: {len(resolved)} papers with PMIDs, {len(unresolved)} without.")
    if unresolved:
        print("\nThese need a PMID filled in by hand (or they may be books,")
        print("reports, or preprints that PubMed doesn't index):")
        for r in unresolved:
            print(f"  - {r['title'][:80]}  (doi: {r['doi'] or 'none'})")
    print("\nNext: review corpus.csv, then run `just build-stubs`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
