"""Prove the evidence quote checker actually checks.

Both tests run offline: the cited paper (PMID:39113893) is committed in
references_cache/, and --no-full-text stops the validator from fetching.

The doctored fixture in tests/data/quote_mismatch/ is a copy of the Liu 2024
file whose evidence snippet was altered ("significantly decreased" ->
"was completely abolished"). If that file ever PASSES, the quote check has
silently stopped working — which is the failure mode this test exists for.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
WRAPPER = ROOT / "scripts" / "run_reference_validator.sh"
SCHEMA = ROOT / "src" / "soma" / "schema" / "soma.yaml"
CONFIG = ROOT / "conf" / "reference_validator_config.yaml"
CACHE = ROOT / "references_cache"

GENUINE = ROOT / "tests" / "data" / "valid" / "Container-liu2024-pm25-cftr.yaml"
DOCTORED = ROOT / "tests" / "data" / "quote_mismatch" / "Container-doctored-snippet.yaml"


def run_reference_validation(data_file: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            str(WRAPPER), "validate", "data", str(data_file),
            "--schema", str(SCHEMA),
            "--target-class", "Container",
            "--config", str(CONFIG),
            "--cache-dir", str(CACHE),
            "--no-full-text",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


def test_genuine_quote_passes():
    result = run_reference_validation(GENUINE)
    assert result.returncode == 0, result.stdout + result.stderr


def test_doctored_quote_fails():
    result = run_reference_validation(DOCTORED)
    assert result.returncode != 0, (
        "A doctored quote passed reference validation - the quote checker "
        "is not checking!\n" + result.stdout + result.stderr
    )
    assert "not found as substring" in result.stdout
