#!/usr/bin/env python3
"""Populate the SEPIO requirements workbook from the answer modules.

Usage:
    python build_workbook.py <blank template .xlsx> <output .xlsx>

The blank template is SEPIO's own Requirements_Collection_Forms.xlsx, from
https://github.com/sepio-framework/sepio-linkml/tree/main/docs/requirements-collection

Answers live in answers_part1..5.py, one module per group of sheets, so that a
revision after project-representative review is an edit to a data structure
rather than a hand edit to a spreadsheet cell. Rerun this script to regenerate.

Cells are written by xlsx_cells.edit_workbook, which edits the sheet XML inside
the template's own zip container and copies every other part byte-for-byte.
That is required by rules 36-40 of REQUIREMENTS_FORM_PROMPT.md: the template
carries Excel Tables, drawings, VML drawings and legacy comments that common
Python spreadsheet libraries do not round-trip faithfully, and the returned
workbook must open without an Excel repair warning.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import xlsx_cells as X  # noqa: E402
import answers_part1, answers_part2, answers_part3, answers_part4, answers_part5  # noqa: E402

MODULES = (answers_part1, answers_part2, answers_part3, answers_part4, answers_part5)

MAPPING_COL_HEADER = "SEPIO Mapping Summary"


def collect() -> dict[str, dict[str, str]]:
    edits: dict[str, dict[str, str]] = {}
    for mod in MODULES:
        for sheet, values in mod.SHEETS.items():
            overlap = set(edits.get(sheet, {})) & set(values)
            if overlap:
                raise SystemExit(f"two modules write the same cells in {sheet}: {sorted(overlap)[:5]}")
            edits.setdefault(sheet, {}).update(values)
    return edits


def check(template: Path, out: Path, edits: dict[str, dict[str, str]]) -> int:
    """Post-population checks required by rule 41 and guidance section IV."""
    import openpyxl

    problems: list[str] = []
    orig = openpyxl.load_workbook(template)
    wb = openpyxl.load_workbook(out)

    # Rule 33 / guidance line 283: never edit the SEPIO Mapping Summary columns.
    for ws_o, ws_n in zip(orig.worksheets, wb.worksheets):
        for cell in ws_o[1]:
            if cell.value and MAPPING_COL_HEADER in str(cell.value):
                for r in range(1, ws_o.max_row + 1):
                    if ws_o.cell(r, cell.column).value != ws_n.cell(r, cell.column).value:
                        problems.append(f"mapping column edited: {ws_n.title} {cell.column_letter}{r}")

    # Required Y/N/M columns must be complete and use exact labels.
    specs = {
        "CRS 3-Claim Rep Structure Form": (("F", "G"), range(2, 7)),
        "RCS 4-Reified Claim Semantics F": (("F", "G"), range(2, 6)),
        "EIT 5-Evidence Item Type Form": (("F", "G"), range(2, 22)),
        "EINT 6-Evidence Interpretation ": (("E", "F"), range(2, 14)),
        "PROV 7-Provenance Types Form": (
            ("G", "H"),
            [r for r in range(2, 50) if r not in (12, 21, 27, 35, 42)],
        ),
    }
    for name, (cols, rows) in specs.items():
        ws = wb[name]
        for r in rows:
            for col in cols:
                if ws[f"{col}{r}"].value not in ("Y", "N", "M"):
                    problems.append(f"bad Y/N/M: {name} {col}{r} = {ws[f'{col}{r}'].value!r}")

    # EIT conditional columns and their controlled vocabularies.
    locs = {"LOCAL", "EXTERNAL", "UNSURE"}
    forms = {"FREE_TEXT", "STRUCTURED_METADATA", "STRUCTURED_CONTENT", "STORED_ARTIFACT", "UNSURE"}
    addrs = {"YES", "NO", "NO_SPECIFIC_REQUIREMENT"}
    ws = wb["EIT 5-Evidence Item Type Form"]
    for r in range(2, 22):
        f2 = ws[f"G{r}"].value
        loc, form, addr = (ws[f"{c}{r}"].value or "" for c in "HIJ")
        if f2 in ("Y", "M"):
            if not loc:
                problems.append(f"EIT row {r}: F2={f2} but F3 location empty")
            for tok in (t.strip() for t in loc.split(";") if t.strip()):
                if tok not in locs:
                    problems.append(f"EIT row {r}: bad location {tok!r}")
            if "LOCAL" in loc:
                for tok in (t.strip() for t in form.split(";") if t.strip()):
                    if tok not in forms:
                        problems.append(f"EIT row {r}: bad representation form {tok!r}")
                if not form:
                    problems.append(f"EIT row {r}: LOCAL but F4 empty")
                if addr not in addrs:
                    problems.append(f"EIT row {r}: bad addressability {addr!r}")
        elif loc or form or addr:
            problems.append(f"EIT row {r}: F2={f2} but conditional columns populated")

    # Required fields on CT and PO.
    ws = wb["CT 2-Claim Type Form"]
    for r in range(2, 8):
        for col in "ABCDEG":
            if not ws[f"{col}{r}"].value:
                problems.append(f"CT {col}{r} empty (required)")
    ws = wb["PO 1-Project Overview Form"]
    for r in (1, 2):
        if not ws[f"B{r}"].value:
            problems.append(f"PO B{r} empty (required)")

    # Guidance line 282: when F2 differs from F1, the explanation must name the
    # supporting source/support type, or flag the row for human review.
    pairs = {
        "CRS 3-Claim Rep Structure Form": ("F", "G", "H"),
        "RCS 4-Reified Claim Semantics F": ("F", "G", "H"),
        "EIT 5-Evidence Item Type Form": ("F", "G", "N"),
        "EINT 6-Evidence Interpretation ": ("E", "F", "G"),
        "PROV 7-Provenance Types Form": ("G", "H", "J"),
    }
    support = re.compile(
        r"EXPLICIT_FUTURE_REQUIREMENT|EXISTING_PROJECT_CAPABILITY_NOT_IN_CANONICAL_EXPORT"
        r"|DOCUMENTED_MODEL_INTENT|UNRESOLVED|HUMAN REVIEW|flagged",
        re.I,
    )
    differing = 0
    for name, (c1, c2, ce) in pairs.items():
        ws = wb[name]
        for r in range(2, ws.max_row + 1):
            a, b = ws[f"{c1}{r}"].value, ws[f"{c2}{r}"].value
            if a in ("Y", "N", "M") and b in ("Y", "N", "M") and a != b:
                differing += 1
                if not support.search(str(ws[f"{ce}{r}"].value or "")):
                    problems.append(f"F1!=F2 without a support type or review flag: {name} row {r}")

    changed = [
        n for n in zipfile.ZipFile(template).namelist()
        if zipfile.ZipFile(template).read(n) != zipfile.ZipFile(out).read(n)
    ]
    total = len(zipfile.ZipFile(template).namelist())

    print(f"cells written      : {sum(len(v) for v in edits.values())} across {len(edits)} sheets")
    print(f"workbook parts     : {len(changed)} changed, {total - len(changed)} byte-identical, {total} total")
    print(f"rows where F1!=F2  : {differing}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nAll checks passed.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    template, out = Path(argv[1]), Path(argv[2])
    if not template.is_file():
        print(f"template not found: {template}")
        return 2
    edits = collect()
    X.edit_workbook(template, out, edits)
    return check(template, out, edits)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
