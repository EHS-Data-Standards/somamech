"""Regression tests for scripts/snippet_receipts.py (issue #108).

The receipt gate exists for quotes CI cannot see: the committed cache entry
is abstract-only and the quote only resolves in the curator's local full-text
extraction. Issue #108 was the over-broad version of that gate — it demanded
a receipt for EVERY snippet whose cache entry is abstract-only, including
snippets verbatim in the committed abstract, which CI's own reference
validator already checks. For papers with no obtainable PDF this deadlocked:
``check`` demanded a receipt that ``write`` refuses to produce without local
full text, and hand-writing either is fabricated evidence.

These tests pin the fixed semantics:

- a snippet that resolves (whitespace-collapsed, "..."-elided, in-order) in
  the committed cache entry needs no receipt, even when that entry is
  abstract-only — the no-PDF case passes both ``write`` and ``check``;
- a snippet that does NOT resolve there still demands a receipt, ``write``
  still refuses without local full text, and an edited snippet stops
  matching its receipt — the paywalled-PDF tamper protection is unchanged.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent

_spec = importlib.util.spec_from_file_location(
    "snippet_receipts", ROOT / "scripts" / "snippet_receipts.py"
)
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)

PMID = "PMID:99990001"

ABSTRACT = """---
reference_id: PMID:99990001
title: Test paper
content_type: abstract_only
---

## Abstract

Exposure to fine particulate matter significantly decreased ciliary beat
frequency in cultured human airway epithelial cells, and the effect was
concentration dependent across all donors tested.
"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Point the module's directory constants at a throwaway repo layout."""
    refs = tmp_path / "references_cache"
    local = tmp_path / "references_cache_local"
    receipts = tmp_path / "verification"
    refs.mkdir()
    monkeypatch.setattr(sr, "ROOT", tmp_path)
    monkeypatch.setattr(sr, "REFS_CACHE", refs)
    monkeypatch.setattr(sr, "REFS_CACHE_LOCAL", local)
    monkeypatch.setattr(sr, "RECEIPTS_DIR", receipts)
    (refs / "PMID_99990001.md").write_text(ABSTRACT)
    return tmp_path


def kb_file(repo: Path, *snippets: str) -> Path:
    evidence = "\n".join(
        f'  - reference: "{PMID}"\n    snippet: "{s}"' for s in snippets
    )
    path = repo / "Container-test.yaml"
    path.write_text(f"publication:\n  evidence:\n{evidence}\n")
    return path


IN_ABSTRACT = (
    "fine particulate matter significantly decreased ciliary beat "
    "frequency in cultured human airway epithelial cells"
)
NOT_IN_ABSTRACT = "mucociliary clearance was completely abolished at 24 h"


def test_verbatim_abstract_snippet_needs_no_receipt(repo):
    """The issue #108 case: every quote is in the committed abstract."""
    kb = kb_file(repo, IN_ABSTRACT)
    assert sr.abstract_only_snippets(kb) == {}
    # check passes with no verification/ file at all...
    assert sr.cmd_check([kb]) == 0
    # ...and write no longer aborts demanding an impossible local full text.
    assert sr.cmd_write([kb]) == 0
    assert not (repo / "verification").exists()


def test_hard_wrapped_cache_text_still_resolves(repo):
    """Matching collapses whitespace, like the reference validator."""
    # The cache hard-wraps this sentence across lines; the snippet is one line.
    kb = kb_file(
        repo, "the effect was concentration dependent across all donors tested"
    )
    assert sr.abstract_only_snippets(kb) == {}


def test_elided_snippet_resolves_in_order(repo):
    kb = kb_file(
        repo,
        "fine particulate matter ... decreased ciliary beat frequency "
        "... across all donors tested",
    )
    assert sr.abstract_only_snippets(kb) == {}


def test_out_of_order_elision_still_demands_receipt(repo):
    kb = kb_file(repo, "across all donors tested ... fine particulate matter")
    assert sr.abstract_only_snippets(kb) == {PMID: {
        "across all donors tested ... fine particulate matter"
    }}


def test_unresolvable_snippet_still_demands_receipt(repo, capsys):
    kb = kb_file(repo, IN_ABSTRACT, NOT_IN_ABSTRACT)
    # Only the CI-invisible snippet is receipt-bound.
    assert sr.abstract_only_snippets(kb) == {PMID: {NOT_IN_ABSTRACT}}
    assert sr.cmd_check([kb]) == 1
    assert "no verification receipt" in capsys.readouterr().out


def test_write_still_refuses_without_local_full_text(repo, capsys):
    kb = kb_file(repo, NOT_IN_ABSTRACT)
    assert sr.cmd_write([kb]) == 1
    assert "references_cache_local" in capsys.readouterr().err


def test_receipt_covers_unresolvable_snippet_and_binds_its_text(repo, capsys):
    kb = kb_file(repo, NOT_IN_ABSTRACT)
    # With the full text present locally, write produces the receipt...
    local = repo / "references_cache_local"
    local.mkdir()
    (local / "PMID_99990001.md").write_text(
        ABSTRACT + f"\n## Full text\n\n{NOT_IN_ABSTRACT}\n"
    )
    assert sr.cmd_write([kb]) == 0
    receipt = repo / "verification" / "PMID_99990001.json"
    assert json.loads(receipt.read_text())["snippet_sha256"] == [
        sr.snippet_hash(NOT_IN_ABSTRACT)
    ]
    # ...check passes against it...
    assert sr.cmd_check([kb]) == 0
    # ...and editing the quote afterwards fails check (tamper protection).
    kb_file(repo, NOT_IN_ABSTRACT.replace("24 h", "48 h"))
    capsys.readouterr()
    assert sr.cmd_check([kb]) == 1
    assert "not covered by the receipt" in capsys.readouterr().out


def test_full_text_cache_entries_are_never_receipt_bound(repo):
    (repo / "references_cache" / "PMID_99990001.md").write_text(
        ABSTRACT.replace("content_type: abstract_only", "content_type: full_text_pmc")
    )
    kb = kb_file(repo, NOT_IN_ABSTRACT)
    # Not this gate's job: the reference validator checks full-text entries.
    assert sr.abstract_only_snippets(kb) == {}
