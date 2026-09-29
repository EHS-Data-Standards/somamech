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
    for name in (
        "Container-liu2024-pm25-cftr.yaml",
        "Container-montgomery2020-pm25-mucociliary.yaml",
        "Container-comprehensive_aop_lung.yaml",
    ):
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
    papers = {r[0] for r in db.execute("SELECT paper_id FROM paper").fetchall()}
    assert len(papers) == 3
    for table in ("KeyEvent", "ExposureCondition", "measurement", "link"):
        orphans = db.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE paper_id IS NULL '
            f'OR paper_id NOT IN (SELECT paper_id FROM paper)'
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
          ON o.paper_id = m.paper_id AND o.id = m.entity_id
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
    text = (tmp_path / "Protocol.tsv").read_text()
    header = text.splitlines()[0].split("\t")
    assert "equipment_required" in header
    # LIST columns are joined, so no row explodes into a nested structure
    assert "[" not in text.split("\n")[1] if len(text.split("\n")) > 1 else True
