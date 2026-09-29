import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "snippet_receipts.py"

spec = importlib.util.spec_from_file_location("snippet_receipts", SCRIPT)
snippet_receipts = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(snippet_receipts)


def test_check_skips_resolvable_abstract_only_snippets():
    kb_file = ROOT / "kb" / "publications" / "Container-nguyen2021-airpollutants-cftr.yaml"
    assert snippet_receipts.abstract_only_snippets(kb_file) == {}
    assert snippet_receipts.cmd_check([kb_file]) == 0


def test_check_requires_receipt_for_abstract_only_snippet_not_in_cache(capsys, tmp_path):
    snippet = "this phrase does not occur in the committed abstract cache entry"
    kb_file = tmp_path / "Container-test.yaml"
    kb_file.write_text(
        yaml.safe_dump(
            {
                "container_id": "test",
                "evidence": [{"reference": "PMID:34601066", "snippet": snippet}],
            }
        )
    )

    assert snippet_receipts.abstract_only_snippets(kb_file) == {"PMID:34601066": {snippet}}
    assert snippet_receipts.cmd_check([kb_file]) == 1
    out = capsys.readouterr().out
    assert "has no verification receipt" in out
