#!/usr/bin/env python3
"""Download every PDF in a Zotero collection into a local folder.

The papers/ folder is gitignored — publisher PDFs stay on this machine and
never reach the public repository.

Needs a Zotero API key with read access to the group INCLUDING file access
(create at https://www.zotero.org/settings/keys: check "Allow library access"
and, under the group, "Read Only" or better — file downloads ride on that).

Usage:
    ZOTERO_API_KEY=xxxx uv run python scripts/zotero_pull_pdfs.py \\
        --group 6330536 --collection CE587BRD

Options:
    --recursive     also walk subcollections of the collection
    --out papers    output folder (default papers/)

Each PDF is saved as <FirstAuthor>_<Year>_<zotero-key>.pdf and a manifest
(papers/manifest.csv) records which paper each file belongs to (title, DOI,
PMID when Zotero has it) so the files can be matched to corpus.csv rows.
Already-downloaded files are skipped, so re-running is safe.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.zotero.org"


def request(url: str, api_key: str, binary: bool = False):
    req = urllib.request.Request(url, headers={"Zotero-API-Key": api_key})
    resp = urllib.request.urlopen(req, timeout=120)
    if binary:
        return resp.read(), dict(resp.headers)
    return json.load(resp), dict(resp.headers)


def paged(url_base: str, api_key: str) -> list[dict]:
    """Fetch all pages of a Zotero listing."""
    out: list[dict] = []
    start, limit = 0, 100
    while True:
        sep = "&" if "?" in url_base else "?"
        data, _ = request(f"{url_base}{sep}format=json&limit={limit}&start={start}", api_key)
        out.extend(data)
        if len(data) < limit:
            break
        start += limit
    return out


def collection_keys(group: str, collection: str, api_key: str, recursive: bool) -> list[str]:
    keys = [collection]
    if recursive:
        todo = [collection]
        while todo:
            current = todo.pop()
            subs = paged(f"{API}/groups/{group}/collections/{current}/collections", api_key)
            for sub in subs:
                keys.append(sub["key"])
                todo.append(sub["key"])
    return keys


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text or "").strip("_") or "Unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--group", default="6330536")
    ap.add_argument("--collection", default="CE587BRD")
    ap.add_argument("--api-key", default="", help="Zotero API key (or env ZOTERO_API_KEY)")
    ap.add_argument("--recursive", action="store_true", help="also walk subcollections")
    ap.add_argument("--out", default="papers", help="output folder (default papers/)")
    args = ap.parse_args()

    api_key = args.api_key or os.environ.get("ZOTERO_API_KEY", "")
    if not api_key:
        sys.exit(
            "No API key. Pass --api-key or set ZOTERO_API_KEY "
            "(create one at https://www.zotero.org/settings/keys with "
            "read access to the group, including file access)."
        )

    out_dir = ROOT / args.out
    out_dir.mkdir(exist_ok=True)

    manifest_path = out_dir / "manifest.csv"
    already: set[str] = set()
    if manifest_path.is_file():
        with manifest_path.open() as f:
            already = {row["zotero_key"] for row in csv.DictReader(f)}

    rows: list[dict] = []
    downloaded = skipped = missing = 0

    for coll in collection_keys(args.group, args.collection, api_key, args.recursive):
        items = paged(f"{API}/groups/{args.group}/collections/{coll}/items/top", api_key)
        print(f"Collection {coll}: {len(items)} items")
        for it in items:
            d = it["data"]
            if d.get("itemType") in ("attachment", "note"):
                continue
            item_key = d["key"]
            title = d.get("title", "")
            year = ""
            m = re.search(r"\d{4}", d.get("date", "") or "")
            if m:
                year = m.group(0)
            creator = ""
            for c in d.get("creators", []):
                if c.get("creatorType") == "author":
                    creator = c.get("lastName") or c.get("name", "")
                    break
            pmid_m = re.search(r"PMID:?\s*(\d+)", d.get("extra", "") or "", re.IGNORECASE)

            # find this item's PDF attachments
            children = paged(f"{API}/groups/{args.group}/items/{item_key}/children", api_key)
            pdfs = [
                ch["data"]
                for ch in children
                if ch["data"].get("itemType") == "attachment"
                and ch["data"].get("contentType") == "application/pdf"
            ]
            if not pdfs:
                print(f"  (no PDF) {title[:70]}")
                missing += 1
                continue

            for n, att in enumerate(pdfs):
                att_key = att["key"]
                suffix = f"-{n + 1}" if n else ""
                fname = f"{slugify(creator)}_{year or 'noyear'}_{att_key}{suffix}.pdf"
                dest = out_dir / fname
                if att_key in already or dest.exists():
                    skipped += 1
                    continue
                try:
                    blob, _ = request(
                        f"{API}/groups/{args.group}/items/{att_key}/file", api_key, binary=True
                    )
                except Exception as e:  # noqa: BLE001 - record and move on
                    print(f"  FAILED {title[:60]}: {e}", file=sys.stderr)
                    continue
                dest.write_bytes(blob)
                downloaded += 1
                print(f"  + {fname}  ({len(blob) // 1024} KB)")
                rows.append(
                    {
                        "file": fname,
                        "zotero_key": att_key,
                        "item_key": item_key,
                        "title": title,
                        "doi": d.get("DOI", ""),
                        "pmid": f"PMID:{pmid_m.group(1)}" if pmid_m else "",
                    }
                )

    if rows:
        exists = manifest_path.is_file()
        with manifest_path.open("a", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=["file", "zotero_key", "item_key", "title", "doi", "pmid"]
            )
            if not exists:
                w.writeheader()
            w.writerows(rows)

    print(
        f"\nDone: {downloaded} downloaded, {skipped} already present, "
        f"{missing} items had no PDF attached."
    )
    print(f"Files in {out_dir.relative_to(ROOT)}/ (gitignored), manifest in {manifest_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
