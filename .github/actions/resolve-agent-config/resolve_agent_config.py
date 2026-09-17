#!/usr/bin/env python3
"""Resolve which Claude model a workflow should use.

Reads .github/agent-config.yaml. Resolution order:
  1. an explicit override (a workflow_dispatch input, passed as --override)
  2. the workflow's own `model:` entry
  3. `default_model`

Deliberately depends only on PyYAML: this runs as a composite action in a
bare environment where the project is not installed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


class ConfigError(Exception):
    pass


def resolve_model(config: dict, workflow: str, override: str | None = None) -> str:
    if override and override.strip():
        return override.strip()
    entry = (config.get("workflows") or {}).get(workflow) or {}
    if not isinstance(entry, dict):
        raise ConfigError(f"workflow '{workflow}' entry must be a mapping")
    model = entry.get("model")
    if model:
        return str(model)
    default = config.get("default_model")
    if not default:
        raise ConfigError(
            f"no model for workflow '{workflow}' and no default_model set"
        )
    return str(default)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workflow", required=True)
    ap.add_argument("--override", default="")
    args = ap.parse_args()
    config = yaml.safe_load(Path(args.config).read_text()) or {}
    try:
        print(resolve_model(config, args.workflow, args.override))
    except ConfigError as e:
        print(f"resolve-agent-config: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
