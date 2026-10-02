# How to Use the SOMA Extraction Workbook

A guide for scientists and data scientists who want to pull study variables out of the
pooled workbook — for example, to parameterize a synthetic population and ask what happens
to it when an exposure variable changes (a wildfire, a new pollution standard, a longer
exposure window).

**Downloads** (rebuilt from the knowledge base on every site deploy):

- [Pooled extraction workbook (`soma_extractions.xlsx`)](artifacts/soma_extractions.xlsx)
- [DuckDB database (`soma.duckdb`)](artifacts/soma.duckdb) — the schema-complete
  relational build, including the `evidence` table of supporting quotes

## What this workbook is

One Excel file, `exports/soma_extractions.xlsx`, pooling the extracted studies on how air
pollution damages the airway (PM2.5, ozone, smoke, and similar exposures). Each study was
read and converted into structured records: who was exposed, to what, how the effect was
measured, and what the numbers were. Every row has a `source_publication` column with the
paper's PubMed ID, so any value can be traced back to its study.

The workbook is generated, not hand-maintained. Rebuild it any time with
`just generate-workbook`; the source of truth is the per-paper YAML files in
`kb/publications/`.

## The tabs, in the order to read them

| Tab | Question it answers |
| --- | --- |
| Papers | Which papers are in here (PMID, title, DOI, source file, assay count)? |
| ExposureCondition | What was applied: agent (e.g. PM2.5), concentration, duration, timing |
| CellularSystem / InVivoSubject / PopulationSubject | Who or what was exposed: cell cultures, lab animals, or human cohorts (with cohort size, age range, inclusion criteria) |
| KeyEvent | The biological events the field tracks, e.g. "oxidative stress", "mucus hypersecretion" |
| KeyEventRelationship | Which event causes which — the causal chain from exposure to disease |
| Assay tabs (CFTRFunctionAssay, GeneExpressionAssay, LungFunctionAssay, ...) | How each effect was measured, and which exposure, subject, and key event it connects |
| Output tabs (one per assay type) | The result records, one row per experimental group |
| **Responses** | Every measured number in one long table — the main tab for modeling |
| ResponseComparison | Exposed-vs-control changes: direction, size, p-value |

A practical path: skim Papers, then work almost entirely out of Responses,
ExposureCondition, the three subject tabs, and KeyEventRelationship.

## Pulling variables for a synthetic population

Think of each simulated individual as a row you assemble from three kinds of variables:

1. **Subject attributes** — from `PopulationSubject` (human cohorts: cohort size, age
   range, inclusion criteria, clinical context), `InVivoSubject` (species, sex, age,
   disease state), and `CellularSystem` (cell type, donor source, culture model). These
   define who is in your population. Human cohort rows are the most direct template;
   mouse and cell-culture rows tell you mechanism, not population structure.
2. **Exposure variables** — from `ExposureCondition`: agent, concentration (with units),
   duration, and timing post exposure. These are the knobs you will turn in a scenario.
3. **Response variables** — from `Responses`: the measured endpoints (FEV1, FVC, ciliary
   beat frequency, MUC5AC expression, IL-6/IL-8 levels, chloride secretion, and so on),
   each with value, unit, variability, and sample size.

The variability and `sample_size` columns matter as much as the means: they are what let
you draw a distribution for each endpoint instead of assigning everyone the same value.
Where a human study reports mean ± SD for FEV1 under a given exposure, you can sample
individuals from that distribution directly.

## The Responses tab: your dose–response table

`Responses` is the one tab built for analysis. One row = one measurement under one
experimental condition. Columns:

| Column | Meaning |
| --- | --- |
| source_publication | PMID of the paper the number came from |
| assay_id / assay_type | Which experiment produced it |
| output_id / experimental_group | Which group within the experiment (e.g. "control", "100 µg/mL PM2.5, 24 h") |
| exposure_condition | ID of the exposure condition — join this to the ExposureCondition tab to get agent, dose, duration |
| measurement | Name of the endpoint (fev1, beat_frequency_hz, il6_concentration, ...) |
| value / unit | The number and its unit |
| central_tendency / variability / sample_size | Mean vs. median, SD/SEM/CI, and n |

To build a dose–response curve for one endpoint: filter `measurement` to the endpoint,
join `exposure_condition` to ExposureCondition for the dose axis, and plot value against
concentration. Keep `source_publication` in the frame so you can check whether a trend
comes from many studies or one.

Loading it in Python:

```python
import pandas as pd

resp = pd.read_excel("exports/soma_extractions.xlsx", sheet_name="Responses")
expo = pd.read_excel("exports/soma_extractions.xlsx", sheet_name="ExposureCondition")
# both sheets carry id/name columns, so suffix the exposure copies
df = resp.merge(expo, left_on="exposure_condition", right_on="id",
                suffixes=("", "_exposure"))
```

## Modeling a scenario change (example: a wildfire)

A scenario change is just a shift in exposure variables, so it maps onto the workbook in
three steps:

1. **Translate the scenario into exposure terms.** A wildfire means a sharp rise in PM2.5
   concentration over days, plus wood-smoke-specific components. In the ExposureCondition
   tab, find rows whose agent and concentration range bracket your scenario (e.g. PM2.5 at
   100–500 µg/m³, 24–72 h).
2. **Read off the responses at those exposures.** Filter Responses to rows whose
   `exposure_condition` matches, and compare against the same endpoints under control
   conditions (ResponseComparison already has the exposed-vs-control deltas and p-values).
3. **Propagate through the causal chain.** KeyEventRelationship tells you the order of
   events — for example: oxidative stress → EGFR activation → mucin hypersecretion →
   reduced mucociliary clearance → reduced lung function. If your scenario raises the
   upstream variable, these rows tell you which downstream endpoints should move in your
   synthetic population, and in which direction.

Two honesty rules when extrapolating: check the subject tab before treating a number as
human (a mouse or cell-culture value calibrates mechanism, not population outcomes), and
check `sample_size` and variability before letting a single small study drive a simulated
effect.

## What is NOT in the workbook

The workbook's columns are generated from the SOMA schema, so every field recorded in the
knowledge base appears on its tab — with one deliberate exception: **evidence quotes**.
Every extracted claim in the knowledge base carries the exact sentence from the paper
that supports it, plus an explanation of how it supports the claim. Those quote records
are omitted from the spreadsheet view to keep it readable.

When you need the evidence behind a surprising number, go to:

- the per-paper YAML files in `kb/publications/` (everything, human-readable), or
- the [DuckDB database](artifacts/soma.duckdb) (rebuild locally with `just build-db`),
  which is schema-complete: every class has its own table, and the `evidence` table links
  each supporting quote to the record it backs (`parent_type`, `parent_id`).
