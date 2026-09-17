---
name: pdf-to-yaml
description: Extract structured data from a publication PDF into a SOMA-compliant Container YAML file
user_invocable: true
---

# /pdf-to-yaml - Publication to SOMA YAML

Use this skill to extract structured assay/measurement data from a publication PDF and produce a SOMA-compliant 
Container YAML file.

## Pipeline Overview

```
PDF --[Read tool]--> Extract data --> Map to SOMA schema --> Assign ontology terms --> Generate YAML --> Validate
```

## Phase 1: Read the PDF

Use the Read tool to read the PDF in 20-page chunks. Extract:
- Study design (in vitro / in vivo models)
- Assay types performed
- Measurements and quantitative results
- Protocols and methods
- Exposure conditions (agent, concentration, duration)
- Statistical results (p-values, sample sizes, fold changes)
- Species, cell types, anatomical sites

## Phase 2: Map to SOMA Schema

Reference these schema files to structure the data:
- **Main schema**: `src/soma/schema/soma.yaml` - Container class with collection slots
- **Assay base**: `src/soma/schema/assay_base.yaml` - Assay, StudySubject, Protocol
- **Microschemas**: `src/soma/schema/assay_microschemas.yaml` - Domain-specific assay + output classes

### Available Assay Types

| Assay Class | Output Class | Use For |
|-------------|-------------|---------|
| CiliaryFunctionAssay | CiliaryFunctionOutput | CBF, active area, cilia length |
| ASLAssay | ASLOutput | Airway surface liquid height/volume |
| MucociliaryClearanceAssay | MCCOutput | Mucociliary transport rate |
| OxidativeStressAssay | OxidativeStressOutput | ROS, GSH, 8-OHdG |
| CFTRFunctionAssay | CFTRFunctionOutput | Isc, chloride secretion |
| EGFRSignalingAssay | EGFRSignalingOutput | EGFR phosphorylation, activation |
| GobletCellAssay | GobletCellOutput | Goblet cell %, MUC5AC/MUC5B |
| BALFSputumAssay | BALFSputumOutput | BALF cytokines, cell counts |
| LungFunctionAssay | LungFunctionOutput | FEV1, sRaw, resistance |
| FoxJExpressionAssay | FoxJExpressionOutput | FOXJ1 mRNA/protein |
| GeneExpressionAssay | GeneExpressionOutput | Generic gene/protein expression |

## Phase 3: Assign Ontology Terms

Use `/oaklib` to find and verify CURIEs for:
- **Chemicals/agents**: CHEBI (e.g., CHEBI:74481 for PM2.5)
- **Cell types**: CL (e.g., CL:0002603 for nasal epithelial cell)
- **Species**: NCBITaxon (e.g., NCBITaxon:9606 for Homo sapiens)
- **Units**: UO (e.g., UO:0000032 for hour)
- **Anatomy**: UBERON (e.g., UBERON:0001707 for nasal cavity)
- **Proteins/genes**: PR, NCBIGene (e.g., PR:000003411 for CFTR protein, NCBIGene:1080 for CFTR genes)
- **Cell lines**: CLO (e.g., CLO:0003679 for Calu-3)

## Phase 4: Generate YAML

### File Naming Convention

```
Container-<firstauthor><year>-<agent>-<focus>.yaml
```

Examples:
- `Container-liu2024-pm25-cftr.yaml`
- `Container-montgomery2020-pm25-mucociliary.yaml`

### Output Location

Write to `kb/publications/` when extracting a corpus paper (the normal case,
via /claim-paper or /fetch-and-curate). Write to the current working
directory only for ad-hoc extractions outside the corpus workflow.

### Source Publication and Evidence (REQUIRED for kb/ files)

Every kb/ file starts by naming its source paper:

```yaml
source_publication:
  reference: "PMID:12345678"
  reference_title: "<title copied from references_cache/PMID_12345678.md>"
  doi: "10.1234/example"
```

Every assay whose numbers come from the paper carries an `evidence:` block —
an exact quote from the paper supporting what the assay records:

```yaml
    evidence:
      - reference: "PMID:12345678"
        reference_title: "<title copied from the cache file>"
        supports: SUPPORT
        evidence_source: IN_VITRO   # or HUMAN_CLINICAL / MODEL_ORGANISM / COMPUTATIONAL
        snippet: "Exact sentence copied from the paper."
        explanation: "One sentence on how this quote supports the assay's values."
```

Rules that make verification work:
- The `snippet` must be copied word-for-word — it is checked automatically
  against the cached copy of the paper (`just verify-snippets <file>`), and a
  paraphrase fails.
- Copy `reference_title` from the cache file's frontmatter
  (`head -5 references_cache/PMID_<n>.md`), never from memory — inventing a
  title next to a verified quote is a documented failure mode.
- If a quote will not verify, re-read the source and fix the quote or drop
  the claim. Never loosen the quote to make the checker happy.

### YAML Structure

Follow the structure of the existing schema in YAML format.  Examples:
- `tests/data/valid/Container-liu2024-pm25-cftr.yaml`
- `tests/data/valid/Container-montgomery2020-pm25-mucociliary.yaml`

Key structural patterns:
- `protocols:` section with all protocols listed
- Each assay type as a top-level collection (e.g., `cftr_assays:`, `gene_expression_assays:`)
- Each assay has inline `has_specified_output:` with the measurement data
- Each assay has inline `study_subject:` with cell type / species info
- Each assay has inline `has_exposure_condition:` with agent/concentration/duration
- Each assay has inline `informs_on_key_event:` linking to the AOP
- Each assay has `follows_protocols:` referencing the protocols section

### ID Conventions

- Protocols: `PROTOCOL:<author>-<method>-<number>` (e.g., `PROTOCOL:liu-ussing-001`)
- Exposures: `EXPOSURE:<author>-<agent>-<detail>` (e.g., `EXPOSURE:liu-pm25-100ug-24h`)
- Key Events: `KE:<type>-<description>` (e.g., `KE:ke-decreased-cftr`)
- Assays: `<PREFIX>:<author>-<target>-<condition>` (e.g., `CFTR:liu-pm25-24h`)
- Outputs: `<assay-id>-output` (e.g., `CFTR:liu-pm25-24h-output`)
- Subjects: `soma:<author>-<type>-<number>` or `SUBJECT:<author>-<type>` for in vivo

## Critical Constraints

1. **ALL numeric values MUST come from the paper** - never hallucinate measurements
2. **Figure-derived values**: do not derive any specific measurements - never hallucinate measurements
3. **Missing data**: omit the slot entirely, do not guess values
4. **Include p-values and sample sizes** in description fields when available, but structure the data using more specific slots when available.
5. **Quote all numeric values** as strings in YAML (e.g., `value: "0.55"`)
6. **For every ontology id you suggest, validate that the string-value from the paper matches the label of the ontology term, or one of its synonyms using linkml-term-validator"

## Phase 5: Validate

After generating the YAML, run the full check stack (schema + ontology terms
+ evidence quotes):

```bash
just validate-file kb/publications/<new-file>.yaml
just verify-snippets kb/publications/<new-file>.yaml
```

For a file kept under tests/data/valid/ instead, also run:

```bash
uv run python -m pytest tests/test_data.py -v -k "<new-file-stem>"
```
