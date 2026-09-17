#!/usr/bin/env python3
"""Build and inspect the paper queue (stubs/) from corpus.csv.

What it does, in plain terms:

  * ``python scripts/build_stubs.py`` — read ``corpus.csv``, look up each
    paper's title/journal/year on PubMed, and write one stub file per paper
    into ``stubs/``. Papers that already have a stub, or are already
    extracted into ``kb/publications/``, are skipped — so it is always safe
    to re-run after corpus.csv grows.

  * ``python scripts/build_stubs.py --check-only`` — the gate used by
    ``just check-stubs``: fail if any stub is malformed (bad PMID, duplicate
    PMID across stubs). Never fails for bookkeeping drift.

  * ``python scripts/build_stubs.py --next 5 --claims tmp/claims.json`` —
    show the next papers available to work on: stubs whose decision is
    EXTRACT or UNDECIDED and whose PMID does not appear in any open claim
    issue title (tmp/claims.json comes from ``just fetch-claims``).

corpus.csv format: a header row, then one paper per row. The only required
column is ``pmid`` (with or without the "PMID:" prefix). Optional columns
``doi``, ``title``, and ``notes`` are carried into the stub; anything else
is ignored. Rows with an empty pmid are skipped with a warning.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CORPUS_CSV = ROOT / "corpus.csv"
STUBS_DIR = ROOT / "stubs"
KB_DIR = ROOT / "kb" / "publications"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "soma-build-stubs"


def normalize_pmid(raw: str) -> str | None:
    """Turn '12345678' or 'PMID:12345678' into 'PMID:12345678'."""
    raw = raw.strip()
    m = re.fullmatch(r"(?:PMID:)?(\d+)", raw)
    return f"PMID:{m.group(1)}" if m else None


def eutils_json(endpoint: str, params: dict) -> dict:
    params = {**params, "retmode": "json", "tool": TOOL}
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def fetch_metadata(pmids: list[str]) -> dict[str, dict]:
    """Fetch title/journal/year/doi for a batch of PMIDs from PubMed."""
    out: dict[str, dict] = {}
    ids = [p.split(":")[1] for p in pmids]
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        data = eutils_json("esummary.fcgi", {"db": "pubmed", "id": ",".join(batch)})
        for uid in data.get("result", {}).get("uids", []):
            rec = data["result"][uid]
            doi = ""
            for aid in rec.get("articleids", []):
                if aid.get("idtype") == "doi":
                    doi = aid.get("value", "")
            year = ""
            m = re.match(r"(\d{4})", rec.get("pubdate", ""))
            if m:
                year = m.group(1)
            first_author = ""
            if rec.get("authors"):
                first_author = rec["authors"][0].get("name", "").split()[0]
            out[f"PMID:{uid}"] = {
                "title": rec.get("title", "").rstrip("."),
                "journal": rec.get("fulljournalname", ""),
                "year": year,
                "doi": doi,
                "first_author": first_author,
            }
        time.sleep(0.4)  # stay under NCBI's rate limit without an API key
    return out


def fetch_open_access(pmids: list[str]) -> set[str]:
    """Return the PMIDs that have a PubMed Central full-text record."""
    oa: set[str] = set()
    ids = [p.split(":")[1] for p in pmids]
    for start in range(0, len(ids), 100):
        batch = ids[start : start + 100]
        data = eutils_json(
            "elink.fcgi",
            {"dbfrom": "pubmed", "db": "pmc", "id": ",".join(batch)},
        )
        for linkset in data.get("linksets", []):
            has_pmc = any(
                db.get("dbto") == "pmc" and db.get("links")
                for db in linkset.get("linksetdbs", [])
            )
            if has_pmc:
                for src in linkset.get("ids", []):
                    oa.add(f"PMID:{src}")
        time.sleep(0.4)
    return oa


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "Unknown"


def existing_pmids() -> tuple[dict[str, Path], set[str]]:
    """PMIDs already stubbed, and PMIDs already extracted into kb/."""
    stubbed: dict[str, Path] = {}
    if STUBS_DIR.is_dir():
        for f in sorted(STUBS_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError:
                continue
            if isinstance(data, dict) and data.get("pmid"):
                stubbed[data["pmid"]] = f
    extracted: set[str] = set()
    if KB_DIR.is_dir():
        for f in sorted(KB_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError:
                continue
            src = (data or {}).get("source_publication") or {}
            if isinstance(src, dict) and src.get("reference"):
                extracted.add(src["reference"])
    return stubbed, extracted


def read_corpus() -> list[dict]:
    if not CORPUS_CSV.is_file():
        print(f"No {CORPUS_CSV.name} found — nothing to do.")
        return []
    rows = []
    with CORPUS_CSV.open() as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            pmid = normalize_pmid(row.get("pmid", "") or "")
            if not pmid:
                print(f"WARNING: corpus.csv line {i}: no usable pmid — skipped")
                continue
            rows.append(
                {
                    "pmid": pmid,
                    "doi": (row.get("doi") or "").strip(),
                    "title": (row.get("title") or "").strip(),
                    "pdf_filename": (row.get("pdf_filename") or "").strip(),
                    "notes": (row.get("notes") or "").strip(),
                }
            )
    return rows


def build(args) -> int:
    rows = read_corpus()
    stubbed, extracted = existing_pmids()
    new = [r for r in rows if r["pmid"] not in stubbed and r["pmid"] not in extracted]
    if not new:
        print(f"Queue up to date: {len(stubbed)} stubs, {len(extracted)} extracted.")
        return 0

    print(f"Fetching PubMed metadata for {len(new)} new papers...")
    meta = fetch_metadata([r["pmid"] for r in new])
    oa = fetch_open_access([r["pmid"] for r in new])

    STUBS_DIR.mkdir(exist_ok=True)
    for r in new:
        m = meta.get(r["pmid"], {})
        if not m:
            print(f"WARNING: {r['pmid']} not found on PubMed — check the ID. Skipped.")
            continue
        stub = {
            "pmid": r["pmid"],
            "doi": r["doi"] or m.get("doi", ""),
            "title": r["title"] or m.get("title", ""),
            "journal": m.get("journal", ""),
            "year": int(m["year"]) if m.get("year") else None,
            "source": "corpus_csv",
            "open_access": r["pmid"] in oa,
            "pdf_filename": r.get("pdf_filename", ""),
            "status": "OPEN",
            "decision": "UNDECIDED",
            "added_date": date.today().isoformat(),
        }
        if r["notes"]:
            stub["notes"] = r["notes"]
        stub = {k: v for k, v in stub.items() if v not in ("", None)}
        name = f"{slugify(m.get('first_author', ''))}_{m.get('year', 'noyear')}_{r['pmid'].replace(':', '')}.yaml"
        path = STUBS_DIR / name
        path.write_text(yaml.safe_dump(stub, sort_keys=False, allow_unicode=True))
        print(f"  + stubs/{name}")
    return 0


def check_only(args) -> int:
    """Gate: fail only on malformed stubs (bad PMID, duplicates)."""
    errors = []
    seen: dict[str, str] = {}
    if STUBS_DIR.is_dir():
        for f in sorted(STUBS_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError as e:
                errors.append(f"{f.name}: unparseable YAML: {e}")
                continue
            pmid = data.get("pmid", "")
            if not re.fullmatch(r"PMID:\d+", str(pmid)):
                errors.append(f"{f.name}: bad or missing pmid: {pmid!r}")
                continue
            if pmid in seen:
                errors.append(f"{f.name}: duplicate of {seen[pmid]} (both {pmid})")
            seen[pmid] = f.name
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    print(f"Checked {len(seen) + len(errors)} stubs: {len(errors)} problem(s).")
    return 1 if errors else 0


def next_unclaimed(args) -> int:
    """Show the next papers available to claim."""
    claimed: set[str] = set()
    claims_path = Path(args.claims)
    if claims_path.is_file():
        for issue in json.loads(claims_path.read_text()):
            for m in re.finditer(r"PMID:\d+", issue.get("title", "")):
                claimed.add(m.group(0))
    candidates = []
    if STUBS_DIR.is_dir():
        for f in sorted(STUBS_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError:
                continue
            if data.get("status", "OPEN") != "OPEN":
                continue
            if data.get("decision", "UNDECIDED") not in ("EXTRACT", "UNDECIDED"):
                continue
            if data.get("pmid") in claimed:
                continue
            candidates.append((f.name, data))
    # EXTRACT (screened-in) papers come before UNDECIDED ones
    candidates.sort(key=lambda c: (c[1].get("decision") != "EXTRACT", c[0]))
    if not candidates:
        print("No unclaimed papers in the queue.")
        return 0
    print(f"Next {min(args.next, len(candidates))} unclaimed papers "
          f"({len(candidates)} available, {len(claimed)} claimed):\n")
    for name, data in candidates[: args.next]:
        oa = "open access" if data.get("open_access") else "abstract only / local PDF"
        print(f"  {data.get('pmid')}  [{data.get('decision')}] ({oa})")
        print(f"    {data.get('title', '?')}")
        print(f"    stub: stubs/{name}\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check-only", action="store_true", help="gate mode: fail on malformed stubs")
    ap.add_argument("--next", type=int, metavar="N", help="show the next N unclaimed papers")
    ap.add_argument("--claims", default="tmp/claims.json", help="claims JSON from `just fetch-claims`")
    args = ap.parse_args()
    if args.check_only:
        return check_only(args)
    if args.next:
        return next_unclaimed(args)
    return build(args)


if __name__ == "__main__":
    raise SystemExit(main())
