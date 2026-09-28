---
name: linkml-validate
description: Validate SOMA YAML files against the LinkML schema
user_invocable: true
---

# /linkml-validate - Schema Validation

Use this skill to validate SOMA YAML data files against the LinkML schema. Run this after generating or editing YAML files.

## Locating the Schema

The schema ships inside the installed `soma-schema` package (import name `soma`). Resolve it once per shell session:

```bash
SOMA_SCHEMA=$(uv run python -c 'from importlib.resources import files; print(files("soma")/"schema"/"soma.yaml")')
```

The `just` recipes (`just validate-file <file>`, `just validate-all`) resolve it for you.

## Validation Methods

### 1. CLI Validation (quick check)

```bash
uv run linkml-validate -s "$SOMA_SCHEMA" <file>
```

Example:
```bash
uv run linkml-validate -s "$SOMA_SCHEMA" tests/data/valid/Container-liu2024-pm25-cftr.yaml
```

### 2. Python Loader Validation (deeper check)

This mirrors what `tests/test_data.py` does:

```python
from linkml_runtime.loaders import yaml_loader
import soma.datamodel.soma

obj = yaml_loader.load(
    "tests/data/valid/Container-liu2024-pm25-cftr.yaml",
    target_class=soma.datamodel.soma.Container
)
assert obj
```

### 3. Full Test Suite

```bash
uv run python -m pytest tests/test_data.py -v
```

This runs all valid YAML files through the Container loader automatically (they are discovered via glob from `tests/data/valid/*.yaml`).

## Schema Files

All inside the installed package, next to `soma.yaml` (`$(dirname "$SOMA_SCHEMA")`):

| File | Purpose |
|------|---------|
| `soma.yaml` | Main schema entry point - Container class, collection slots |
| `aop_framework.yaml` | KeyEvent, AdverseOutcomePathway classes |
| `assay_base.yaml` | Assay, StudySubject, Protocol base classes |
| `assay_microschemas.yaml` | 11 domain-specific assay + output classes |
| `evidence.yaml` | EvidenceItem (exact-quote evidence), source_publication |
| `publication_stub.yaml` | PublicationStub for the paper queue |

The schema is maintained in [EHS-Data-Standards/soma](https://github.com/EHS-Data-Standards/soma); to change it, open a PR there and bump the `soma-schema` pin in `pyproject.toml` here.

## Validation Workflow

1. Run `linkml-validate` CLI for a quick syntax/structure check
2. If that passes, run `pytest tests/test_data.py -v` to confirm Python loader compatibility
3. Fix any errors reported before proceeding to Excel generation

## Common Errors

- **Missing required field**: Check that `id` is present on all entities
- **`has_specified_output` not a list**: it is multivalued - wrap the output
  record(s) in a YAML list (`- id: ...`), one record per experimental condition
- **Invalid enum value**: Check allowed values in the schema (e.g., `biological_action`, `subject_type`, `experimental_group`, `variability_type`, `change_type`)
- **Type mismatch**: Ensure numeric values are quoted strings in YAML (e.g., `value: "0.55"` not `value: 0.55`)
- **Unknown slot**: Verify slot name matches the schema exactly (check `assay_microschemas.yaml`)

## Validating All Test Data

```bash
# Validate all valid examples (should all pass)
for f in tests/data/valid/Container-*.yaml; do
  echo "=== $f ==="
  uv run linkml-validate -s "$SOMA_SCHEMA" "$f"
done
```
