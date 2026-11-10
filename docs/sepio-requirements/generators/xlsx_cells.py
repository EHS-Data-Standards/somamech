"""Surgical cell writer for the SEPIO requirements workbook.

Rules 36-40 of REQUIREMENTS_FORM_PROMPT.md require the returned workbook to
preserve the template's formatting exactly and to open without an Excel repair
warning. The template carries Excel Tables, drawings, VML drawings and legacy
comments, which openpyxl does not round-trip faithfully. So we edit the sheet
XML in place inside the zip and copy every other part byte-for-byte.

Values are written as inline strings, so sharedStrings.xml is never touched.
Each cell keeps whatever style index (@s) the template gave it.
"""
from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("", NS)


def _q(tag: str) -> str:
    return f"{{{NS}}}{tag}"


def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n


def split_ref(ref: str) -> tuple[str, int]:
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    if not m:
        raise ValueError(f"bad cell ref {ref!r}")
    return m.group(1), int(m.group(2))


def set_cells(sheet_xml: bytes, values: dict[str, str]) -> bytes:
    """Return sheet_xml with `values` ({'A2': 'text'}) written as inline strings."""
    root = ET.fromstring(sheet_xml)
    data = root.find(_q("sheetData"))
    if data is None:
        raise ValueError("no sheetData")

    rows = {int(r.get("r")): r for r in data.findall(_q("row"))}

    by_row: dict[int, dict[str, str]] = {}
    for ref, val in values.items():
        col, rownum = split_ref(ref)
        by_row.setdefault(rownum, {})[col] = val

    for rownum in sorted(by_row):
        row = rows.get(rownum)
        if row is None:
            row = ET.Element(_q("row"), {"r": str(rownum)})
            # insert in row order
            later = [r for n, r in sorted(rows.items()) if n > rownum]
            if later:
                data.insert(list(data).index(later[0]), row)
            else:
                data.append(row)
            rows[rownum] = row

        cells = {split_ref(c.get("r"))[0]: c for c in row.findall(_q("c"))}

        for col, val in sorted(by_row[rownum].items(), key=lambda kv: col_to_num(kv[0])):
            cell = cells.get(col)
            if cell is None:
                cell = ET.Element(_q("c"), {"r": f"{col}{rownum}"})
                later = [
                    c
                    for cc, c in sorted(cells.items(), key=lambda kv: col_to_num(kv[0]))
                    if col_to_num(cc) > col_to_num(col)
                ]
                if later:
                    row.insert(list(row).index(later[0]), cell)
                else:
                    row.append(cell)
                cells[col] = cell

            # drop any existing value/formula children, keep @s
            for child in list(cell):
                cell.remove(child)
            style = cell.get("s")
            cell.attrib.clear()
            cell.set("r", f"{col}{rownum}")
            if style is not None:
                cell.set("s", style)

            if val is None or val == "":
                continue
            cell.set("t", "inlineStr")
            is_el = ET.SubElement(cell, _q("is"))
            t_el = ET.SubElement(is_el, _q("t"))
            t_el.text = str(val)
            # preserve leading/trailing whitespace and newlines
            t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    return ET.tostring(root, encoding="UTF-8", xml_declaration=True)


def edit_workbook(src: Path, dst: Path, edits: dict[str, dict[str, str]]) -> None:
    """edits maps sheet filename ('xl/worksheets/sheet2.xml') -> {ref: value}."""
    src, dst = Path(src), Path(dst)
    if dst.exists():
        dst.unlink()
    with zipfile.ZipFile(src) as zin:
        infos = zin.infolist()
        payload = {i.filename: zin.read(i.filename) for i in infos}

    for sheet, values in edits.items():
        if sheet not in payload:
            raise KeyError(f"{sheet} not in workbook")
        payload[sheet] = set_cells(payload[sheet], values)

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for i in infos:  # preserve original part order
            zout.writestr(i, payload[i.filename])


def verify(path: Path, expect: dict[str, dict[str, str]] | None = None) -> None:
    """Read back with openpyxl and confirm the workbook parses and values landed."""
    import openpyxl

    wb = openpyxl.load_workbook(path)
    order = [n for n in zipfile.ZipFile(path).namelist() if n.startswith("xl/worksheets/sheet")]
    print(f"  parsed OK: {len(wb.worksheets)} sheets, {len(order)} sheet parts")
    if expect:
        sheet_by_part = dict(zip(sorted(order, key=lambda s: int(re.search(r"(\d+)", s).group(1))), wb.worksheets))
        bad = 0
        for part, values in expect.items():
            ws = sheet_by_part[part]
            for ref, val in values.items():
                got = ws[ref].value
                if val and (got or "") != val:
                    bad += 1
                    if bad <= 3:
                        print(f"  MISMATCH {ws.title} {ref}: {str(got)[:60]!r} != {str(val)[:60]!r}")
        print(f"  value check: {bad} mismatches")
