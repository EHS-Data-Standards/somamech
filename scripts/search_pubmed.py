#!/usr/bin/env python3
"""Run the committed PubMed searches (conf/pubmed_searches.tsv).

Used by the /fetch-and-curate skill to discover new papers. For each search
it records how many papers matched (the run log) and which papers matched
(the raw retrieval — one row per paper per search, duplicates across searches
kept on purpose: a paper found by five searches is probably more central than
one found by one).

Examples:
    # Run every search, keep only open-access papers, skip known ones:
    python scripts/search_pubmed.py --open-access-only --exclude-known

    # Run two specific searches:
    python scripts/search_pubmed.py --search L1_PMMCC --search L4_MCCEnd

Output (written to data/literature_search/):
    run_log.csv                 date, search_id, hit_count  (appended)
    raw_retrieval_<date>.csv    pmid, search_id
    candidates_<date>.csv       pmid, n_searches, search_ids  (deduped, ranked)
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
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEARCHES_TSV = ROOT / "conf" / "pubmed_searches.tsv"
OUT_DIR = ROOT / "data" / "literature_search"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "soma-search-pubmed"


def eutils_json(endpoint: str, params: dict) -> dict:
    params = {**params, "retmode": "json", "tool": TOOL}
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def load_searches() -> dict[str, str]:
    """search_id -> english-filtered query"""
    searches = {}
    with SEARCHES_TSV.open() as f:
        for row in csv.DictReader(f, delimiter="\t"):
            searches[row["search_id"]] = row["english_filtered_query"]
    return searches


def run_search(query: str, retmax: int) -> list[str]:
    """Return the PMIDs matching one PubMed query."""
    data = eutils_json(
        "esearch.fcgi",
        {"db": "pubmed", "term": query, "retmax": retmax},
    )
    time.sleep(0.4)  # stay under NCBI's rate limit without an API key
    return [f"PMID:{i}" for i in data["esearchresult"].get("idlist", [])]


def filter_open_access(pmids: list[str]) -> set[str]:
    """Keep only PMIDs with a PubMed Central full-text record."""
    oa: set[str] = set()
    ids = [p.split(":")[1] for p in pmids]
    for start in range(0, len(ids), 200):
        batch = ids[start : start + 200]
        data = eutils_json(
            "elink.fcgi", {"dbfrom": "pubmed", "db": "pmc", "id": ",".join(batch)}
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


def known_pmids() -> set[str]:
    """PMIDs already in corpus.csv, stubs/, or kb/publications/."""
    known: set[str] = set()
    corpus = ROOT / "corpus.csv"
    if corpus.is_file():
        with corpus.open() as f:
            for row in csv.DictReader(f):
                m = re.fullmatch(r"(?:PMID:)?(\d+)", (row.get("pmid") or "").strip())
                if m:
                    known.add(f"PMID:{m.group(1)}")
    for d, key in [(ROOT / "stubs", "pmid")]:
        if d.is_dir():
            for f in d.glob("*.yaml"):
                try:
                    data = yaml.safe_load(f.read_text()) or {}
                except yaml.YAMLError:
                    continue
                if data.get(key):
                    known.add(data[key])
    kb = ROOT / "kb" / "publications"
    if kb.is_dir():
        for f in kb.glob("*.yaml"):
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError:
                continue
            src = (data or {}).get("source_publication") or {}
            if isinstance(src, dict) and src.get("reference"):
                known.add(src["reference"])
    return known


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--search", action="append", metavar="ID",
                    help="run only this search (repeatable; default: all)")
    ap.add_argument("--retmax", type=int, default=10000, help="max hits per search")
    ap.add_argument("--open-access-only", action="store_true",
                    help="keep only papers with a PubMed Central record")
    ap.add_argument("--exclude-known", action="store_true",
                    help="drop papers already in corpus.csv, stubs/, or kb/")
    args = ap.parse_args()

    searches = load_searches()
    if args.search:
        missing = [s for s in args.search if s not in searches]
        if missing:
            print(f"ERROR: unknown search id(s): {', '.join(missing)}", file=sys.stderr)
            print(f"Known: {', '.join(searches)}", file=sys.stderr)
            return 1
        searches = {k: searches[k] for k in args.search}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    raw_rows: list[tuple[str, str]] = []

    run_log = OUT_DIR / "run_log.csv"
    log_exists = run_log.is_file()
    with run_log.open("a", newline="") as logf:
        logw = csv.writer(logf)
        if not log_exists:
            logw.writerow(["date", "search_id", "hit_count"])
        for sid, query in searches.items():
            pmids = run_search(query, args.retmax)
            print(f"{sid}: {len(pmids)} hits")
            logw.writerow([today, sid, len(pmids)])
            raw_rows.extend((p, sid) for p in pmids)

    raw_path = OUT_DIR / f"raw_retrieval_{today}.csv"
    with raw_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pmid", "search_id"])
        w.writerows(raw_rows)

    by_pmid: dict[str, list[str]] = defaultdict(list)
    for pmid, sid in raw_rows:
        by_pmid[pmid].append(sid)

    dropped_known = dropped_paywalled = 0
    if args.exclude_known:
        known = known_pmids()
        before = len(by_pmid)
        by_pmid = {p: s for p, s in by_pmid.items() if p not in known}
        dropped_known = before - len(by_pmid)
    if args.open_access_only:
        oa = filter_open_access(list(by_pmid))
        before = len(by_pmid)
        by_pmid = {p: s for p, s in by_pmid.items() if p in oa}
        dropped_paywalled = before - len(by_pmid)

    cand_path = OUT_DIR / f"candidates_{today}.csv"
    ranked = sorted(by_pmid.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    with cand_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pmid", "n_searches", "search_ids"])
        for pmid, sids in ranked:
            w.writerow([pmid, len(sids), ";".join(sorted(set(sids)))])

    print(f"\n{len(raw_rows)} raw hits -> {len(by_pmid)} unique candidate papers")
    if dropped_known:
        print(f"  ({dropped_known} dropped as already known)")
    if dropped_paywalled:
        print(f"  ({dropped_paywalled} dropped as not open access)")
    print(f"Run log:        {run_log.relative_to(ROOT)}")
    print(f"Raw retrieval:  {raw_path.relative_to(ROOT)}")
    print(f"Candidates:     {cand_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
