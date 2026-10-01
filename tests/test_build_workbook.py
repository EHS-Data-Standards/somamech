"""Tests for the pooled-workbook generator (scripts/build_workbook.py)."""
import shutil
import subprocess
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "build_workbook.py"
VALID = ROOT / "tests" / "data" / "valid"


def run(*args):
    return subprocess.run(
        ["uv", "run", "python", str(SCRIPT), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_pools_multiple_papers_into_one_workbook(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(VALID / "Container-liu2024-pm25-cftr.yaml", kb)
    shutil.copy(VALID / "Container-montgomery2020-pm25-mucociliary.yaml", kb)
    out = tmp_path / "pooled.xlsx"

    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    assert out.exists()

    wb = openpyxl.load_workbook(out)
    assert "Papers" in wb.sheetnames
    assert wb["Papers"].max_row - 1 == 2  # one row per paper
    # every data tab's first column names the source paper
    for ws in wb.worksheets:
        assert ws.cell(1, 1).value == "source_publication"
    # rows from both papers land in the same GeneExpressionAssay tab
    sources = {r[0] for r in wb["GeneExpressionAssay"].iter_rows(min_row=2, values_only=True)}
    assert len(sources) == 2


def test_output_rows_are_emitted_for_list_valued_outputs(tmp_path):
    """Regression for #109: has_specified_output is a list in every kb file,
    but the pooled builder only accepted a bare dict, so *Output tabs were
    always empty and check-entity-ids never saw an output ID."""
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(VALID / "Container-liu2024-pm25-cftr.yaml", kb)
    out = tmp_path / "pooled.xlsx"

    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    wb = openpyxl.load_workbook(out)
    assert "CFTRFunctionOutput" in wb.sheetnames
    output_rows = list(wb["CFTRFunctionOutput"].iter_rows(min_row=2, values_only=True))
    assert len(output_rows) > 0
    # every output row carries a source paper and a non-empty id
    header = [c.value for c in wb["CFTRFunctionOutput"][1]]
    id_col = header.index("id")
    for row in output_rows:
        assert row[0] == "PMID:39113893"
        assert row[id_col]


def test_output_row_legacy_bare_dict_still_accepted(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    (kb / "legacy.yaml").write_text(
        """\
source_publication:
  reference: "PMID:11111111"
cftr_assays:
  - id: "ASSAY:legacy-cftr"
    has_specified_output:
      id: "CFTR:legacy-output"
      name: "Legacy single-dict output"
"""
    )
    out = tmp_path / "pooled.xlsx"

    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    wb = openpyxl.load_workbook(out)
    rows = list(wb["CFTRFunctionOutput"].iter_rows(min_row=2, values_only=True))
    assert len(rows) == 1


def test_duplicate_output_id_across_papers_is_an_error(tmp_path):
    """Output IDs now take part in the cross-paper uniqueness check."""
    kb = tmp_path / "kb"
    kb.mkdir()
    yaml_text = """\
source_publication:
  reference: "{pmid}"
cftr_assays:
  - id: "ASSAY:{tag}-cftr"
    has_specified_output:
      - id: "CFTR:shared-output-id"
"""
    (kb / "a.yaml").write_text(yaml_text.format(pmid="PMID:11111111", tag="a"))
    (kb / "b.yaml").write_text(yaml_text.format(pmid="PMID:22222222", tag="b"))

    result = run("--kb-dir", str(kb), "--check-only")
    assert result.returncode != 0
    assert "CFTR:shared-output-id" in result.stderr


def test_cross_paper_id_collision_fails(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    original = (VALID / "Container-liu2024-pm25-cftr.yaml").read_text()
    (kb / "a.yaml").write_text(original)
    # same content, different declared paper -> every shared assay id collides
    (kb / "b.yaml").write_text(original.replace("PMID:39113893", "PMID:99999999"))

    result = run("--kb-dir", str(kb), "--check-only")
    assert result.returncode != 0
    assert "must be unique to one paper" in result.stderr


def test_empty_kb_dir_is_fine(tmp_path):
    result = run("--kb-dir", str(tmp_path), "--check-only")
    assert result.returncode == 0, result.stdout + result.stderr


def test_review_only_paper_contributes_key_events_and_relationships(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    shutil.copy(ROOT / "kb" / "publications" / "Container-liu2012-shs-mcc.yaml", kb)
    out = tmp_path / "pooled.xlsx"

    result = run("--kb-dir", str(kb), "--output", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    wb = openpyxl.load_workbook(out)

    assert "KeyEventRelationship" in wb.sheetnames
    ker_sources = {
        row[0]
        for row in wb["KeyEventRelationship"].iter_rows(min_row=2, values_only=True)
        if row and row[0]
    }
    assert "PMID:22973232" in ker_sources

    ke_sources = {
        row[0]
        for row in wb["KeyEvent"].iter_rows(min_row=2, values_only=True)
        if row and row[0]
    }
    assert "PMID:22973232" in ke_sources
