#!/usr/bin/env python3
"""Schema-driven mapping from the SOMA LinkML schema to a relational DuckDB model.

This module holds the *mapping rules* only: which LinkML classes become tables,
which become flattened columns, and what each column is called. The loader
(build_duckdb.py) and the DDL emitter both read their answers from here, so the
schema is interpreted in exactly one place.

Why not just use `gen-sqltables` output verbatim? Three of its choices make the
result hard to query and unusable in a spreadsheet:

  * `QuantityValue` has no identifier, so LinkML gives it a surrogate integer PK
    and a shared table. 114 columns across the schema are FKs into it, meaning
    every single number in the KB costs a join. Here those slots are FLATTENED
    into `<slot>_value` / `<slot>_unit` / `<slot>_unit_label` columns, and the
    full detail (dispersion, n, central tendency) lands in the long
    `measurement` table.
  * Reused child classes get one nullable FK column per possible parent:
    `EvidenceItem` has 27, `Protocol` 18, `ExposureCondition` 12. The walker
    always knows the real parent, so children carry a single
    `parent_id`/`parent_type`/`parent_slot` triple instead.
  * Multivalued scalars get their own side table (13 of them). DuckDB has native
    LIST columns, so they stay on the parent row as `VARCHAR[]`.

Everything else follows the schema: one table per concrete class, natural `id`
primary keys, and ontology term references flattened to a curie + label pair
(with a `term` dimension table collecting every term the KB uses).
"""
from __future__ import annotations

from linkml_runtime import SchemaView

# Value objects with no identifier: flattened inline, never their own table.
QUANTITY_CLASSES = {"QuantityValue", "QuantityRange", "Variability"}

# Ontology term stubs ({id, name}): flattened to `<slot>` + `<slot>_label`.
# They keep their identifiers, so every term also lands in the `term` table.
TERM_CLASSES = {
    "Unit",
    "NamedEntity",
    "CellTypeReference",
    "SpeciesReference",
    "ChemicalEntityReference",
    "AnatomicalEntityReference",
}

# The tree root becomes the `paper` table (one row per source YAML file).
ROOT_CLASS = "Container"
PAPER_TABLE = "paper"

# Stamped on every row so any table can be traced back to its paper.
PROVENANCE_COLUMNS = [("paper_id", "VARCHAR"), ("source_file", "VARCHAR")]

# Stamped on rows that are inlined children of another entity.
PARENT_COLUMNS = [
    ("parent_id", "VARCHAR"),
    ("parent_type", "VARCHAR"),
    ("parent_slot", "VARCHAR"),
]

TYPE_MAP = {
    "string": "VARCHAR",
    "uriorcurie": "VARCHAR",
    "uri": "VARCHAR",
    "curie": "VARCHAR",
    "ncname": "VARCHAR",
    "integer": "BIGINT",
    "float": "DOUBLE",
    "double": "DOUBLE",
    "decimal": "DOUBLE",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP",
    "time": "TIME",
}


def load_schema(schema_path: str) -> SchemaView:
    return SchemaView(schema_path)


def sql_type(sv: SchemaView, range_name: str | None) -> str:
    """DuckDB type for a LinkML type or enum range."""
    if range_name is None:
        return "VARCHAR"
    if range_name in sv.all_enums():
        return "VARCHAR"
    t = sv.all_types().get(range_name)
    while t is not None:
        base = (t.uri or "").split(":")[-1].lower()
        if t.name in TYPE_MAP:
            return TYPE_MAP[t.name]
        if base in TYPE_MAP:
            return TYPE_MAP[base]
        t = sv.all_types().get(t.typeof) if t.typeof else None
    return TYPE_MAP.get(range_name, "VARCHAR")


def is_entity(sv: SchemaView, range_name: str | None) -> bool:
    """A class that becomes its own table."""
    return (
        range_name in sv.all_classes()
        and range_name not in QUANTITY_CLASSES
        and range_name not in TERM_CLASSES
    )


def _cache(sv: SchemaView) -> dict:
    """Per-SchemaView memo store.

    Kept on the view itself rather than in a module-level dict keyed by
    `id(sv)`: a global would either leak every view it ever saw or, once one
    was released, serve a recycled id's answers for a different schema.
    """
    store = getattr(sv, "_soma_duckdb_cache", None)
    if store is None:
        store = {}
        sv._soma_duckdb_cache = store
    return store


def designator_slot(sv: SchemaView, cls: str) -> str | None:
    """The slot whose value names the concrete class, if the schema declares one."""
    memo = _cache(sv).setdefault("designator", {})
    if cls not in memo:
        memo[cls] = next(
            (s.name for s in sv.class_induced_slots(cls) if s.designates_type), None
        )
    return memo[cls]


def concrete_class(sv: SchemaView, declared: str, obj: dict) -> str:
    """Resolve the real class of `obj`, honouring `designates_type: true`.

    `study_subject` is declared as StudySubject but instances are CellularSystem,
    InVivoSubject or PopulationSubject; `follows_protocols` is declared Protocol
    but instances are ImagingProtocol, StainingProtocol, and so on.
    """
    slot = designator_slot(sv, declared)
    if slot:
        value = obj.get(slot)
        if value and value in sv.all_classes():
            return value
    return declared


def table_classes(sv: SchemaView) -> frozenset[str]:
    """Concrete classes that become tables, excluding the root and flattened ones.

    Memoized: the walker asks this for every node it visits, and computing it
    sorts all classes and induces slots on each.
    """
    memo = _cache(sv)
    if "table_classes" in memo:
        return memo["table_classes"]
    out = []
    for name, cls in sv.all_classes().items():
        if cls.abstract or name == ROOT_CLASS:
            continue
        if name in QUANTITY_CLASSES or name in TERM_CLASSES:
            continue
        # A class with no identifier still needs a table (EvidenceItem,
        # PublicationReference); it is keyed by a surrogate id instead.
        out.append(name)
    memo["table_classes"] = frozenset(out)
    return memo["table_classes"]


def has_natural_key(sv: SchemaView, cls: str) -> bool:
    return bool([s for s in sv.class_induced_slots(cls) if s.identifier])


def columns_for(sv: SchemaView, cls: str) -> list[tuple[str, str]]:
    """Column list for a class's table, in declaration order.

    Returns (column_name, duckdb_type) pairs, excluding provenance/parent
    columns which the DDL emitter adds.
    """
    cols: list[tuple[str, str]] = []
    if not has_natural_key(sv, cls):
        # Surrogate ids are strings ("EvidenceItem-3"): one counter serves every
        # surrogate-keyed class, so ids stay unique across tables.
        cols.append(("id", "VARCHAR"))
    for s in sv.class_induced_slots(cls):
        rng = s.range
        if s.designates_type:
            cols.append((s.name, "VARCHAR"))
            continue
        if is_entity(sv, rng):
            if s.multivalued:
                continue  # children live in their own table via parent_id
            cols.append((f"{s.name}_id", "VARCHAR"))
            continue
        if rng in QUANTITY_CLASSES:
            if s.multivalued:
                continue  # no multivalued quantities in this schema
            cols.extend(_quantity_columns(s.name, rng))
            continue
        if rng in TERM_CLASSES:
            if s.multivalued:
                cols.append((s.name, "VARCHAR[]"))
                cols.append((f"{s.name}_labels", "VARCHAR[]"))
            else:
                cols.append((s.name, "VARCHAR"))
                cols.append((f"{s.name}_label", "VARCHAR"))
            continue
        # plain type or enum
        base = sql_type(sv, rng)
        cols.append((s.name, f"{base}[]" if s.multivalued else base))
    return cols


def _quantity_columns(prefix: str, rng: str) -> list[tuple[str, str]]:
    """Compact flattening of a value object: enough to read and filter.

    Dispersion, sample size and central tendency are deliberately NOT here —
    they would triple the width of already-sparse tables. They live in the long
    `measurement` table, which carries the full detail for every number.
    """
    if rng == "QuantityRange":
        return [
            (f"{prefix}_min_value", "VARCHAR"),
            (f"{prefix}_max_value", "VARCHAR"),
            (f"{prefix}_unit", "VARCHAR"),
            (f"{prefix}_unit_label", "VARCHAR"),
        ]
    return [
        (f"{prefix}_value", "VARCHAR"),
        (f"{prefix}_unit", "VARCHAR"),
        (f"{prefix}_unit_label", "VARCHAR"),
    ]


def quantity_slots(sv: SchemaView, cls: str) -> list[str]:
    """Names of the single-valued value-object slots on a class."""
    return [
        s.name
        for s in sv.class_induced_slots(cls)
        if s.range in QUANTITY_CLASSES and not s.multivalued
    ]
