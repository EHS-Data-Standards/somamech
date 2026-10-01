---
name: oaklib
description: Ontology Access Kit - lookup, validate, and search ontology terms using the runoak CLI
user_invocable: true
---

# /oaklib - Ontology Access Kit

Use this skill when the user asks to look up, validate, or search ontology terms relevant to the SOMA schema.

## Supported Ontologies

| Prefix | Ontology | Example |
|--------|----------|---------|
| CHEBI | Chemical Entities of Biological Interest | CHEBI:28939 (N-acetyl-L-cysteine) |
| ENVO | Environment Ontology | ENVO:01000415 (fine respirable suspended particulate matter) |
| CL | Cell Ontology | CL:2000094 (nasal cavity respiratory epithelium epithelial cell of viscerocranial mucosa) |
| UBERON | Uber-anatomy Ontology | UBERON:0001707 (nasal cavity) |
| NCBITaxon | NCBI Taxonomy | NCBITaxon:9606 (Homo sapiens) |
| UO | Units of Measurement | UO:0000032 (hour) |
| OBI | Ontology for Biomedical Investigations | OBI:0000070 (assay) |
| GO | Gene Ontology | GO:0005216 (ion channel activity) |
| ECTO | Environmental Conditions, Treatments, and Exposures | ECTO:0001018 |
| PR | Protein Ontology | PR:000003411 (CFTR) |
| HP | Human Phenotype Ontology | HP:0002110 (bronchiectasis) |
| PATO | Phenotypic Quality Ontology | PATO:0000001 (quality) |
| CLO | Cell Line Ontology | CLO:0002192 (Calu-3) |

## Commands

All commands use the pattern: `uv run runoak -i sqlite:obo:<ONT> <command> <args>`

The `<ONT>` must be the **lowercase** ontology name (e.g., `chebi`, `envo`, `cl`, `uberon`, `ncbitaxon`, `uo`).

### Look up a term by CURIE

```bash
uv run runoak -i sqlite:obo:chebi info CHEBI:28939
```

### Search for a term by label

```bash
uv run runoak -i sqlite:obo:cl search "nasal epithelial cell"
```

### Get ancestors of a term

```bash
uv run runoak -i sqlite:obo:cl ancestors CL:2000094
```

### Get relationships for a term

```bash
uv run runoak -i sqlite:obo:uberon relationships UBERON:0001707
```

### Get cross-ontology mappings

```bash
uv run runoak -i sqlite:obo:chebi mappings CHEBI:28939
```

### Validate that a CURIE exists and get its label

```bash
uv run runoak -i sqlite:obo:ncbitaxon info NCBITaxon:9606
```

## Notes

- The first run for each ontology will download the SQLite database (can take a minute).
- For the Protein Ontology (PR), use `sqlite:obo:pr`.
- For NCBITaxon, use `sqlite:obo:ncbitaxon` (all lowercase, no underscore).
- For Cell Line Ontology, use `sqlite:obo:clo`.
- If a search returns too many results, add `| head -20` to limit output.
- CURIEs in SOMA YAML files should use the standard prefix format (e.g., `CHEBI:28939`, not `chebi:28939`).
- **Never trust a label you did not resolve.** `runoak info` is the only way to confirm a CURIE means what a
  neighbouring `name:` claims. PM2.5 sat in this repo as `CHEBI:74481` for months; that ID is actually
  *N(2)-methylguanosine 5'-monophosphate(1-) residue*. Not every exposure agent is a CHEBI term — PM2.5 and
  other environmental materials live in ENVO.

## Common SOMA CURIEs for Validation

```bash
# Verify PM2.5 (an ENVO material, not a CHEBI chemical)
uv run runoak -i sqlite:obo:envo info ENVO:01000415

# Verify nasal epithelial cell
uv run runoak -i sqlite:obo:cl info CL:2000094

# Verify Homo sapiens
uv run runoak -i sqlite:obo:ncbitaxon info NCBITaxon:9606

# Verify hour unit
uv run runoak -i sqlite:obo:uo info UO:0000032
```
