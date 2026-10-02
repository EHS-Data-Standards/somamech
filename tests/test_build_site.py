"""Tests for the KB review-site generator (scripts/build_site.py)."""
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "scripts" / "build_site.py"
VALID = ROOT / "tests" / "data" / "valid"


def run(*args):
    return subprocess.run(
        ["uv", "run", "python", str(SCRIPT), *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def build(tmp_path, *files, version=None):
    kb = tmp_path / "kb"
    kb.mkdir()
    for f in files:
        shutil.copy(VALID / f, kb)
    out = tmp_path / "site"
    args = ["--kb-dir", str(kb), "--out", str(out)]
    if version:
        args += ["--version", version]
    result = run(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    return out


def test_builds_index_network_and_one_page_per_paper(tmp_path):
    out = build(tmp_path, "Container-liu2024-pm25-cftr.yaml",
                "Container-montgomery2020-pm25-mucociliary.yaml")
    assert (out / "index.html").exists()
    assert (out / "key-events.html").exists()
    assert (out / "assets" / "site.css").exists()
    pages = sorted(p.name for p in (out / "publications").glob("*.html"))
    assert pages == ["liu2024-pm25-cftr.html", "montgomery2020-pm25-mucociliary.html"]


def test_publication_page_quotes_evidence_and_links_sources(tmp_path):
    out = build(tmp_path, "Container-liu2024-pm25-cftr.yaml")
    page = (out / "publications" / "liu2024-pm25-cftr.html").read_text()
    # evidence snippets are rendered as quotes with their PubMed reference
    assert "snippet" in page
    assert "pubmed.ncbi.nlm.nih.gov" in page
    # the page links back to the YAML source of truth
    assert "kb/publications/Container-liu2024-pm25-cftr.yaml" in page


def test_key_event_network_pools_papers(tmp_path):
    out = build(tmp_path, "Container-liu2024-pm25-cftr.yaml",
                "Container-montgomery2020-pm25-mucociliary.yaml")
    page = (out / "key-events.html").read_text()
    assert "<svg" in page           # network rendered
    assert "liu2024" in page        # paper cross-links present
    assert "montgomery2020" in page


def test_toplevel_key_events_render_with_evidence_and_any_level_builds(tmp_path):
    """Two regressions from PR #172 review: evidence under a top-level
    key_events: block was counted but never rendered, and a schema-valid
    level_of_biological_organization missing from LEVEL_ORDER (population)
    crashed the whole network build instead of degrading."""
    kb = tmp_path / "kb"
    kb.mkdir()
    src = (VALID / "Container-liu2024-pm25-cftr.yaml").read_text()
    assert "\nkey_events:" not in src
    (kb / "Container-liu2024-pm25-cftr.yaml").write_text(src + """
key_events:
  - id: "KE:test-population-morbidity"
    name: "Increased respiratory morbidity"
    level_of_biological_organization: population
    biological_action: increased
    evidence:
      - reference: "PMID:38880065"
        supports: REFUTE
        snippet: "A deliberately recorded negative finding."
  - id: "KE:test-future-enum-level"
    name: "Future enum value"
    level_of_biological_organization: some_future_level
""")
    out = tmp_path / "site"
    result = run("--kb-dir", str(kb), "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr

    page = (out / "publications" / "liu2024-pm25-cftr.html").read_text()
    assert 'id="key-events"' in page
    assert "Increased respiratory morbidity" in page
    assert "A deliberately recorded negative finding." in page
    assert "REFUTE" in page

    network = (out / "key-events.html").read_text()
    assert "population" in network              # column/level rendered
    assert "Future enum value" in network       # unknown level degraded, not crashed


def test_version_is_stamped_into_footer_and_source_links(tmp_path):
    out = build(tmp_path, "Container-liu2024-pm25-cftr.yaml", version="v1.2.3")
    index = (out / "index.html").read_text()
    assert "v1.2.3" in index
    page = (out / "publications" / "liu2024-pm25-cftr.html").read_text()
    assert "/blob/v1.2.3/kb/publications/" in page


def test_html_escapes_yaml_content(tmp_path):
    kb = tmp_path / "kb"
    kb.mkdir()
    src = (VALID / "Container-liu2024-pm25-cftr.yaml").read_text()
    assert 'reference_title: "' in src
    (kb / "Container-evil.yaml").write_text(src.replace(
        'reference_title: "', 'reference_title: "<script>alert(1)</script> '))
    out = tmp_path / "site"
    result = run("--kb-dir", str(kb), "--out", str(out))
    assert result.returncode == 0, result.stdout + result.stderr
    index = (out / "index.html").read_text()
    assert "<script>alert(1)</script>" not in index
    assert "&lt;script&gt;" in index
    for page in (out / "publications").glob("*.html"):
        assert "<script>alert(1)</script>" not in page.read_text()
