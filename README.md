> [!IMPORTANT]
> ## ⚠️ AI-Generated Content Notice
>
> **The vast majority of the content in this repository is AI-generated.** Schema files, knowledge-base entries, documentation, and code have been produced by AI agents (e.g., Claude) working under human direction.
>
> **A person's name on a commit, pull request, issue, or knowledge-base entry does *not* mean that person authored the content themselves.** It means that person guided an AI agent, which made the change on their behalf. Human contributors direct, review, and approve the work, but the content itself is written by AI.

<p align="center">
  <img src="src/docs/soma-logo.svg" alt="SOMA Logo" width="700">
</p>

<p align="center">
  A <a href="https://linkml.io/">LinkML</a> schema for representing Key Event and Outcome measurements, assays, and experimental protocols in the context of environmental health sciences (EHS) outcomes research.
</p>

<p align="center">
  <a href="https://EHS-Data-Standards.github.io/soma"><strong>Documentation</strong></a> &middot;
  <a href="https://EHS-Data-Standards.github.io/soma/elements/"><strong>Schema</strong></a> &middot;
  <a href="https://EHS-Data-Standards.github.io/soma/examples.html"><strong>Examples</strong></a> &middot;
  <a href="https://EHS-Data-Standards.github.io/soma/artifacts.html"><strong>Artifacts</strong></a>
</p>

---

## Purpose

This data model provides a standardized way to capture and exchange data about airway biology
assays relevant to respiratory health outcomes, including:

- **Ciliary function** - Beat frequency, active area, morphology
- **Airway surface liquid** - ASL height, periciliary layer depth, ion composition
- **Mucociliary clearance** - Transport rates, directionality, clearance efficiency
- **Oxidative stress** - ROS, lipid peroxidation, antioxidant capacity
- **Ion channel function** - CFTR chloride secretion, sweat chloride
- **Signaling pathways** - EGFR phosphorylation, downstream kinases
- **Mucin biology** - Goblet cells, MUC5AC/MUC5B expression
- **Inflammatory markers** - BALF/sputum cell counts, cytokines
- **Lung function** - Spirometry outcomes (FEV1, FVC)
- **Gene expression** - Target gene mRNA levels

## Key Features

- **Assay-centric architecture** with domain-specific assay classes using named measurement slots
- **StudySubject hierarchy** for describing biological systems: cell cultures, human/animal subjects, populations
- **Typed protocol hierarchy**: ImagingProtocol, MolecularAssayProtocol, StainingProtocol, SpirometryProtocol
- **AOP Framework integration**: KeyEvent and AdverseOutcomePathway classes with assay linkage
- **Ontology-backed** entities mapped to GO, ChEBI, CL, UO, OBI, and other biomedical ontologies

## Getting Started

The schema can be used to:

1. **Validate data** - Ensure your data conforms to the model
2. **Generate code** - Create Python dataclasses, Pydantic models, JSON Schema
3. **Transform data** - Convert between JSON, YAML, RDF, and other formats

## Development Workflow

For local development, use `uv` and `just` as the canonical entry points.
The repository may contain underlying Python, npm, and LinkML commands, but contributors
should treat the `just` recipes as the supported interface for routine setup, testing,
and generation tasks.

### Prerequisites

- `uv` for Python environment and dependency management
- `just` for repository task automation
- `node` and `npm` for DataHarmonizer frontend builds

### Setup

Install the Python dependencies managed by the repo:

```bash
just install
```

### Common Commands

- Run the full validation workflow: `just test`
- Regenerate project artifacts: `just gen-project`
- Regenerate schema documentation: `just gen-doc`
- Build the DataHarmonizer assets: `just build-dh`
- List all available recipes: `just --list`

If you need to run a Python tool directly, prefer `uv run ...` so it executes inside the
managed project environment.

### Querying the knowledge base

The `kb/publications/*.yaml` files are the source of truth. Two generated products
make them queryable; both are gitignored and rebuilt on demand, never hand-edited.

- `just build-db` — build `exports/soma.duckdb`, a local [DuckDB](https://duckdb.org)
  database with one table per schema class.
- `just dump-tsv` — dump every table and view to `exports/tsv/*.tsv`.
- `just build-db-all` — both of the above.
- `just query 'SELECT ...'` — run one query; with no argument, list the relations.
- `just generate-workbook` — the pooled Excel workbook (see `scripts/build_workbook.py`).

Start with the **`measurement_full`** view: one row per number in the KB, already
joined to its paper, assay, exposure condition, experimental group and key event.

```sh
just query "SELECT paper_id, measurement, value, unit_label, exposure_agent_label \
            FROM measurement_full WHERE measurement LIKE '%beat%'"
```

Alongside the per-class tables, three tables carry what the class-per-table layout
cannot: `measurement` (long format, with dispersion and sample size), `link` (every
entity-to-entity edge, authoritative for many-to-many slots such as
`follows_protocols`) and `term` (every ontology term referenced, with its label).
The views `assay` and `assay_output` union the 11 assay and 11 output subclasses so
a cross-assay question does not need an 11-way `UNION`.

The DuckDB schema is derived from the installed `soma-schema` at build time, so a
version bump regenerates it — inspect it with `just db-schema`. It deliberately
differs from LinkML's own relational model (`just db-schema-linkml`) in three ways,
documented in [scripts/soma_duckdb.py](scripts/soma_duckdb.py): value objects such
as `QuantityValue` are flattened into named columns rather than joined through a
shared table, reused children carry one `parent_type`/`parent_id` pair instead of one
nullable foreign key per possible parent, and multivalued scalars stay on the parent
row as DuckDB `LIST` columns instead of side tables.

## Repository Structure

* [docs/](docs/) - mkdocs-managed documentation
* [examples/](examples/) - Examples of using the schema
* [project/](project/) - project files (auto-generated, do not edit)
* Schema and datamodel: the [soma-schema](https://pypi.org/project/soma-schema/) package, maintained in [EHS-Data-Standards/soma](https://github.com/EHS-Data-Standards/soma)
* [tests/](tests/) - Python tests

## Developer Tools

There are several pre-defined command-recipes available.
They are written for the command runner [just](https://github.com/casey/just/). To list all pre-defined commands, run `just` or `just --list`.

## Credits

This project uses the template [linkml-project-copier](https://github.com/dalito/linkml-project-copier) published as [doi:10.5281/zenodo.15163584](https://doi.org/10.5281/zenodo.15163584).
