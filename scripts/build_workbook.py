#!/usr/bin/env python3
"""Build ONE pooled Excel workbook from every kb/publications/ YAML file.

The per-paper YAML files are the source of truth — validated, quote-checked,
reviewed. This workbook is a generated product: rebuilt by `just
generate-workbook`, never hand-edited, and never committed in a curation PR.

Layout (same tab-per-class shape as scripts/yaml_to_excel.py, which this
script reuses): one tab per entity type, one row per entity — from ALL
papers. Every row's first column says which paper it came from
(`source_publication`, the PMID declared in that file), and a Papers tab
lists one row per source file.

Cross-paper ID rules, checked while pooling (and by `--check-only`, which is
the `just check-entity-ids` gate in `just qc`):

  * KeyEvent IDs are shared vocabulary — the same `KE:...` may appear in many
    papers on purpose. Identical rows are merged (sources joined); the same
    ID with DIFFERENT content is reported as an error, because two papers
    would be silently describing different things under one name.
  * Every other ID (assays, outputs, protocols, exposures, subjects) belongs
    to one paper. The same ID in two papers is an error.

Usage:
    uv run python scripts/build_workbook.py                       # kb/publications -> exports/soma_extractions.xlsx
    uv run python scripts/build_workbook.py --check-only          # just the ID rules, no file written
    uv run python scripts/build_workbook.py --kb-dir tests/data/valid --output tmp/pooled.xlsx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from yaml_to_excel import (  # noqa: E402 - reuse the per-paper converter's pieces
    COLLECTION_MAP,
    HEADERS,
    TAB_COLORS,
    _assay_row,
    _cellular_system_row,
    _collect_exposure_conditions,
    _collect_key_events,
    _collect_subjects,
    _exposure_row,
    _key_event_row,
    _invivo_subject_row,
    _make_sheet,
    _output_row,
    _protocol_row,
)

DEFAULT_KB_DIR = ROOT / "kb" / "publications"
DEFAULT_OUT = ROOT / "exports" / "soma_extractions.xlsx"

# Tabs whose IDs are shared vocabulary across papers (mergeable when identical)
SHARED_ID_TABS = {"KeyEvent"}


def source_of(data: dict, path: Path) -> str:
    """The paper a file came from: its declared PMID, else the filename."""
    src = (data or {}).get("source_publication") or {}
    if isinstance(src, dict) and src.get("reference"):
        return src["reference"]
    print(f"WARNING: {path.name} has no source_publication — using filename", file=sys.stderr)
    return path.name


def collect(files: list[Path]):
    """Pool rows per tab across all files.

    Returns (tabs, papers, errors) where tabs maps tab name ->
    list of (source, row_tuple), papers is the Papers-tab rows, and errors
    are ID-rule violations.
    """
    tabs: dict[str, list[tuple[str, tuple]]] = {}
    papers: list[list] = []
    # id -> (tab, source, row) for collision checking
    seen_ids: dict[tuple[str, str], tuple[str, tuple]] = {}
    errors: list[str] = []

    def add(tab: str, source: str, entity_id: str, row: tuple):
        key = (tab, entity_id)
        if entity_id and key in seen_ids:
            prev_source, prev_row = seen_ids[key]
            if prev_source == source:
                pass  # same paper repeating an id within itself is fine here
            elif tab in SHARED_ID_TABS:
                if prev_row == row:
                    # identical shared entity: merge, record the extra source
                    for i, (s, r) in enumerate(tabs[tab]):
                        if r == row and entity_id in r:
                            tabs[tab][i] = (f"{s}; {source}", r)
                            return
                else:
                    errors.append(
                        f"{tab} id '{entity_id}' differs between {prev_source} and "
                        f"{source} — same name, different content"
                    )
            else:
                errors.append(
                    f"{tab} id '{entity_id}' appears in both {prev_source} and "
                    f"{source} — IDs outside KeyEvent must be unique to one paper"
                )
        else:
            seen_ids[key] = (source, row)
        tabs.setdefault(tab, []).append((source, row))

    for path in files:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        source = source_of(data, path)
        src_pub = data.get("source_publication") or {}
        n_assays = sum(len(data.get(k) or []) for k in COLLECTION_MAP)
        papers.append(
            [
                source,
                src_pub.get("reference_title", ""),
                src_pub.get("doi", ""),
                path.name,
                n_assays,
            ]
        )

        for p in data.get("protocols", []) or []:
            add("Protocol", source, p.get("id", ""), _protocol_row(p))
        for ec in _collect_exposure_conditions(data):
            add("ExposureCondition", source, ec.get("id", ""), _exposure_row(ec))
        for ke in _collect_key_events(data):
            add("KeyEvent", source, ke.get("id", ""), _key_event_row(ke))
        cellular, invivo = _collect_subjects(data)
        for s in cellular:
            add("CellularSystem", source, s.get("id", ""), _cellular_system_row(s))
        for s in invivo:
            add("InVivoSubject", source, s.get("id", ""), _invivo_subject_row(s))
        for coll_key, (assay_tab, output_tab) in COLLECTION_MAP.items():
            for a in data.get(coll_key, []) or []:
                add(assay_tab, source, a.get("id", ""), _assay_row(a, HEADERS.get(assay_tab, [])))
                out = a.get("has_specified_output")
                if out and isinstance(out, dict):
                    out = dict(out)
                    out.setdefault("source_assay", a.get("id", ""))
                    add(output_tab, source, out.get("id", ""), _output_row(out, HEADERS.get(output_tab, [])))

    return tabs, papers, errors


def write_workbook(tabs, papers, output_path: Path):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    _make_sheet(
        wb,
        "Papers",
        ["source_publication", "title", "doi", "file", "n_assays"],
        papers,
        tab_color=TAB_COLORS.get("Metadata", "4472C4"),
    )

    # Fixed tab order: shared context first, then assay/output pairs
    order = ["Protocol", "ExposureCondition", "KeyEvent", "CellularSystem", "InVivoSubject"]
    for _, (assay_tab, output_tab) in COLLECTION_MAP.items():
        order.extend([assay_tab, output_tab])
    for tab in [t for t in order if t in tabs]:
        rows = [(src, *row) for src, row in tabs[tab]]
        _make_sheet(
            wb,
            tab,
            ["source_publication", *HEADERS.get(tab, [])],
            rows,
            tab_color=TAB_COLORS.get(tab),
        )
        wb[tab].freeze_panes = "B2"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kb-dir", default=str(DEFAULT_KB_DIR), help="folder of per-paper YAML files")
    ap.add_argument("--output", "-o", default=str(DEFAULT_OUT), help="workbook to write")
    ap.add_argument("--check-only", action="store_true", help="only run the cross-paper ID rules")
    args = ap.parse_args()

    kb_dir = Path(args.kb_dir)
    files = sorted(p for p in kb_dir.glob("*.yaml"))
    if not files:
        print(f"No YAML files in {kb_dir} — nothing to pool.")
        return 0

    tabs, papers, errors = collect(files)

    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    n_rows = sum(len(v) for v in tabs.values())
    print(f"Pooled {len(papers)} papers -> {len(tabs)} tabs, {n_rows} rows.")

    if errors:
        print(f"{len(errors)} cross-paper ID problem(s) — fix these in the YAML.", file=sys.stderr)
        return 1
    if args.check_only:
        print("Cross-paper ID rules: OK")
        return 0

    out = Path(args.output)
    write_workbook(tabs, papers, out)
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
