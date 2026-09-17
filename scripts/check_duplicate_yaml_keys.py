#!/usr/bin/env python3
"""Fail if any YAML file repeats a key inside the same mapping.

Why this matters: PyYAML (what most tools here use) silently keeps the LAST
value when a key is repeated, so a duplicate is invisible to tests — but the
stricter parser inside linkml-reference-validator refuses the file entirely.
Duplicates usually arrive by merge, not by typing: two PRs each add the same
section to the same file at different spots, both merge cleanly, and the
result is broken. That's why this check sweeps every file, not just changed
ones. (Pattern borrowed from dismech.)

Usage:
    python scripts/check_duplicate_yaml_keys.py              # sweep default dirs
    python scripts/check_duplicate_yaml_keys.py kb/publications/foo.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Directories swept by default: curated content, the queue, schema, config.
DEFAULT_DIRS = ["kb", "stubs", "src/soma/schema", "conf"]


class DuplicateKeyError(Exception):
    pass


class DuplicateDetectingLoader(yaml.SafeLoader):
    """A loader that raises instead of silently keeping the last value."""


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if isinstance(key, (str, int, float, bool)) and key in seen:
            raise DuplicateKeyError(
                f"duplicate key {key!r} at line {key_node.start_mark.line + 1}"
            )
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep)


DuplicateDetectingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def check_file(path: Path) -> str | None:
    """Return an error message, or None if the file is clean."""
    try:
        with path.open() as f:
            list(yaml.load_all(f, Loader=DuplicateDetectingLoader))
    except DuplicateKeyError as e:
        return f"{path}: {e}"
    except yaml.YAMLError as e:
        return f"{path}: unparseable YAML: {e}"
    return None


def main(argv: list[str]) -> int:
    if argv:
        files = [Path(a) for a in argv]
    else:
        files = []
        for d in DEFAULT_DIRS:
            base = ROOT / d
            if base.is_dir():
                files.extend(sorted(base.rglob("*.yaml")))
                files.extend(sorted(base.rglob("*.yml")))

    errors = [msg for f in files if (msg := check_file(f))]
    for msg in errors:
        print(f"ERROR: {msg}", file=sys.stderr)

    print(f"Checked {len(files)} YAML files: {len(errors)} problem(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
