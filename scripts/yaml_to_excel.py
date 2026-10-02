#!/usr/bin/env python3
"""Convert a validated SOMA YAML file to a formatted Excel workbook.

Reads SOMA Container YAML data and produces an Excel workbook with tabs
for each entity type, styled consistently with the SOMA project conventions.

Tab names and column lists are derived from the installed soma-schema at
import time (see the "Schema-driven headers" section), so a slot added to
the schema shows up in the workbook without editing this script.

Usage:
    uv run python scripts/yaml_to_excel.py --input <yaml> --output <xlsx>
    uv run python scripts/yaml_to_excel.py --input <yaml> --output <xlsx> --template project/excel/soma.xlsx
"""

import argparse
import datetime
import sys
from importlib.resources import files as _pkg_files
from pathlib import Path

import openpyxl
import yaml
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from soma_duckdb import (  # noqa: E402 - needs the sys.path line above
    QUANTITY_CLASSES,
    TERM_CLASSES,
    is_entity,
    load_schema,
)

# ---------------------------------------------------------------------------
# Styling (matches generate_paper_excel.py)
# ---------------------------------------------------------------------------

HEADER_FONT = Font(bold=True, size=11, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
WRAP = Alignment(wrap_text=True, vertical="top")

# Tab colors by entity type
TAB_COLORS = {
    "Metadata": "4472C4",
    "Protocol": "70AD47",
    "ExposureCondition": "FFC000",
    "KeyEvent": "ED7D31",
    "CellularSystem": "4472C4",
    "InVivoSubject": "4472C4",
    "PopulationSubject": "4472C4",
    "ModelSystem": "4472C4",
    "AdverseOutcomePathway": "ED7D31",
    "CFTRFunctionAssay": "C00000",
    "CFTRFunctionOutput": "C00000",
    "GeneExpressionAssay": "5B9BD5",
    "GeneExpressionOutput": "5B9BD5",
    "GobletCellAssay": "A9D18E",
    "GobletCellOutput": "A9D18E",
    "BALFSputumAssay": "7030A0",
    "BALFSputumOutput": "7030A0",
    "LungFunctionAssay": "002060",
    "LungFunctionOutput": "002060",
    "FoxJExpressionAssay": "BF8F00",
    "FoxJExpressionOutput": "BF8F00",
    "CiliaryFunctionAssay": "548235",
    "CiliaryFunctionOutput": "548235",
    "ASLAssay": "2E75B6",
    "ASLOutput": "2E75B6",
    "MucociliaryClearanceAssay": "843C0C",
    "MucociliaryClearanceOutput": "843C0C",
    "OxidativeStressAssay": "BF8F00",
    "OxidativeStressOutput": "BF8F00",
    "EGFRSignalingAssay": "ED7D31",
    "EGFRSignalingOutput": "ED7D31",
    "Responses": "2E75B6",
    "ResponseComparison": "C55A11",
    "KeyEventRelationship": "ED7D31",
}

# ---------------------------------------------------------------------------
# Schema-driven headers
# ---------------------------------------------------------------------------
# Tab names and column lists come from the installed soma-schema, read with
# the same SchemaView mapping rules as scripts/soma_duckdb.py:
#   * QuantityValue slot   -> <slot>_value / <slot>_unit columns
#   * QuantityRange slot   -> <slot>_min_value / <slot>_max_value / <slot>_unit
#   * term reference slot  -> <slot> (label) + <slot>_id columns
#   * entity reference     -> the referenced id ('; '-joined when multivalued)
#   * plain scalar / enum  -> one column ('; '-joined when multivalued)
# Two slots are deliberately not columns: `has_specified_output` (each output
# record already gets its own Output-tab row) and `evidence` (quote-level
# provenance with no natural key -- it lives in the YAML and in the DuckDB
# `evidence` table, not in the spreadsheet view).

_SV = load_schema(str(_pkg_files("soma") / "schema" / "soma.yaml"))

_SKIPPED_SLOTS = {"has_specified_output", "evidence"}
_FRONT_COLUMNS = ("id", "name", "description")


def _slot_specs(slot):
    """(header, kind, slot_name) triples for one induced slot."""
    rng = slot.range
    n = slot.name
    if slot.designates_type:
        return [(n, "scalar", n)]
    if rng == "QuantityRange":
        return [
            (f"{n}_min_value", "qty_min", n),
            (f"{n}_max_value", "qty_max", n),
            (f"{n}_unit", "qty_unit", n),
        ]
    if rng in QUANTITY_CLASSES:
        base = n[: -len("_value")] if n.endswith("_value") else n
        return [(f"{base}_value", "qty_value", n), (f"{base}_unit", "qty_unit", n)]
    if rng in TERM_CLASSES:
        if slot.multivalued:
            return [(n, "term_list", n)]
        return [(n, "term_label", n), (f"{n}_id", "term_id", n)]
    if is_entity(_SV, rng):
        if slot.multivalued:
            return [(n, "ref_list", n)]
        return [(n, "ref", n)]
    return [(n, "scalar", n)]


def _class_specs(class_names):
    """Merged column specs for a tab pooling these classes (base class first),
    with id/name/description pulled to the front."""
    specs, seen = [], set()
    for cls in class_names:
        for s in _SV.class_induced_slots(cls):
            if s.name in _SKIPPED_SLOTS:
                continue
            for spec in _slot_specs(s):
                if spec[0] not in seen:
                    seen.add(spec[0])
                    specs.append(spec)
    front = [sp for name in _FRONT_COLUMNS for sp in specs if sp[0] == name]
    return front + [sp for sp in specs if sp[0] not in _FRONT_COLUMNS]


# Concrete study-subject classes: each gets its own tab, rows routed by the
# subject_type designator (so PopulationSubject cohorts no longer land on the
# CellularSystem tab with the wrong columns).
SUBJECT_TABS = tuple(
    c for c in _SV.class_descendants("StudySubject") if c != "StudySubject"
)

# Tab -> schema classes pooled into it. The Protocol and KeyEvent tabs pool
# the base class with its concrete subtypes (ImagingProtocol,
# StainingProtocol, ..., MolecularInitiatingEvent), so subtype-specific slots
# become columns too.
_TAB_CLASSES = {
    "Protocol": list(_SV.class_descendants("Protocol")),
    "ExposureCondition": ["ExposureCondition"],
    "KeyEvent": list(_SV.class_descendants("KeyEvent")),
    "ResponseComparison": ["ResponseComparison"],
    "KeyEventRelationship": ["KeyEventRelationship"],
    "AdverseOutcomePathway": ["AdverseOutcomePathway"],
}
for _subj in SUBJECT_TABS:
    _TAB_CLASSES[_subj] = [_subj]

# YAML collection key -> (assay tab name, output tab name), from the
# Container's slots: every multivalued Container slot whose range class
# declares has_specified_output is an assay collection.
COLLECTION_MAP = {}
for _s in _SV.class_induced_slots("Container"):
    if _s.multivalued and _s.range in _SV.all_classes():
        _hso = next(
            (x for x in _SV.class_induced_slots(_s.range) if x.name == "has_specified_output"),
            None,
        )
        if _hso is not None:
            COLLECTION_MAP[_s.name] = (_s.range, _hso.range)
            _TAB_CLASSES[_s.range] = [_s.range]
            _TAB_CLASSES[_hso.range] = [_hso.range]

_TAB_SPECS = {tab: _class_specs(classes) for tab, classes in _TAB_CLASSES.items()}

# Every output record also says which assay produced it; this column is
# synthesized by the converters rather than declared on the schema class.
for _assay_tab, _output_tab in COLLECTION_MAP.values():
    _TAB_SPECS[_output_tab].append(("source_assay", "scalar", "source_assay"))

HEADERS = {tab: [h for h, _, _ in specs] for tab, specs in _TAB_SPECS.items()}

# Long-format tab: one row per (output record x measurement), so each
# experimental condition's response, uncertainty, and unit line up.
# Hand-shaped rather than schema-derived.
HEADERS["Responses"] = [
    "assay_id", "assay_type", "output_id", "experimental_group",
    "exposure_condition", "measurement", "value", "unit",
    "central_tendency", "variability", "sample_size",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _style_header(ws, row, max_col):
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = WRAP
        cell.border = THIN_BORDER


def _add_row(ws, row, data):
    for col, val in enumerate(data, 1):
        cell = ws.cell(row=row, column=col, value=val)
        cell.alignment = WRAP
        cell.border = THIN_BORDER


def _auto_width(ws, max_col, min_w=12, max_w=40):
    for col in range(1, max_col + 1):
        letter = get_column_letter(col)
        ws.column_dimensions[letter].width = min(
            max(min_w, max(len(str(c.value or "")) for c in ws[letter])),
            max_w,
        )


def _make_sheet(wb, name, headers, rows, tab_color=None):
    ws = wb.create_sheet(name)
    if tab_color:
        ws.sheet_properties.tabColor = tab_color
    ncol = len(headers)
    for j, h in enumerate(headers, 1):
        ws.cell(row=1, column=j, value=h)
    _style_header(ws, 1, ncol)
    for i, row_data in enumerate(rows, 2):
        _add_row(ws, i, row_data)
    _auto_width(ws, ncol)
    return ws


def _fmt_value_unit(obj):
    """Extract value and unit string from a measurement dict like {value: '0.5', unit: {id: ..., name: ...}}."""
    if not obj or not isinstance(obj, dict):
        return "", ""
    # a present-but-null key blanks rather than stringifying to 'None'.
    # Checked against None instead of falsiness so a real 0 survives.
    val = obj.get("value")
    val = "" if val is None else val
    unit_obj = obj.get("unit")
    if unit_obj is None:
        unit_obj = {}
    if isinstance(unit_obj, dict):
        unit_name = unit_obj.get("name", "")
        unit_id = unit_obj.get("id", "")
        unit_str = f"{unit_name} ({unit_id})" if unit_id else unit_name
    else:
        unit_str = str(unit_obj)
    return _as_number(val), unit_str


def _as_number(val):
    """A real int/float when the value parses as one, so Excel gets a numeric
    cell; curator strings like '<0.05' or '~12' pass through unchanged."""
    if isinstance(val, (int, float)):
        return val
    try:
        f = float(val)
    except (TypeError, ValueError):
        return str(val)
    return int(f) if f.is_integer() and "." not in str(val) and "e" not in str(val).lower() else f


def _fmt_variability(var):
    """Format a Variability dict like {variability_type: ..., value: ..., unit: {...}}
    or interval form {variability_type: ..., lower_bound: ..., upper_bound: ...}."""
    if not var or not isinstance(var, dict):
        return ""
    vtype = var.get("variability_type", "")
    unit_obj = var.get("unit", {})
    unit_name = unit_obj.get("name", "") if isinstance(unit_obj, dict) else str(unit_obj or "")
    lower = var.get("lower_bound")
    upper = var.get("upper_bound")
    if lower not in (None, "") or upper not in (None, ""):
        core = f"{lower or ''}-{upper or ''}"
    else:
        core = f"±{var.get('value', '')}"
    text = f"{core} {unit_name}".strip()
    return f"{text} ({vtype})" if vtype else text


def _fmt_id_name(obj):
    """Format an object with id/name as 'name (id)' or just 'id'."""
    if not obj or not isinstance(obj, dict):
        return str(obj) if obj else ""
    obj_id = obj.get("id", "")
    obj_name = obj.get("name", "")
    if obj_name and obj_id:
        return f"{obj_name} ({obj_id})"
    return obj_id or obj_name or ""


def _fmt_list_refs(items):
    """Format a list of references as semicolon-separated id strings."""
    if not items:
        return ""
    if isinstance(items, dict):
        return items.get("id", "")
    if isinstance(items, list):
        return "; ".join(
            item.get("id", str(item)) if isinstance(item, dict) else str(item)
            for item in items
        )
    return str(items)


def _get_nested(d, *keys, default=""):
    """Safely traverse nested dicts."""
    current = d
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current if current is not None else default


# ---------------------------------------------------------------------------
# Metadata extraction from YAML header comments
# ---------------------------------------------------------------------------

def _extract_metadata(yaml_path):
    """Extract metadata from YAML file header comments."""
    rows = [["Field", "Value"]]
    with open(yaml_path) as f:
        in_header = False
        for line in f:
            line = line.rstrip()
            if line.startswith("# ===="):
                in_header = not in_header
                continue
            if line.startswith("# ") and not line.startswith("# ----"):
                text = line[2:].strip()
                if not text or text.startswith("==="):
                    continue
                if ":" in text and not text.startswith("http"):
                    key, _, val = text.partition(":")
                    rows.append([key.strip(), val.strip()])
                elif text.startswith("- "):
                    rows.append(["", text[2:].strip()])
                else:
                    rows.append(["Note", text])
    return rows


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def _collect_exposure_conditions(data):
    """Collect unique exposure conditions from all assays."""
    seen = {}
    for coll_key in COLLECTION_MAP:
        for assay in data.get(coll_key, []) or []:
            conditions = assay.get("has_exposure_condition", [])
            if isinstance(conditions, dict):
                conditions = [conditions]
            for ec in conditions or []:
                ec_id = ec.get("id", "")
                if ec_id and ec_id not in seen:
                    seen[ec_id] = ec
    return list(seen.values())


def _collect_key_events(data):
    """Collect unique key events: the container-level declarations first
    (the one Container collection nothing else reads), then assay inlines."""
    seen = {}
    for ke in data.get("key_events", []) or []:
        if isinstance(ke, dict):
            ke_id = ke.get("id", "")
            if ke_id and ke_id not in seen:
                seen[ke_id] = ke
    for coll_key in COLLECTION_MAP:
        for assay in data.get(coll_key, []) or []:
            ke = assay.get("informs_on_key_event")
            if ke and isinstance(ke, dict):
                ke_id = ke.get("id", "")
                if ke_id and ke_id not in seen:
                    seen[ke_id] = ke
    return list(seen.values())


# Output-record keys that are not measurement slots
_NON_MEASUREMENT_KEYS = {
    "id", "name", "description", "experimental_group", "measured_under",
    "source_assay",
}


def _iter_outputs(assay):
    """Yield each output record of an assay (handles list and legacy dict form)."""
    outs = assay.get("has_specified_output")
    if isinstance(outs, dict):
        outs = [outs]
    for out in outs or []:
        if isinstance(out, dict):
            yield out


def _collect_response_rows(data):
    """One row per (output record x measurement): the long-format table with
    each condition's response value, uncertainty, and unit side by side."""
    rows = []
    for coll_key, (assay_tab, _output_tab) in COLLECTION_MAP.items():
        for assay in data.get(coll_key, []) or []:
            for out in _iter_outputs(assay):
                for slot, mv in out.items():
                    if slot in _NON_MEASUREMENT_KEYS or not isinstance(mv, dict):
                        continue
                    if "value" not in mv and "unit" not in mv:
                        continue
                    val, unit = _fmt_value_unit(mv)
                    rows.append((
                        assay.get("id", ""),
                        assay_tab,
                        out.get("id", ""),
                        out.get("experimental_group", ""),
                        # range: ExposureCondition -- a CURIE string today
                        # (non-inlined), coerced for the same reason as above
                        _fmt_cell(out.get("measured_under", "")),
                        slot,
                        val,
                        unit,
                        mv.get("central_tendency", ""),
                        _fmt_variability(mv.get("variability")),
                        mv.get("sample_size", ""),
                    ))
    return rows


def _collect_subjects(data):
    """Collect unique study subjects, grouped by concrete class tab.

    Routed by the subject_type designator; a subject with no (or an unknown)
    subject_type keeps the historical default of CellularSystem.
    """
    groups = {tab: {} for tab in SUBJECT_TABS}
    for coll_key in COLLECTION_MAP:
        for assay in data.get(coll_key, []) or []:
            subj = assay.get("study_subject")
            if not subj or not isinstance(subj, dict):
                continue
            tab = subj.get("subject_type", "")
            if tab not in groups:
                tab = "CellularSystem"
            groups[tab].setdefault(subj.get("id", ""), subj)
    return {tab: list(seen.values()) for tab, seen in groups.items()}


def _collect_protocols(data):
    """Top-level protocols plus protocol objects inlined on assays'
    follows_protocols, deduplicated by id (first occurrence wins)."""
    seen: dict = {}
    for p in data.get("protocols", []) or []:
        if isinstance(p, dict):
            seen.setdefault(p.get("id", id(p)), p)
    for coll_key in COLLECTION_MAP:
        for assay in data.get(coll_key, []) or []:
            protos = assay.get("follows_protocols", [])
            if isinstance(protos, dict):
                protos = [protos]
            for p in protos or []:
                if isinstance(p, dict):
                    seen.setdefault(p.get("id", id(p)), p)
    return list(seen.values())


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _join_multivalued(values):
    """Render a multivalued slot as one '; '-joined cell.

    Entries are plain strings in the schema (and in current kb data), but
    tolerate dict entries (e.g. a primer set split into gene/forward/reverse)
    by flattening them to 'key: value' pairs so nothing exports as '{...}'.
    """
    if values is None:
        return ""
    if not isinstance(values, list):
        values = [values]
    parts = []
    for v in values:
        if isinstance(v, dict):
            parts.append(", ".join(f"{k}: {x}" for k, x in v.items()))
        else:
            parts.append(str(v))
    return "; ".join(parts)


# What openpyxl writes without help. datetime.datetime subclasses
# datetime.date, so the one entry covers both.
_EXCEL_SCALARS = (
    str,
    int,
    float,
    bool,
    datetime.date,
    datetime.time,
    datetime.timedelta,
)


def _fmt_cell(value):
    """Coerce one slot value into something openpyxl can write.

    The assay and output row builders are header-driven: a slot named in
    HEADERS with no special handling is read straight off the record. Most are
    scalars, but a slot whose range is an inlined class arrives as a dict --
    target_cell_type, for one, is a CellTypeReference -- and openpyxl raises
    ValueError rather than writing it. Format those the way the hand-written
    row builders already format their term and measurement objects, so adding
    an inlined slot to HEADERS can never break the workbook again.

    Everything openpyxl writes natively is handed back untouched, temporal
    types included: it writes date, time and timedelta as real typed cells, so
    one reaching this function must not be flattened into text. A validated
    kb file cannot carry one -- LinkML maps `range: date` to a JSON-Schema
    string, so an unquoted `assay_date` fails `linkml-validate` before it gets
    here -- but `yaml_to_excel.py --input` can be pointed at a file nobody
    validated, and a passthrough that silently dropped them would be wrong.
    """
    if value is None or isinstance(value, _EXCEL_SCALARS):
        return value
    if isinstance(value, dict):
        # a measurement before a term: a dict carrying both keeps its value
        if "value" in value or "unit" in value:
            val, unit = _fmt_value_unit(value)
            return f"{val} {unit}".strip()
        if value.get("id") or value.get("name"):
            return _fmt_id_name(value)
    return _join_multivalued(value)


def _resolve_cell(record, kind, slot):
    """One cell: the record's slot value rendered per its schema-derived kind."""
    v = record.get(slot)
    if v is None:
        return ""
    if kind == "qty_value":
        return _fmt_value_unit(v)[0] if isinstance(v, dict) else _fmt_cell(v)
    if kind == "qty_unit":
        return _fmt_value_unit(v)[1] if isinstance(v, dict) else ""
    if kind == "qty_min":
        # min_value/max_value are themselves QuantityValue objects in the
        # schema, so the bound may arrive as {'value': '4'} rather than 4
        return _fmt_cell(_get_nested(v, "min_value")) if isinstance(v, dict) else _fmt_cell(v)
    if kind == "qty_max":
        return _fmt_cell(_get_nested(v, "max_value")) if isinstance(v, dict) else ""
    if kind == "term_label":
        if isinstance(v, dict):
            return v.get("name") or v.get("id") or ""
        return _fmt_cell(v)
    if kind == "term_id":
        return _get_nested(v, "id") if isinstance(v, dict) else ""
    if kind == "ref":
        # keep the referenced id so the column joins against the target tab;
        # an inlined object with no id still shows its name
        if isinstance(v, dict):
            return v.get("id") or _fmt_id_name(v)
        return _fmt_cell(v)
    if kind == "ref_list":
        return _fmt_list_refs(v)
    if kind == "term_list":
        if isinstance(v, list):
            return "; ".join(
                _fmt_id_name(x) if isinstance(x, dict) else str(x) for x in v
            )
        return _fmt_cell(v)
    return _fmt_cell(v)


def _row_for_tab(record, tab):
    """Build one row for a schema-derived tab."""
    return tuple(_resolve_cell(record, kind, slot) for _, kind, slot in _TAB_SPECS[tab])


def _tab_for_headers(headers):
    """Recover the tab a header list belongs to (same object or equal list)."""
    for tab, cols in HEADERS.items():
        if cols is headers or cols == headers:
            return tab
    return None


def _protocol_row(p):
    return _row_for_tab(p, "Protocol")


def _exposure_row(ec):
    return _row_for_tab(ec, "ExposureCondition")


def _key_event_row(ke):
    return _row_for_tab(ke, "KeyEvent")


def _subject_row(subj, tab):
    return _row_for_tab(subj, tab)


def _cellular_system_row(subj):
    return _row_for_tab(subj, "CellularSystem")


def _invivo_subject_row(subj):
    return _row_for_tab(subj, "InVivoSubject")


def _response_comparison_row(rc):
    return _row_for_tab(rc, "ResponseComparison")


def _key_event_relationship_row(ker):
    return _row_for_tab(ker, "KeyEventRelationship")


def _generic_row(record, headers):
    """Header-name-driven fallback for a header list no schema tab owns."""
    row = []
    for h in headers:
        if h.endswith("_value") and h not in record:
            row.append(_get_nested(record, h[: -len("_value")], "value"))
        elif h.endswith("_unit") and h not in record:
            unit_obj = _get_nested(record, h[: -len("_unit")], "unit")
            if isinstance(unit_obj, dict):
                row.append(_fmt_id_name(unit_obj))
            else:
                row.append(str(unit_obj) if unit_obj else "")
        elif h.endswith("_id") and h not in record:
            row.append(_get_nested(record, h[: -len("_id")], "id"))
        else:
            row.append(_fmt_cell(record.get(h, "")))
    return tuple(row)


def _assay_row(assay, assay_headers):
    """Build an assay row for the tab the header list belongs to."""
    tab = _tab_for_headers(assay_headers)
    if tab is not None:
        return _row_for_tab(assay, tab)
    return _generic_row(assay, assay_headers)


def _output_row(output, output_headers):
    """Build an output row for the tab the header list belongs to."""
    tab = _tab_for_headers(output_headers)
    if tab is not None:
        return _row_for_tab(output, tab)
    return _generic_row(output, output_headers)


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def yaml_to_excel(input_path, output_path, template_path=None):
    """Convert a SOMA YAML file to an Excel workbook."""
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Load YAML
    with open(input_path) as f:
        data = yaml.safe_load(f)

    if not data:
        print(f"Error: {input_path} is empty or invalid YAML", file=sys.stderr)
        sys.exit(1)

    # Create workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # --- Metadata tab ---
    meta_rows = _extract_metadata(input_path)
    if len(meta_rows) > 1:  # more than just the header
        ws = wb.create_sheet("Metadata")
        ws.sheet_properties.tabColor = TAB_COLORS.get("Metadata", "4472C4")
        for i, row in enumerate(meta_rows, 1):
            for j, val in enumerate(row, 1):
                cell = ws.cell(row=i, column=j, value=val)
                cell.alignment = WRAP
                cell.border = THIN_BORDER
                if i == 1:
                    cell.font = HEADER_FONT
                    cell.fill = HEADER_FILL
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 80

    # --- Protocol tab (top-level and inlined on assays) ---
    protocols = _collect_protocols(data)
    if protocols:
        _make_sheet(
            wb, "Protocol", HEADERS["Protocol"],
            [_protocol_row(p) for p in protocols],
            tab_color=TAB_COLORS.get("Protocol"),
        )

    # --- ExposureCondition tab ---
    exposures = _collect_exposure_conditions(data)
    if exposures:
        _make_sheet(
            wb, "ExposureCondition", HEADERS["ExposureCondition"],
            [_exposure_row(ec) for ec in exposures],
            tab_color=TAB_COLORS.get("ExposureCondition"),
        )

    # --- KeyEvent tab ---
    key_events = _collect_key_events(data)
    if key_events:
        _make_sheet(
            wb, "KeyEvent", HEADERS["KeyEvent"],
            [_key_event_row(ke) for ke in key_events],
            tab_color=TAB_COLORS.get("KeyEvent"),
        )

    # --- Study-subject tabs (one per concrete StudySubject class) ---
    for subj_tab, subjects in _collect_subjects(data).items():
        if subjects:
            _make_sheet(
                wb, subj_tab, HEADERS[subj_tab],
                [_subject_row(s, subj_tab) for s in subjects],
                tab_color=TAB_COLORS.get(subj_tab),
            )

    # --- Assay + Output tabs ---
    for coll_key, (assay_tab, output_tab) in COLLECTION_MAP.items():
        assays = data.get(coll_key, []) or []
        if not assays:
            continue

        assay_headers = HEADERS.get(assay_tab, [])
        output_headers = HEADERS.get(output_tab, [])

        # Build assay rows
        assay_rows = [_assay_row(a, assay_headers) for a in assays]
        _make_sheet(
            wb, assay_tab, assay_headers, assay_rows,
            tab_color=TAB_COLORS.get(assay_tab),
        )

        # Build output rows from has_specified_output
        # (multivalued: one output record per experimental condition/group)
        output_rows = []
        for a in assays:
            for out in _iter_outputs(a):
                # Add source_assay reference
                out_with_ref = dict(out)
                if "source_assay" not in out_with_ref:
                    out_with_ref["source_assay"] = a.get("id", "")
                output_rows.append(_output_row(out_with_ref, output_headers))

        if output_rows:
            _make_sheet(
                wb, output_tab, output_headers, output_rows,
                tab_color=TAB_COLORS.get(output_tab),
            )

    # --- Responses tab (long format: one row per condition x measurement) ---
    response_rows = _collect_response_rows(data)
    if response_rows:
        _make_sheet(
            wb, "Responses", HEADERS["Responses"], response_rows,
            tab_color=TAB_COLORS.get("Responses"),
        )

    # --- ResponseComparison tab (analysis layer: change vs. control) ---
    comparisons = data.get("response_comparisons", []) or []
    if comparisons:
        _make_sheet(
            wb, "ResponseComparison", HEADERS["ResponseComparison"],
            [_response_comparison_row(rc) for rc in comparisons],
            tab_color=TAB_COLORS.get("ResponseComparison"),
        )

    # --- KeyEventRelationship tab (container-level AOP network topology) ---
    kers = data.get("key_event_relationships", []) or []
    if kers:
        _make_sheet(
            wb, "KeyEventRelationship", HEADERS["KeyEventRelationship"],
            [_key_event_relationship_row(ker) for ker in kers],
            tab_color=TAB_COLORS.get("KeyEventRelationship"),
        )

    # --- AdverseOutcomePathway tab ---
    aops = data.get("adverse_outcome_pathways", []) or []
    if aops:
        _make_sheet(
            wb, "AdverseOutcomePathway", HEADERS["AdverseOutcomePathway"],
            [_row_for_tab(a, "AdverseOutcomePathway") for a in aops],
            tab_color=TAB_COLORS.get("AdverseOutcomePathway"),
        )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert SOMA YAML to formatted Excel workbook"
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to SOMA Container YAML file",
    )
    parser.add_argument(
        "--output", "-o", required=True,
        help="Path for output Excel file",
    )
    parser.add_argument(
        "--template", "-t", default=None,
        help="Path to LinkML-generated Excel scaffold (default: project/excel/soma.xlsx)",
    )
    args = parser.parse_args()
    yaml_to_excel(args.input, args.output, args.template)


if __name__ == "__main__":
    main()
