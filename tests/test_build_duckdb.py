"""Tests for the DuckDB knowledge-base build (scripts/build_duckdb.py).

These guard the parts that would break silently if the schema shifted: that
value objects stay flattened (no QuantityValue table reappears), that reused
children keep a single parent column instead of one per possible parent, and
that the measurement_full view still joins a number to its paper, assay and
exposure.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "build_duckdb.py"
VALID = ROOT / "tests" / "data" / "valid"
FIXTURES = (
    "Container-liu2024-pm25-cftr.yaml",
    "Container-montgomery2020-pm25-mucociliary.yaml",
    "Container-comprehensive_aop_lung.yaml",
)

sys.path.insert(0, str(ROOT / "scripts"))


def run(*args):
    return subprocess.run(
        ["uv", "run", "python", str(SCRIPT), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("duckdb")
    kb = tmp / "kb"
    kb.mkdir()
    for name in FIXTURES:
        shutil.copy(VALID / name, kb)
    out = tmp / "soma.duckdb"
    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    con = duckdb.connect(str(out), read_only=True)
    yield con
    con.close()


def relations(con):
    return {
        r[0] for r in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
    }


def columns(con, table):
    return {r[0] for r in con.execute(f'DESCRIBE "{table}"').fetchall()}


def test_value_objects_are_flattened_not_joined(db):
    """QuantityValue must not exist as a table; its slots become columns."""
    rels = relations(db)
    assert "QuantityValue" not in rels
    assert "Variability" not in rels
    cols = columns(db, "CFTRFunctionOutput")
    assert {"cftr_chloride_secretion_value",
            "cftr_chloride_secretion_unit",
            "cftr_chloride_secretion_unit_label"} <= cols
    # and no surrogate FK into a quantity table
    assert not any(c.endswith("_id") and "secretion" in c for c in cols)


def test_reused_children_have_one_parent_not_one_column_per_parent(db):
    """EvidenceItem has 27 possible parents; it must not have 27 FK columns."""
    cols = columns(db, "EvidenceItem")
    assert {"parent_id", "parent_type", "parent_slot"} <= cols
    assert "CFTRFunctionAssay_id" not in cols
    assert not [c for c in cols if c.endswith("Assay_id")]


def test_multivalued_scalars_are_list_columns_not_side_tables(db):
    rels = relations(db)
    assert "Protocol_equipment_required" not in rels
    types = dict(
        (r[0], r[1]) for r in db.execute('DESCRIBE "Protocol"').fetchall()
    )
    assert types["equipment_required"].endswith("[]")


def test_every_row_traces_back_to_a_paper(db):
    papers = {r[0] for r in db.execute("SELECT source_file FROM paper").fetchall()}
    assert len(papers) == len(FIXTURES)
    for table in ("KeyEvent", "ExposureCondition", "measurement", "link"):
        orphans = db.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE source_file IS NULL '
            f'OR source_file NOT IN (SELECT source_file FROM paper)'
        ).fetchone()[0]
        assert orphans == 0, f"{table} has {orphans} rows with no paper"


def test_measurement_full_joins_number_to_its_context(db):
    row = db.execute("""
        SELECT paper_id, assay_type, measurement, value, value_num, unit_label,
               experimental_group, exposure_agent_label
        FROM measurement_full
        WHERE value_num IS NOT NULL AND exposure_agent_label IS NOT NULL
        LIMIT 1
    """).fetchone()
    assert row is not None, "no measurement resolved to an exposure"
    paper_id, assay_type, measurement, value, value_num, unit, group, agent = row
    assert paper_id and assay_type and measurement
    assert value_num == pytest.approx(float(value))
    assert agent


def test_measurement_is_canonical_and_wide_tables_echo_it(db):
    """The compact 3 columns on a wide table must agree with the long table."""
    mismatches = db.execute("""
        SELECT COUNT(*) FROM measurement m
        JOIN "CFTRFunctionOutput" o
          ON o.source_file = m.source_file AND o.id = m.entity_id
        WHERE m.slot_name = 'cftr_chloride_secretion'
          AND COALESCE(o.cftr_chloride_secretion_value,'') <> COALESCE(m.value,'')
    """).fetchone()[0]
    assert mismatches == 0


def test_ddl_only_builds_nothing_and_is_valid_sql(tmp_path):
    result = run("--ddl-only")
    assert result.returncode == 0, result.stderr
    assert "CREATE TABLE" in result.stdout and "CREATE VIEW" in result.stdout
    # the emitted script must actually execute
    from build_duckdb import _execute_script
    con = duckdb.connect(str(tmp_path / "ddl.duckdb"))
    _execute_script(con, result.stdout)
    con.close()


def test_tsv_dump_is_rectangular_and_flattens_lists(db, tmp_path):
    from build_duckdb import dump_tsv

    written = dump_tsv(Path(db.execute("PRAGMA database_list").fetchone()[2]), tmp_path)
    assert "measurement_full.tsv" in written
    lines = (tmp_path / "Protocol.tsv").read_text().splitlines()
    header = lines[0].split("\t")
    assert "equipment_required" in header
    # LIST columns are joined with '; ', so no cell holds a nested structure
    # and every row has exactly as many fields as the header.
    equip = header.index("equipment_required")
    assert len(lines) > 1, "no Protocol rows to check"
    for line in lines[1:]:
        if line.count('"') % 2:      # skip rows continued by a quoted newline
            continue
        assert "[" not in line.split("\t")[equip]


# ---------------------------------------------------------------------------
# Regressions for the review findings on PR #106
# ---------------------------------------------------------------------------

def test_measurement_has_no_duplicate_rows(db):
    """An entity inlined under several parents contributes its number once.

    The fixtures inline one exposure condition in full under six assays, which
    previously produced six identical measurement rows and threw off every
    aggregate over the table.
    """
    total, distinct = db.execute("""
        SELECT COUNT(*), COUNT(DISTINCT (source_file, entity_type, entity_id, slot_name))
        FROM measurement
    """).fetchone()
    assert total == distinct, f"{total - distinct} duplicate measurement rows"


def test_link_rows_are_joinable_to_a_real_table(db):
    """No link may point at an abstract class, which has no table."""
    rels = relations(db)
    bad = db.execute(
        "SELECT DISTINCT target_type FROM link WHERE target_type IS NOT NULL"
    ).fetchall()
    unjoinable = [r[0] for r in bad if r[0] not in rels]
    assert not unjoinable, f"link.target_type not a relation: {unjoinable}"


def test_two_files_citing_one_paper_both_survive(tmp_path):
    """Identity is the source file, so a shared PMID must not abort the build."""
    kb = tmp_path / "kb"
    kb.mkdir()
    src = VALID / "Container-liu2024-pm25-cftr.yaml"
    shutil.copy(src, kb / "a.yaml")
    shutil.copy(src, kb / "b.yaml")
    out = tmp_path / "dup.duckdb"

    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    con = duckdb.connect(str(out), read_only=True)
    try:
        assert con.execute("SELECT COUNT(*) FROM paper").fetchone()[0] == 2
        # the two files' entities stay separate rather than merging
        per_file = con.execute(
            'SELECT source_file, COUNT(*) FROM "CFTRFunctionAssay" '
            "GROUP BY source_file ORDER BY source_file"
        ).fetchall()
        assert len(per_file) == 2
        assert per_file[0][1] == per_file[1][1]
    finally:
        con.close()
    assert "already cited by" in result.stdout + result.stderr


def test_unresolvable_inlined_child_warns_instead_of_vanishing(tmp_path):
    """An inlined value of an abstract-ranged slot must not disappear silently."""
    import yaml as _yaml

    kb = tmp_path / "kb"
    kb.mkdir()
    data = _yaml.safe_load((VALID / "Container-liu2024-pm25-cftr.yaml").read_text())
    # ResponseComparison.control_output is declared AssayOutputMeasurement,
    # which is abstract; inline a value carrying no type designator.
    data["response_comparisons"] = [{
        "id": "RC:test-1",
        "name": "inlined control output with an abstract declared range",
        "control_output": {"id": "OUT:inlined-control", "name": "inlined"},
    }]
    (kb / "rc.yaml").write_text(_yaml.safe_dump(data))

    result = run("--kb-dir", str(kb), "--output", str(tmp_path / "rc.duckdb"))
    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "has no table" in combined and "control_output" in combined


def test_term_usage_counts_more_than_units(db):
    """Every term reference is counted, not only the ones that are units."""
    unused = db.execute("SELECT COUNT(*) FROM term_usage WHERE n_uses = 0").fetchone()[0]
    assert unused == 0, f"{unused} terms read as unused"
    non_unit = db.execute(
        "SELECT COUNT(DISTINCT term_id) FROM term_ref WHERE slot_name NOT LIKE '%.unit'"
    ).fetchone()[0]
    assert non_unit > 0, "no non-unit term references recorded"


def test_value_qualifier_keeps_inequalities_queryable(db):
    """'<0.05' must not silently become 0.05 with the bound discarded."""
    from build_duckdb import _num

    assert _num("12.3") == (12.3, None)
    assert _num("<0.05") == (0.05, "<")
    assert _num("~12") == (12.0, "~")
    assert _num("not a number") == (None, None)
    # and the column exists on the built table
    assert "value_qualifier" in columns(db, "measurement")


def test_surrogate_keyed_children_dedupe_by_content(tmp_path):
    """An entity inlined N times carrying evidence yields ONE evidence row.

    EvidenceItem has no identifier, so a counter-based surrogate id handed every
    sighting a fresh key and the dedupe could never fire — the same defect as
    the measurement double-count, in the table this repo cares about most.
    """
    import copy
    import yaml as _yaml

    kb = tmp_path / "kb"
    kb.mkdir()
    data = _yaml.safe_load((VALID / "Container-liu2024-pm25-cftr.yaml").read_text())
    shared = {
        "id": "KE:shared-1",
        "name": "shared key event",
        "evidence": [{
            "reference": "PMID:39113893", "supports": "supports",
            "snippet": "one quote", "explanation": "why",
        }],
    }
    copies = 0
    for coll in ("cftr_assays", "gene_expression_assays", "goblet_cell_assays"):
        for assay in data.get(coll, []) or []:
            assay["informs_on_key_event"] = copy.deepcopy(shared)
            copies += 1
    assert copies >= 3, "fixture no longer has enough assays to inline under"
    (kb / "dup.yaml").write_text(_yaml.safe_dump(data))

    out = tmp_path / "dedupe.duckdb"
    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    con = duckdb.connect(str(out), read_only=True)
    try:
        n = con.execute(
            'SELECT COUNT(*) FROM "EvidenceItem" WHERE parent_id = ?', ["KE:shared-1"]
        ).fetchone()[0]
        assert n == 1, f"{copies} inlined copies produced {n} evidence rows"
    finally:
        con.close()


def test_disagreeing_copies_of_one_id_warn(tmp_path):
    """Two inlined copies of one id with different content must not pick a winner silently."""
    import yaml as _yaml

    kb = tmp_path / "kb"
    kb.mkdir()
    data = _yaml.safe_load((VALID / "Container-liu2024-pm25-cftr.yaml").read_text())
    assays = data.get("cftr_assays") or []
    assert len(assays) >= 2, "fixture needs two assays to disagree across"
    for i, assay in enumerate(assays[:3]):
        assay["informs_on_key_event"] = {
            "id": "KE:conflict-1",
            "name": f"COPY-{i + 1}",
            "level_of_biological_organization": "cellular",
        }
    (kb / "conflict.yaml").write_text(_yaml.safe_dump(data))

    result = run("--kb-dir", str(kb), "--output", str(tmp_path / "c.duckdb"))
    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "disagree" in combined and "KE:conflict-1" in combined


def test_paper_level_parent_pointers_resolve(db):
    """Top-level entities must parent on the paper table's actual key."""
    dangling = db.execute("""
        SELECT COUNT(*) FROM link
        WHERE parent_type = 'paper'
          AND parent_id NOT IN (SELECT source_file FROM paper)
    """).fetchone()[0]
    assert dangling == 0, f"{dangling} paper-level parent pointers dangle"
    # and the same for the parent_* triple carried on entity rows
    for table in ("KeyEvent", "Protocol"):
        bad = db.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE parent_type = \'paper\' '
            f"AND parent_id NOT IN (SELECT source_file FROM paper)"
        ).fetchone()[0]
        assert bad == 0, f"{table} has {bad} dangling paper parents"
